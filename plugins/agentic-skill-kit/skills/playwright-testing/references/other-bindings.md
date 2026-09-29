# Other Bindings: Python, .NET, Java

Same browser engine and concepts (locators, auto-waiting, web-first assertions, contexts, `storageState`, `route`, tracing). Differences are mostly in the **test runner**: only Node's `@playwright/test` includes fixtures, projects, parallel workers, retries, sharding, HTML report and `toHaveScreenshot` built in.

## Quick comparison
| Topic | TypeScript (`@playwright/test`) | Python (`pytest-playwright`) | .NET (`Microsoft.Playwright.NUnit` / `.MSTest` / `.Xunit`) | Java |
|---|---|---|---|---|
| Install | `npm init playwright@latest` | `pip install pytest-playwright` then `playwright install --with-deps` | `dotnet add package Microsoft.Playwright.NUnit`, build, then `pwsh bin/Debug/net8.0/playwright.ps1 install` | Maven `com.microsoft.playwright:playwright`; browsers download on first run (or `mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="install --with-deps"`) |
| Runner | Built in | pytest | NUnit / MSTest / xUnit | JUnit 5 (`@UsePlaywright`, 1.42+) or TestNG |
| Locator | `page.getByRole('button', { name: 'Search' })` | `page.get_by_role("button", name="Search")` | `Page.GetByRole(AriaRole.Button, new() { Name = "Search" })` | `page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Search"))` |
| Assertion | `await expect(loc).toHaveText('Departed')` | `expect(loc).to_have_text("Departed")` (`from playwright.sync_api import expect`) | `await Expect(loc).ToHaveTextAsync("Departed")` | `assertThat(loc).hasText("Departed")` (`PlaywrightAssertions`) |
| Async | `async/await` everywhere | Sync API by default (async API available) | `async Task` + `await` everywhere | Synchronous |
| Fixtures | `test.extend` | pytest fixtures (`page`, `context`, `browser`; override `browser_context_args`) | Base classes `PageTest` / `ContextTest`; override `ContextOptions()` | JUnit extensions / your own base class |
| Parallel | Workers, `fullyParallel` | `pytest-xdist` (`-n auto`) | NUnit `[Parallelizable]` + `LevelOfParallelism`; MSTest `[assembly: Parallelize]` | JUnit parallel config; one `Playwright` instance per thread (not thread-safe) |
| Retries | `retries` in config | `pytest-rerunfailures` (`--reruns 2`) | NUnit `[Retry(2)]` (assertion failures only) | JUnit plugins / Surefire `rerunFailingTestsCount` |
| Config | `playwright.config.ts` | `pytest.ini` / CLI (`--browser`, `--headed`, `--base-url` via `pytest-base-url`, `--tracing retain-on-failure`) | `.runsettings` (`<Playwright><BrowserName>`, `LaunchOptions`), env vars | Code (`BrowserType.LaunchOptions`) |
| Trace | `trace` option | `--tracing retain-on-failure` | `Context.Tracing.StartAsync/StopAsync` in setup/teardown | `context.tracing().start/stop` |
| Visual | `toHaveScreenshot` | Not built in (use a plugin, e.g. `pytest-playwright-visual`, or compare manually) | Not built in | Not built in |
| Codegen | `npx playwright codegen` | `playwright codegen` | `pwsh bin/.../playwright.ps1 codegen` | `mvn exec:java ... -D exec.args="codegen"` |

## Python example (pytest, sync)
```python
import os
import re
from playwright.sync_api import Page, expect

def test_search_shows_status(page: Page) -> None:
    page.goto(os.environ["BASE_URL"] + "/tracking")
    page.get_by_label("AWB number").fill("176-12345675")
    page.get_by_role("button", name="Search").click()
    expect(page.get_by_role("status")).to_have_text(re.compile("Departed"))
```
Auth: create `storage_state` in a session-scoped fixture and override `browser_context_args` to return `{**browser_context_args, "storage_state": path}`.

## .NET example (NUnit)
```csharp
using Microsoft.Playwright;
using Microsoft.Playwright.NUnit;

[Parallelizable(ParallelScope.Self)]
public class TrackingTests : PageTest
{
    public override BrowserNewContextOptions ContextOptions() => new()
    {
        BaseURL = Environment.GetEnvironmentVariable("BASE_URL"),
        StorageStatePath = "playwright/.auth/user.json",
    };

    [Test]
    public async Task SearchShowsStatus()
    {
        await Page.GotoAsync("/tracking");
        await Page.GetByLabel("AWB number").FillAsync("176-12345675");
        await Page.GetByRole(AriaRole.Button, new() { Name = "Search" }).ClickAsync();
        await Expect(Page.GetByRole(AriaRole.Status)).ToHaveTextAsync("Departed");
    }
}
```
.NET pitfall: a missing `await` compiles (warning CS4014) and the test may pass without asserting; treat CS4014 as an error (`<WarningsAsErrors>CS4014</WarningsAsErrors>`).

## Java example (JUnit 5)
```java
import com.microsoft.playwright.*;
import com.microsoft.playwright.junit.UsePlaywright;
import com.microsoft.playwright.options.AriaRole;
import org.junit.jupiter.api.Test;
import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;

@UsePlaywright
class TrackingTest {
  @Test
  void searchShowsStatus(Page page) {
    page.navigate(System.getenv("BASE_URL") + "/tracking");
    page.getByLabel("AWB number").fill("176-12345675");
    page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Search")).click();
    assertThat(page.getByRole(AriaRole.STATUS)).hasText("Departed");
  }
}
```

## Rules that apply to every binding
- Use the binding's web-first assertions (`expect` / `Expect` / `assertThat`), never the test framework's plain `Assert.AreEqual(await loc.TextContentAsync(), ...)`.
- No `time.sleep`, `Thread.Sleep`, `Task.Delay`, `page.wait_for_timeout`.
- Keep the Playwright package version and installed browsers in sync (reinstall browsers after upgrading).
