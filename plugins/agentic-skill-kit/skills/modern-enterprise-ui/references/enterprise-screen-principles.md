# Enterprise screen principles - look and feel for operations software

Colour, type and logo come from the owning project's tokens when it has them;
hold the WCAG AA contrast floor (≥4.5:1 body text) regardless. Everything
below is shape, rhythm and behaviour, drawn in those tokens.

## 1. Who uses these screens, and what that changes

Operations staff open the same worklist fifty times a day and scan hundreds
of rows. They are experts on the data and novices on nothing. So:

- **Density is a feature.** More rows per screen beats more air per row.
- **Scanability beats expression.** Consistent column alignment, tabular
  figures, worded statuses - the eye finds the exception fast.
- **Nothing decorative.** Every rule, tint, weight and icon must encode
  information (state, grouping, hierarchy) or it goes.
- **Familiar beats novel.** A pager, a filter row, a sortable header should
  work the way the user's other ten systems work.

## 2. Density tiers - choose one per screen, say which

| Tier | Where | Row height | Body type | Cell padding |
|---|---|---|---|---|
| **Worklist** | grids, queues, listings | 32-36px | 13px | 6-8px vertical, 6-10px horizontal |
| **Form** | create/edit, detail views | 40-44px control rows | 14px | 8px grid, 16-24px between groups |
| **Dashboard** | KPI + chart surfaces | n/a | 14px body, 24-32px figures | 16-24px card padding |

Never mix tiers inside one surface. A worklist with dashboard padding is the
"looks 2010 with modern colours" failure.

## 3. The data-grid recipe

1. **Header:** no fill. One 2px rule in the primary token underneath. Labels
   small (11px), medium weight, secondary text colour. Uppercase or
   sentence case is a *choice* - see section 6 - but pick one for the product.
2. **Rows:** one hairline below each row in the neutral border token. **No
   vertical gridlines.** This single change removes most of the 2010 look.
3. **Zebra:** a tint of the cool surface token at 15-30%, never full strength
   - it must sit under the hairline, not compete with it.
4. **Hover:** the same tint at ~50%. Selected: stronger tint plus a 2px
   left rule in the primary token.
5. **Alignment:** text left, numbers right (or left in mono with tabular
   figures when mixed with text), status columns left. Header aligns with
   its column.
6. **Tabular figures** in the mono stack for IDs, phone numbers, amounts.
7. **Status is a word,** optionally with a tint; never colour alone.
8. **Filter row** lives with the header, visually quiet: 1px neutral border,
   small radius (4px), fills its cell, focus ring in the primary token.
   Icons are 16px and never wider than the input they serve.
9. **Pager** is chrome: no borders, secondary text, primary-token links,
   one filled primary button at most.
10. **Container** is one card: surface token, 1px neutral border, 8px radius,
    understated cool shadow. Not a card inside a panel inside a box.
11. **Empty state, loading state, error state** exist and are designed.
12. **Width budget** is computed, not hoped for (see legacy-webforms-css.md 6).

## 4. Layout rhythm

- 8px grid. Spacing values: 4 / 8 / 16 / 24 / 40.
- Page title -> 8px -> toolbar/card. Not 40px of air.
- Toolbars hold actions on the right and context (count, active filters) on
  the left. An empty left half is a design smell: fill it or remove the bar.
- Side navigation: 200-240px, primary-token ground, 13-14px labels, current
  item marked by a fill or a left rule - not by colour alone.
- Content claims the full width the container offers. Margins are for the
  container, not for the table inside it.

## 5. States and accessibility floor

- Visible `:focus-visible` on every interactive element, in the primary or
  accent token of the project's palette.
- Hover changes are subtle (brightness or a tint), 120-200ms, no bounce.
- Hit targets 28px minimum in a worklist, 36px in a form.
- Text never below 12px; secondary text uses the secondary token, never a
  lighter grey invented for the purpose.
- Reduced-motion respected. Colour is never the only signal.

## 6. Working with `frontend-design` (and where it must not win)

`frontend-design` is excellent for **direction**: it stops a screen from
looking like every other generated page and forces deliberate choices. Use it
when a surface needs an identity - a landing, a dashboard hero, a login.

But it is written for expressive web pages and lists as anti-patterns several
things that are **correct** on a dense operations grid:

| `frontend-design` says avoid | On a worklist |
|---|---|
| All-caps labels | Acceptable for column headers and status pills if the product uses them consistently - it is the common enterprise-grid convention |
| Mono for small data labels | Correct for IDs, references and figures - tabular alignment is the point |
| Hairline rules, zero radius, dense columns | Exactly the worklist recipe above |
| Middle-dot meta strings | Fine for compact meta lines in a toolbar |

Resolution (design-brand-tokens-vs-look-and-feel.md was withdrawn 2026-09-07
with the `kale-design` skill it cited — ledger row 91; that local skill is now `kale-docs-brand`, documents only): **tokens win on brand,
design wins on layout - and on a worklist, scanability is the design goal.** Take `frontend-design`'s discipline (one bold thing, remove
an accessory, no default gradients/shadows/cards-in-cards) and leave its
editorial-page taste where it conflicts with density. Say which you did.

## 7. Self-critique before hand-off

- Can a user find the one exceptional row in under two seconds?
- Is there anything on the screen that carries no information? Remove it.
- Does every colour trace to a token name? Does every measurement come from
  the DOM?
- Would a 2010 GridView user recognise how to sort, filter and page? Good.
  Would they mistake it for 2010? Then the header fill, vertical gridlines
  or boxed pager is still there.
