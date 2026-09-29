# Java Reference (Java 21 LTS, Spring Boot 3.x)

Default: Java 21 + Spring Boot 3.x (Spring Framework 6, Jakarta EE 10, Hibernate 6). If the build shows Java 25 LTS or Spring Boot 4 (Framework 7), use those and say so. If it shows Boot 2.x / `javax.*`, stay on it and flag the migration (Boot 2.7 is out of OSS support).

## Project structure (package by feature)
```
src/main/java/com/example/cargo/
  CargoApplication.java
  booking/        BookingController, BookingService, BookingRepository, Booking (entity), DTO records
  flight/         ...same layout per feature
  common/         ApiExceptionHandler, config, security
src/main/resources/application.yml, db/migration/ (Flyway) or db/changelog/ (Liquibase)
src/test/java/com/example/cargo/booking/  unit, @WebMvcTest, @DataJpaTest, integration tests
```
Layers: controller (HTTP only) → service (transactions, rules) → repository (Spring Data). Keep entities out of controllers.

## Idioms & conventions
| Topic | Do | Avoid |
|---|---|---|
| DTOs | `record` with Bean Validation annotations | Returning JPA entities as JSON |
| DI | Constructor injection (single constructor, no `@Autowired` needed), `final` fields | Field injection |
| Validation | `@Valid @RequestBody`, `@Validated` on class for `@PathVariable`/`@RequestParam` constraints | Manual `if` chains in controllers |
| Transactions | `@Transactional` on service methods; `readOnly = true` for reads | `@Transactional` on private methods or self-invocation (proxy bypassed) |
| Concurrency | Virtual threads: `spring.threads.virtual.enabled=true` (Boot 3.2+, Java 21) for blocking I/O workloads | Pooling virtual threads; long `synchronized` blocks around I/O on Java 21 (pins carrier; fixed in Java 24+) |
| Language | `var`, records, sealed interfaces, pattern matching `switch`, text blocks | Lombok `@Data` on JPA entities (broken `equals/hashCode`) |
| HTTP clients | `RestClient` (Boot 3.2+) or `WebClient` if reactive | `RestTemplate` for new code (maintenance mode) |
| Migrations | Flyway or Liquibase | `ddl-auto=update` outside local dev |

## Error handling
- Return `ProblemDetail` (RFC 9457) from a `@RestControllerAdvice`; extend `ResponseEntityExceptionHandler` so validation errors (`MethodArgumentNotValidException`) also become problem details, or set `spring.mvc.problemdetails.enabled=true`.
- Domain exceptions (`BookingNotFoundException`) map to 404/409 in one place.
- Never return stack traces: `server.error.include-stacktrace=never`.

## Logging
- SLF4J with placeholders: `log.info("Booking created bookingId={} awb={}", id, awb);`, never string concatenation.
- Structured JSON: `logging.structured.format.console=ecs` (Boot 3.4+) or Logback + logstash encoder.
- Correlation: Micrometer Tracing puts `traceId`/`spanId` in MDC; for a custom `X-Correlation-ID`, a `OncePerRequestFilter` that sets and clears MDC.

## Config & secrets
- `application.yml` + profiles (`application-prod.yml`); bind with `@ConfigurationProperties` records + `@Validated`.
- Secrets from env vars (`SPRING_DATASOURCE_PASSWORD`), Spring Cloud Vault, AWS/Azure secret stores. Use `${DB_PASSWORD}` placeholders.

## Testing
- JUnit 5 + AssertJ + Mockito (`@ExtendWith(MockitoExtension.class)`) for services.
- Slices: `@WebMvcTest` (controller + advice), `@DataJpaTest` (repositories).
- Mocks in Spring context: `@MockitoBean` (Boot 3.4+); `@MockBean` is deprecated since 3.4.
- Real DB: Testcontainers + `@ServiceConnection` (Boot 3.1+), e.g. `PostgreSQLContainer`. Avoid H2 when prod is Postgres/Oracle/SQL Server.
- If Spring Security is on the classpath, `@WebMvcTest` applies it: use `@WithMockUser` or `spring-security-test` `jwt()`.
- Run: `./mvnw test` or `./gradlew test`.

## Performance pitfalls
- N+1 from lazy associations: `@EntityGraph`, `JOIN FETCH`, or DTO projections.
- `FetchType.EAGER` on collections; open-session-in-view (`spring.jpa.open-in-view=false`).
- Unbounded `findAll()`; use `Pageable`/`Slice` or keyset.
- Batch inserts: `hibernate.jdbc.batch_size` + avoid `IDENTITY` IDs when batching matters.
- Blocking calls on reactive (WebFlux) threads.

## Security pitfalls
- JPQL/native query string concatenation → use `:param` bindings.
- Mass assignment: bind to records, not entities.
- Spring Security 6: `SecurityFilterChain` bean (the `WebSecurityConfigurerAdapter` class is removed); keep CSRF on for cookie sessions, disable only for stateless token APIs.
- Actuator: expose only `health,info` publicly.
- Jackson default typing / polymorphic deserialization of untrusted input.

