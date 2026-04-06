# Web Functionality Audit

Historická poznámka:
tenhle soubor zachycuje tehdejší stav webu a tehdejší UX priority. Ber ho jako vývojový audit, ne jako definitivní popis současného UI.

Date: `2026-04-06`

Scope audited:

- public GitHub Pages site in `docs/`
- public web source scripts in `site_src/static/`
- shared styles in `app/static/styles.css`

## Summary

The web already had strong data depth, but several functions were clearer in code than in the actual user experience. The main gaps were:

- filters were powerful, but hard to read as a current search state
- sorting was implicit rather than user-controlled
- evidence grading was compact but under-explained
- detail pages were rich, but long and not easy to scan quickly
- gallery and search had useful controls, but not enough guidance for practical exploration

The first improvement wave focused on the easiest high-value upgrades first:

- clearer labels and action names
- explicit active-filter summaries
- user-controlled sorting
- a new `How well known` filter
- evidence labels with human-readable meaning
- better empty states and helper tips
- quick navigation inside detail pages

## Functionality Inventory And Decisions

| Area | Functionality | Current Value | Improvement Decision | Status |
|---|---|---|---|---|
| Home | Summary stats cards | Good orientation | Keep; already useful | Keep |
| Home | Fulltext search across names/effects/processes | High value | Add stronger guidance/examples | Improved now |
| Home | Domain filter | Useful | Keep | Keep |
| Home | Minimum evidence filter | Useful but too abstract | Explain evidence grades directly in labels | Improved now |
| Home | Plant-part category filter | Useful | Keep | Keep |
| Home | Use-category filter | Useful | Keep | Keep |
| Home | Processing-method filter | High practical value | Keep and surface active state more clearly | Improved now |
| Home | Manual month filter | Useful but secondary | Keep; make current state more visible | Improved now |
| Home | Seasonal toggle with month buffer | Strong default behavior | Keep and display more clearly as an active constraint | Improved now |
| Home | Durable-only filter | High practical value | Keep and make active state clearer | Improved now |
| Home | Core-only filter | High practical value | Keep and make active state clearer | Improved now |
| Home | Result limit selector | Useful | Keep and explain when it truncates output | Improved now |
| Home | URL-persisted filter state | Strong | Keep | Keep |
| Home | Debounced live filtering | Strong | Keep | Keep |
| Home | Result cards with photos and metadata | Strong base | Improve action clarity and badge readability | Improved now |
| Home | Card action split: use detail vs plant detail | Useful | Rename actions to be explicit | Improved now |
| Home | Hidden “knowledge rarity” in data | Missing in UI | Expose as direct filter because it is practically valuable | Improved now |
| Home | Sorting | Missing explicit control | Add user-facing sorting options | Improved now |
| Home | Active filter overview | Missing | Add visible chip summary with quick removal | Improved now |
| Home | Empty state guidance | Too generic | Make suggestions context-sensitive | Improved now |
| Gallery | Separate plant gallery entry point | Strong | Keep | Keep |
| Gallery | Plant search | Strong | Add better hinting for usage style | Improved now |
| Gallery | Seasonal plant filter | Strong | Keep and show as active state | Improved now |
| Gallery | Durable/core filters | Strong | Keep and surface active state more clearly | Improved now |
| Gallery | Gallery limit selector | Useful | Keep and explain truncation | Improved now |
| Gallery | Plant cards with counts | Strong | Improve export/profile labels | Improved now |
| Gallery | Gallery sorting | Missing explicit control | Add user-facing sorting options | Improved now |
| Gallery | Gallery active filter overview | Missing | Add visible chip summary with quick removal | Improved now |
| Gallery | Knowledge rarity exploration | Missing | Add direct filter to help niche discovery | Improved now |
| Gallery | Photo-count visibility | Useful | Rename “Media” badge to “Fotky” | Improved now |
| Detail | Standalone plant detail pages | Strong | Keep | Keep |
| Detail | Standalone use detail pages | Strong | Keep | Keep |
| Detail | Copy link | Useful | Keep | Keep |
| Detail | Markdown export | Strong | Rename more clearly as a download action | Improved now |
| Detail | JSON export | Strong | Rename more clearly as a download action | Improved now |
| Detail | Photo provenance | Strong | Keep | Keep |
| Detail | Use detail sections (prep/effect/gathering/risks/etc.) | High practical value | Keep, but improve scanability | Improved now |
| Detail | Plant detail sections (status/uses/sources) | High value | Keep, but improve scanability | Improved now |
| Detail | Long-page navigation | Missing | Add quick section navigation | Improved now |
| Detail | Source presentation | Informative but visually noisy | Replace raw URL text with a clearer “Open source” action | Improved now |
| Detail | Use links inside plant detail | Useful | Rename to “Detail použití” for clarity | Improved now |
| Infra | Static routing for `/`, `/plants/`, `/plant/...`, `/use/...` | Strong | Keep | Keep |
| Infra | 404 deep-link recovery | Strong | Keep | Keep |
| Infra | Static client-side filtering from JSON bundle | Strong | Keep | Keep |
| Infra | External source links open separately | Good | Keep | Keep |

## Implemented In This Wave

### Clarity

- Explicit action labels on cards and detail pages
- Human-readable evidence labels such as `A · nejsilnější opora`
- Better helper text in search/filter panels
- Clearer wording for exports and source links

### Usefulness

- New `Jak známé` filter on search and gallery pages
- New explicit sorting on search and gallery pages
- Better empty states with actionable suggestions

### Consistency

- Active filter chips on both search and gallery pages
- Shared filter-state phrasing across both page types
- Consistent “Praktické jádro” wording
- “Fotky” wording instead of generic “Media”

### Practical Navigation

- Quick section navigation inside plant and use details
- Better explanation of when the result limit is hiding items
- Faster removal of individual active filters directly from chip buttons

## Later Improvements Worth Doing

- Add saved search presets such as `jídlo do zásoby`, `méně známé dubnové`, `jen opravdu silně doložené`
- Add direct “related plants” and “related processing methods” on detail pages
- Add comparison mode for two or more plants
- Add richer availability explanation on cards, not only in detail
- Add a dedicated “hidden gems today” landing section
- Add lightweight analytics-friendly event tracking for which filters users rely on most
