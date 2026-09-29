// Deliberately BAD sample for perf_smells.py - do not copy.
import java.util.*;
import java.util.regex.Pattern;

public class FlightLoadService {
    private final UldRepository uldRepository;
    private final RestTemplate restTemplate;

    public String report(List<Flight> flights, List<String> vipCarriers) {
        String out = "";
        for (Flight f : flights) {
            List<Uld> ulds = uldRepository.findByFlightId(f.getId());      // io-in-loop (N+1)
            Rate r = restTemplate.getForObject("/rates/" + f.getId(), Rate.class); // io-in-loop
            if (vipCarriers.contains(f.getCarrier())) { }                  // linear-lookup-loop
            Pattern p = Pattern.compile("[A-Z]{3}\\d{5}[A-Z]{2}");          // regex-in-loop
            out += f.getNumber() + ";";                                     // string-concat-loop
            System.out.println("flight " + f.getNumber());                  // log-in-loop
        }
        return out;
    }

    public List<Flight> delayed() {
        String q = "select * from flight where delayed = 1";                // select-star
        return flightRepository.findAll().stream().filter(Flight::isDelayed).toList(); // filter-in-memory
    }

    public void backoff() throws InterruptedException {
        Thread.sleep(2000);                                                 // sleep-in-code
    }
}