## Snippet: controller + service + problem details + test
```java
// src/main/java/com/example/cargo/booking/BookingController.java
package com.example.cargo.booking;

import jakarta.validation.Valid;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.util.UriComponentsBuilder;

@RestController
@RequestMapping("/api/v1/bookings")
class BookingController {
    private final BookingService service;

    BookingController(BookingService service) {
        this.service = service;
    }

    @GetMapping("/{id}")
    BookingResponse get(@PathVariable UUID id) {
        return service.get(id);
    }

    @PostMapping
    ResponseEntity<BookingResponse> create(@Valid @RequestBody CreateBookingRequest request,
                                           UriComponentsBuilder uri) {
        BookingResponse created = service.create(request);
        return ResponseEntity
                .created(uri.path("/api/v1/bookings/{id}").buildAndExpand(created.id()).toUri())
                .body(created);
    }
}
```
```java
// src/main/java/com/example/cargo/booking/BookingDtos.java
package com.example.cargo.booking;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.util.UUID;

record CreateBookingRequest(
        @NotBlank @Pattern(regexp = "\\d{3}-\\d{8}", message = "AWB must look like 176-12345675") String awbNumber,
        @Min(1) @Max(9999) int pieces,
        @NotNull @Positive BigDecimal weightKg) {}

record BookingResponse(UUID id, String awbNumber, int pieces, BigDecimal weightKg) {}

class BookingNotFoundException extends com.example.cargo.common.NotFoundException {
    BookingNotFoundException(UUID id) {
        super("Booking " + id + " not found");
    }
}
```
```java
// src/main/java/com/example/cargo/booking/BookingService.java
package com.example.cargo.booking;

import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class BookingService {
    private static final Logger log = LoggerFactory.getLogger(BookingService.class);
    private final BookingRepository repository;

    BookingService(BookingRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    BookingResponse get(UUID id) {
        return repository.findById(id)
                .map(BookingService::toResponse)
                .orElseThrow(() -> new BookingNotFoundException(id));
    }

    @Transactional
    BookingResponse create(CreateBookingRequest request) {
        Booking saved = repository.save(new Booking(request.awbNumber(), request.pieces(), request.weightKg()));
        log.info("Booking created bookingId={} awb={}", saved.getId(), saved.getAwbNumber());
        return toResponse(saved);
    }

    private static BookingResponse toResponse(Booking b) {
        return new BookingResponse(b.getId(), b.getAwbNumber(), b.getPieces(), b.getWeightKg());
    }
}
```
```java
// src/main/java/com/example/cargo/booking/Booking.java
package com.example.cargo.booking;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "bookings")
class Booking {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true, length = 12)
    private String awbNumber;

    private int pieces;

    @Column(precision = 10, scale = 2)
    private BigDecimal weightKg;

    protected Booking() {}

    Booking(String awbNumber, int pieces, BigDecimal weightKg) {
        this.awbNumber = awbNumber;
        this.pieces = pieces;
        this.weightKg = weightKg;
    }

    UUID getId() { return id; }
    String getAwbNumber() { return awbNumber; }
    int getPieces() { return pieces; }
    BigDecimal getWeightKg() { return weightKg; }
}
```
```java
// src/main/java/com/example/cargo/booking/BookingRepository.java
package com.example.cargo.booking;

import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

interface BookingRepository extends JpaRepository<Booking, UUID> {}
```
```java
// src/main/java/com/example/cargo/common/NotFoundException.java
package com.example.cargo.common;

public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) {
        super(message);
    }
}
```
```java
// src/main/java/com/example/cargo/common/ApiExceptionHandler.java
package com.example.cargo.common;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
class ApiExceptionHandler extends ResponseEntityExceptionHandler { // validation errors -> ProblemDetail too
    @ExceptionHandler(NotFoundException.class)
    ProblemDetail handleNotFound(NotFoundException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setTitle("Resource not found");
        return pd;
    }
}
```

```java
// src/test/java/com/example/cargo/booking/BookingControllerTest.java
package com.example.cargo.booking;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(BookingController.class)
class BookingControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean BookingService service;

    @Test
    void rejectsInvalidAwbWithProblemDetails() throws Exception {
        mvc.perform(post("/api/v1/bookings")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"awbNumber":"bad","pieces":1,"weightKg":10}
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON));
        verifyNoInteractions(service);
    }

    @Test
    void returns404WhenBookingMissing() throws Exception {
        UUID id = UUID.randomUUID();
        when(service.get(id)).thenThrow(new BookingNotFoundException(id));
        mvc.perform(get("/api/v1/bookings/{id}", id)).andExpect(status().isNotFound());
    }
}
```
