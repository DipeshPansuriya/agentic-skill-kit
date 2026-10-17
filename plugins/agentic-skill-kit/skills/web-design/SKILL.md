---
name: web-design
description: "Use when Dipesh wants a marketing site, landing page, or visual redesign that must not look like generic AI UI. Five stages: extract a design system, write tokens, build, Playwright-check, then tighten with numbers. Not for data-dense admin screens (use modern-enterprise-ui) or ordinary component bugs (use frontend-engineering)."
user-invocable: true
---

# Web design (design system first)

This file in DipeshPansuriya/agentic-skill-kit is the whole skill. Do not fetch another owner's GitHub tree. `frontend-design` (official plugin already on) is the only extra pack.

**The design system goes in before the first line of code.** Separate prompts per stage. Playwright stays on (`## playwright-on-the-branch`): first look may use MCP; the artifact is a spec in the **code root**; next run is `npx playwright test`.

Do not copy another product's name, logo, sounds or palette. Take structure; invent tokens. Figma MCP is on UI agents (sign in on first use). Session model stays `inherit`.

## Anti-slop (house)

A model default looks like: centred headline, three icon cards, soft gradient, thin rules, monospace caption. Reject that.

- The idea comes from **this** subject, not a template category.
- Type set larger; whole fields of colour; real pictures of this subject's world (Dipesh's assets or credited open archives).
- No fake stock heroes. No ornaments that do not carry content.
- Motion is restraint (duration, easing, what moves) — not another product's visual brand.

## Five stages

### 1 · Reference in — do not build

Paste a Figma frame link or named *feel* URLs.

```
Read this Figma frame with the Figma MCP: [link]
Don't build anything. Extract the design system as a list: every
color with its role, the type scale (size, weight, line height), the
spacing values, corner radii, shadows, and every component.
```

No Figma? Name 1–2 sites for feel only, then invent tokens (never clone their brand).

### 2 · Design system file

Turn that list into tokens (`DESIGN.md` or the project's token CSS). Later pages only use these values.

### 3 · Build from a director brief

```
Build a marketing site for [business]. Audience: [who]. Feeling: [e.g. clean, premium].
Reference the feel of [1 or 2], not their brand.
Pages: [list]. Home: hero with one promise, 3 benefits, proof, FAQ, one CTA.
Brand: colors [hex], fonts [names] from DESIGN.md.
```

Enterprise admin / grids → `modern-enterprise-ui`.

### 4 · Check in a real browser

Screenshot desktop and mobile. Fix spacing, overflow, alignment. Commit the Playwright spec on the task branch; re-run `npx playwright test`.

### 5 · Refine with numbers, not vibes

```
Tighten the hero: more whitespace, larger headline, one button not two.
Make section spacing consistent at [N]px. Fix the mobile nav overflow.
Show before and after screenshots.
```

## When it looks generic

| Symptom | Fix |
|---|---|
| Flat AI template | No reference or skipped tokens. Restart from stage 1. |
| Cramped / misaligned | Exact spacing + fully responsive; Playwright on mobile. |
| Fake stock heroes | Real credited photos. Rebuild around them. |

## Hand-off

Stage done, DESIGN.md path, screenshot paths, Playwright spec path, every colour traced to a token. Unmeasured items tagged UNVERIFIED.
