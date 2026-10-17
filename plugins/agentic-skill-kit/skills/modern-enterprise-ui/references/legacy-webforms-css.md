# Restyling legacy ASP.NET WebForms / GridView pages with CSS only

Learned on a 1,000-page portal, 2026-09-02..04. Every item below cost a
regression before it became a rule.

## 1. The markup you are actually styling

A GridView renders **nested tables**: an outer layout table whose single cell
holds the grid; a header row whose cells each contain a nested *filter* table
(operator icon | text input | filter icon); a pager cell (`td.table_nav`) that
holds its own table. Any selector shaped `.grid table td` therefore matches the
wrapper cell, the filter widget cells, and the pager cells - not just data.

**The nested-table test for every grid selector:** does it match a cell that
contains a table, or sits inside the header/pager? If yes, scope it:

    /* data cells only */
    .list_table table td:not(:has(table))
    /* zebra on data rows only */
    .list_table table tr:nth-child(even):not(:has(table)) > td:not(:has(table))
    /* header by its class, never by position */
    tr.gridHeader-yellow > td
    /* pager by its class, never tr:last-child (that is the OUTER wrapper row) */
    td.table_nav, td.table_nav td

Regressions this prevented once learned: zebra painting the whole grid blue
(outer row was "even"); a `tr:last-child` rule stripping every border in the
grid; boxes under every filter input; `.list_table ~ *` hitting every sibling.

## 2. Buttons are the anchor

Legacy pattern: `<a class="orange-btn"><span><input class="blue-butn"></span></a>`.
The **anchor** paints the button; the input is only the label. Styling the
input alone leaves the anchor's slab behind it; styling both stacks two boxes
and the 34px input spills out of the 31px anchor. Rule:

    a.orange-btn:has(.blue-butn) { /* paint here: bg, border, radius */ }
    a.orange-btn:has(.blue-butn) input { background:transparent; border:0;
                                          min-height:0; color:inherit; }

Secondary variant uses `.blue-butn-no-border` - outline the anchor, transparent
input.

## 3. Floats collapse their parent

A floated toolbar (`.btn-float`) inside a plain div collapses it to 0px, so the
button overhangs whatever is below. Contain with `display: flow-root` on the
parent. **Not** `overflow: hidden` - it clips filter dropdowns.

## 4. Specificity floor

Legacy sheets use attribute selectors: `div[id$="liMode"] nav ul.abc` is
(0,2,3) - an attribute selector counts as a class. `body ul.abc !important`
loses silently. Match or exceed with `html body ...` plus a class, and prefer
one extra class over another `!important`.

## 5. Gate page-wide rules on the DOM that must exist

A sidebar rule that fires on pages without that nav renders an empty rail.
Gate: `body:has(nav ul.abc > li[id]) ...` so the rule no-ops where the
structure is absent. Any layout rule that assumes a structure gets a gate.

## 6. Width budget arithmetic

Eight columns in ~1240px: sum(min content) + 2 x padding x 8 + hairlines. The
house 14px cell padding overflowed by 46px; 6px fitted with 3px to spare.
When it does not fit: set column proportion hints on the header cells
(percentages that sum to 100), let long text wrap with `overflow-wrap:
anywhere`, and only then trim padding. Never below 6px horizontal.

## 7. Measure, do not eyeball

Row height, column width, container width, `scrollWidth - clientWidth`,
computed colours: all from `evaluate_script` (`getBoundingClientRect`,
`getComputedStyle`). A screenshot scaled to fit read 44px where the DOM said
35px. Screenshots confirm; they never measure.

## 8. What recycles the app pool (and kills the session)

Editing `*.Master`, `*.ascx`, `Web.config`, or anything under `bin/` recycles
IIS; in-process session dies; a captcha-gated login is lost. `.css`/`.js`
edits do not. **Sequence: sign in -> all authenticated verification -> then
master edits.** Cold recompile after a bin change is ~5 minutes.

## 9. Master pages and stylesheet paths

A plain `<link href="../Styles/x.css">` inside `<head runat="server">` is
emitted **verbatim** and resolves against the *page* URL, not the master's.
Pages at other depths get a 404/302. Use `href="~/Styles/x.css"
runat="server"` (an ID-less control adds no designer field, but confirm).

## 10. Encoding

Some masters are CP1252 (em dash 0x97), most are UTF-8. Detect per file; for
CP1252 byte-splice only and assert byte count, CRLF count and the marker bytes
you *measured*, not the ones a handover told you about.

## 11. Ship as one late-loaded stylesheet

Eight legacy sheets cannot be reordered safely. Add one self-contained sheet,
linked last in every master, with sections per phase and an UNVERIFIED marker
on anything written without a render. Revert = delete one link.
