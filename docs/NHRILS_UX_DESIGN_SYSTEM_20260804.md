# NHRILS UX Design System

Date: 2026-08-04

## Purpose

Define the reusable UX rules, visual tokens, shell layout, and component standards for the National Health Research Integrated Library System.

This design system supports the first catalogue shell and later NHRILS work. It is intentionally grounded in:

- NIMR identity and mandate: national health research coordination, documentation, and dissemination.
- CERN Library Catalogue pattern: search-first catalogue discovery with clear filters, record details, and help.
- InvenioILS internals: public `literature` discovery, librarian-managed `documents` and `series`, physical `items`, digital `eitems`, `locations`, `patrons`, and circulation workflows.
- Material Design principles: clear hierarchy, accessible controls, predictable surfaces, consistent spacing, and state feedback.

## Product Tone

NHRILS should feel like a national research service, not a marketing site.

Use:

- calm institutional language;
- direct action labels;
- dense but readable catalogue layouts;
- clear metadata and access states;
- strong search affordance;
- restrained color and elevation.

Avoid:

- oversized decorative hero sections after the first landing shell;
- unexplained implementation labels;
- page-local styling;
- hidden authorization behind UI state;
- mixing public catalogue and staff workflows without a clear boundary.

## Tokens

### Color

| Token | Value | Use |
| --- | --- | --- |
| `--nhrils-blue-900` | `#07365f` | Primary text, header identity, active navigation |
| `--nhrils-blue-800` | `#0b4f83` | Primary buttons, links |
| `--nhrils-blue-700` | `#126aa5` | Focus state |
| `--nhrils-blue-100` | `#e7f3fb` | Active nav and soft blue surfaces |
| `--nhrils-green-700` | `#1d8a58` | Positive state and secondary institutional accent |
| `--nhrils-green-100` | `#e8f6ef` | Soft positive chips |
| `--nhrils-gold-500` | `#d7a522` | Warnings and attention, not decoration |
| `--nhrils-ink` | `#18221d` | Body headings |
| `--nhrils-muted` | `#5c6964` | Supporting text |
| `--nhrils-border` | `#d9e5df` | Component borders |
| `--nhrils-canvas` | `#f4f8f5` | Page background |

### Typography

- Base family: Inter, Roboto, Helvetica Neue, Arial, sans-serif.
- Body text: 15-16px.
- Card heading: 18px.
- Operational section heading: 20-24px.
- Landing shell headline: 30-36px depending on viewport.
- Letter spacing: 0. Do not use negative tracking.

### Shape And Elevation

- Small radius: 4px.
- Card/surface radius: 8px.
- Use light elevation for grouped surfaces.
- Do not nest decorative cards inside cards.

### Spacing

- Page padding: 24px desktop, 16px mobile.
- Component gap: 16px.
- Major section gap: 24px.
- Field height: at least 44px.
- Button height: at least 44px.

## Shell Layout

The catalogue shell has four areas:

1. Header: NIMR logo, short system name, compact navigation.
2. Search hero: product context plus the primary search form.
3. Discovery cards: material categories and access expectations.
4. Help/workflow panel: how users search, filter, open records, and request resources.

Future authenticated staff pages should use a denser app shell, but the public catalogue entry must remain search-first.

## Route Ownership

| Route | Owner | Purpose |
| --- | --- | --- |
| `/nhrils/catalogue` | NHRILS shell | First branded public catalogue landing/search route |
| `/nhrils/catalogue/search` | NHRILS shell | Seed-backed review results, filters, and empty state before indexed import |
| `/search` | InvenioILS frontend/API integration | Future indexed search results and facets |
| `/pages/search-guide` | Static content | Search syntax help |
| `/api` | Invenio REST API | Machine-readable access |
| backoffice/admin routes | InvenioILS | Librarian and administrator workflows |

Do not duplicate the same page title in both shell and content. Route identity belongs in the shell; content starts with the current task.

## Component Rules

### Header

- Logo appears once.
- System short name appears near the logo.
- Long system name may appear as supporting text.
- Navigation labels must be short and task-based.

### Search Panel

- Search is the primary action.
- Use a visible label, not only placeholder text.
- Search examples should be chips that execute real queries.
- Advanced search links should be secondary.

### Cards

- Sibling cards use the same anatomy: icon, heading, supporting text.
- Cards in a row should have consistent padding and height behavior.
- Icons can be text placeholders in the first slice, but should later map to a shared icon set.

### Buttons

- Primary: filled NIMR blue.
- Secondary: outlined NIMR blue.
- Destructive actions are not part of the public catalogue shell.
- Buttons must have visible text.

### Status And Access

- Public metadata can be visible.
- Patron data, restricted e-items, loans, and staff actions must require backend permission checks.
- UI hiding is never authorization.

## Accessibility

- One `h1` per page.
- Search form uses `role="search"` and a visible label.
- Header navigation has an accessible label.
- Focus states must be visible.
- Links and buttons must meet contrast requirements.
- Mobile layout must keep search input and submit button readable.

## First Implementation

The first shell is implemented as an additive server-rendered route:

- route: `/nhrils/catalogue`;
- template: `invenio_app_ils/templates/invenio_app_ils/catalogue_shell.html`;
- CSS: `invenio_app_ils/static/css/nhrils-catalogue.css`;
- logo: `invenio_app_ils/static/images/nimr.svg`.

This is intentionally separate from schema, mapping, permission, circulation, and data-import work.

## Verification

For each UX slice:

1. Run focused tests for the touched route/template.
2. Confirm static assets are package-included.
3. Review desktop and mobile layout.
4. Confirm public catalogue links resolve to the intended future Invenio surfaces.
5. Confirm no restricted/patron data is exposed by the shell.
