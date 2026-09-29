// Deliberately VULNERABLE sample for sec_scan.py - fake secrets, do not copy.
import java.io.ObjectInputStream;
import java.security.MessageDigest;
import java.util.Random;

@RestController
@CrossOrigin(origins = "*")                                                          // cors-wildcard
public class ShipmentController {
    private static final String DB_PASSWORD = "Cargo#2024!";                         // hardcoded-password

    @GetMapping("/shipments")
    public List<Shipment> find(@RequestParam String hawb) {
        String q = "SELECT id, hawb FROM shipment WHERE hawb = '" + hawb + "'";      // sql-injection
        return jdbcTemplate.query(q, mapper);
    }

    public Object read(InputStream in) throws Exception {
        return new ObjectInputStream(in).readObject();                              // insecure-deserialize
    }

    public byte[] hashPassword(String password) throws Exception {
        return MessageDigest.getInstance("SHA-1").digest(password.getBytes());      // weak-password-hash
    }

    public String otp() { return String.valueOf(new Random().nextInt(999999)); }    // otp: insecure-random

    public void log(Passenger p) {
        log.info("Passenger passport {}", p.getPassportNumber());                   // sensitive-logging
    }
}
