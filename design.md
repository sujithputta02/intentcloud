---
name: intentcloud-frontend-design
description: Design system and build rules for the IntentCloud Next.js + Tailwind frontend (Upload, Search, Dashboard, Download). Reference this before building or restyling any IntentCloud page or component. Encodes the premium file-manager aesthetic from the approved reference screenshot, adapted to IntentCloud's actual feature set, with mandatory light/dark theming and full device responsiveness.
---

# IntentCloud Frontend Design Skill

This is the design contract for the IntentCloud web app (`intentcloud-web`, Next.js App Router + Tailwind CSS, per PRD v3.0 §5.1 / §9). Read this before writing or editing any page, layout, or component. It translates the approved reference screenshot (a premium cloud file-manager) into rules specific to IntentCloud's real product: **semantic, intent-aware file retrieval — not folder browsing.**

Every screen must ship in a light theme, a dark theme, and every breakpoint from 360px to 1920px+ before it is considered done. This is not a checklist to do at the end — build responsive and theme-aware from the first component.

---

## 1. Ground the design in the actual product

The reference screenshot is a generic multi-tenant file manager (folders, collaborators, "Invite Collaborators," file-type filter pills). IntentCloud is **not** that product — do not copy it feature-for-feature. Borrow its *quality bar and layout grammar* (warm greeting hero, soft card grid, pill filters, calm neutral base with one accent color), and rebuild the content around what IntentCloud actually does per the PRD:

| Screenshot concept | IntentCloud equivalent | Why it changes |
|---|---|---|
| "Good morning, Emir" hero banner over a photo | "Good morning, {name}" hero over a **flat gradient**, not a stock photo — IntentCloud has no brand photography and a photo hero reads as templated | Keeps the warmth, drops the generic stock-photo tell |
| Folder cards with avatar stacks ("Stuffed," "Rebranding," 21 files, 3 collaborators) | **Topic tag cards** ("Kafka & Microservices," "Thesis Drafts," "12 files") — no folders exist in IntentCloud; topic clusters come from embeddings, not manual organization (PRD §5.1, Memory Profile Dashboard) | There is no login/collaborator system in Phase 1 (PRD §5.2 Deferred Features) — never show avatar stacks or "Invite Collaborators" |
| "New Files / New Folders / Invite Collaborators" menu | A single primary action: **"Upload files"** — opens the drag-and-drop uploader (PRD Feature 1) | No folder concept, no multi-user invites in Phase 1 |
| "All files / PDF / Photos / Vectors" pills + "Most opened" sort | **"All files / PDF / DOCX / TXT"** pills + a **search bar as the primary control**, not a secondary sort dropdown | Natural-language search (PRD Feature 2) is the product's entire reason to exist — it must dominate the page, not sit below a file grid like an afterthought |
| Colored folder-style file icons | Colored **file-type badges** (PDF / DOCX / TXT) plus a **relevance score chip** on search-result cards ("92% match") | Relevance and "why this matched" (PRD Feature 2) is unique, load-bearing information the reference design has no equivalent for — invent this pattern, don't skip it |

If a screen doesn't map to a PRD feature (Upload, Search, Dashboard/Memory Profile, Download), don't build it. No settings pages, no billing, no team management — that's explicitly Deferred (PRD §5.2).

---

## 2. Design tokens

Describe every token as a CSS custom property in `globals.css`, referenced from Tailwind via `theme.extend.colors` — never hardcode hex values inside components.

### 2.1 Color — light theme (default, `:root`)

| Token | Value | Use |
|---|---|---|
| `--bg-base` | `#FAF9F6` | Page background — warm off-white, not stark `#FFFFFF` |
| `--bg-surface` | `#FFFFFF` | Cards, panels |
| `--bg-hero` | linear-gradient(135deg, `#3D2C2E` → `#8C5E58` → `#D9A679`) | Greeting hero — warm dusk gradient, echoes the screenshot's photo tone without using a photo |
| `--text-primary` | `#1C1917` | Headings, body |
| `--text-secondary` | `#6B6560` | Meta text (timestamps, file size) |
| `--border-subtle` | `#E8E5DF` | Card borders, dividers |
| `--accent` | `#B45F3C` | Primary actions, active pill, focus ring — a muted terracotta, warmer/darker than the Claude-orange tell (`#D97757`) so it doesn't read as a default |
| `--accent-hover` | `#9C4F30` | Hover/pressed state of accent |
| `--success` | `#3F7D58` | High relevance score, "Done" status |
| `--warning` | `#B8860B` | Medium relevance, "In Progress" |
| `--danger` | `#B3392C` | Delete, failed upload |
| `--badge-pdf` | `#C96A45` | PDF file-type badge |
| `--badge-docx` | `#3B6FA0` | DOCX file-type badge |
| `--badge-txt` | `#5C8A5C` | TXT file-type badge |

### 2.2 Color — dark theme (`.dark` class on `<html>`)

| Token | Value |
|---|---|
| `--bg-base` | `#15130F` |
| `--bg-surface` | `#1E1B17` |
| `--bg-hero` | linear-gradient(135deg, `#120E0C` → `#3D2C2E` → `#6B4A44`) |
| `--text-primary` | `#F2EFE9` |
| `--text-secondary` | `#A8A29A` |
| `--border-subtle` | `#332E28` |
| `--accent` | `#E08556` |
| `--accent-hover` | `#EFA279` |
| `--success` | `#5FAE7A` |
| `--warning` | `#D4A72C` |
| `--danger` | `#E0685A` |
| `--badge-pdf` / `--badge-docx` / `--badge-txt` | Same hues, lightness raised ~12% for AA contrast on dark surfaces |

Every color pair must hit **WCAG AA (4.5:1)** for body text and **3:1** for large text/icons. Check both themes independently — a pair tuned for light mode is not assumed to pass in dark mode.

### 2.3 Typography

- Display / headings: **Fraunces** (variable, serif) — gives the "Good morning" hero warmth and personality without reaching for generic system-UI sans everywhere.
- Body / UI: **Inter** — for file names, buttons, form fields, table data. Never mix in a third typeface.
- Scale: `text-3xl` (hero greeting) → `text-xl` (section headers: "My files") → `text-base` (file names) → `text-sm` (meta: size, timestamp) → `text-xs` (badges).
- Weight: 600–700 for headings, 500 for file names/buttons, 400 for meta text. Avoid 800/900 — it reads as a template default at this content density.

### 2.4 Spacing, radius, elevation

- Spacing scale: Tailwind default (4px base unit) — `gap-2/3/4/6/8` between related elements, `gap-8/12` between sections.
- Radius: `rounded-2xl` (16px) on cards and the hero panel, `rounded-full` on pills/badges/avatars, `rounded-lg` (8px) on buttons and inputs. Consistent radius family across the whole app — don't mix 8px and 12px on sibling elements.
- Elevation: flat by default (`border` + `bg-surface`, no shadow) at rest; `shadow-sm` only on hover/focus of interactive cards. The reference screenshot is largely shadow-free and flat — keep that; do not add drop shadows to every card, it reads as a template default.

---

## 3. Theme switching (mandatory)

Every page must work correctly in three states: **system-linked**, **forced light**, **forced dark**. Implement exactly this pattern — do not invent a different mechanism:

1. **Tailwind config**: `darkMode: 'class'` in `tailwind.config.ts`.
2. **Preference source of truth**: a `theme` value in `localStorage` (`'light' | 'dark' | 'system'`), read in a tiny inline `<script>` in `app/layout.tsx`'s `<head>` **before** hydration, so there is no flash of the wrong theme. If no stored value exists, default to `'system'` and resolve it against `window.matchMedia('(prefers-color-scheme: dark)')`.
3. **Live updates**: while `theme === 'system'`, subscribe to the `matchMedia` change event so the UI flips automatically if the OS theme changes mid-session — don't require a reload.
4. **User control**: a three-way toggle (Light / Dark / System) in the top-right of the app shell, next to the notification bell position from the reference screenshot. Persist the choice back to `localStorage` on change.
5. **Never** use `prefers-color-scheme` in raw CSS media queries as the only mechanism — it must be overridable per-device, since a person may want IntentCloud dark while their OS is light (or vice versa). System preference is the *default*, not a hard rule.

```ts
// app/layout.tsx — inline, before hydration
const script = `
  (function () {
    const stored = localStorage.getItem('theme') || 'system';
    const isDark = stored === 'dark' ||
      (stored === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', isDark);
  })();
`;
```

---

## 4. Responsive rules (mandatory, all breakpoints)

Build mobile-first; verify at minimum these widths before calling any screen done:

| Breakpoint | Width | Layout behavior |
|---|---|---|
| `base` | 360–639px (phone) | Single column everywhere. Hero collapses to greeting + one-line subtext, no decorative gradient height beyond ~120px. Topic-card row becomes a horizontally scrollable strip (`overflow-x-auto snap-x`), not a wrapped grid. File grid becomes a single-column stacked list. Filter pills scroll horizontally, don't wrap. Search bar is full-width and sticky under the header. |
| `sm` | 640–767px | Topic cards: 2 per row. File grid: 1 column, wider cards. |
| `md` | 768–1023px (tablet) | Topic cards: 3 per row. File grid: 2 columns. Sidebar (if present) collapses to icon-only rail. |
| `lg` | 1024–1279px (small laptop) | Topic cards: 4 per row, matches reference screenshot density. File grid: 3 columns. |
| `xl` | 1280px+ (desktop) | Topic cards: up to 5 visible + scroll affordance, matching the reference's partially-cut-off 5th card. File grid: 3–4 columns, max content width `max-w-7xl` centered — never stretch cards edge-to-edge on ultrawide monitors. |

Rules that apply at every breakpoint:
- Touch targets ≥ 44×44px on any layout that can be touched (this includes laptop touchscreens — don't assume mouse-only below `lg`).
- No horizontal scroll on the page body itself, ever — only intentionally on the topic-card strip and pill row.
- The upload drop-zone must remain reachable and usable down to 360px width (stack the "browse" button under the drop text, don't shrink the tap target).
- Test with the OS text-size setting increased (or Tailwind's `text-base` respecting `rem`, not `px`) — layouts must not break when a person increases their base font size.

---

## 5. Component patterns (map 1:1 to PRD features)

### 5.1 App shell / header
Sticky top bar: IntentCloud wordmark (left) · global search-adjacent nothing else — keep it minimal · theme toggle + a single settings-free avatar placeholder (right). No notification bell unless/until a real notification feature exists (PRD §5.2 explicitly defers this kind of scope) — do not add UI for features that don't exist yet, even if the reference screenshot has one.

### 5.2 Dashboard / Memory Profile (PRD Feature 4)
- Greeting hero (gradient, §2.1/§2.2) with "Good morning/afternoon/evening, {name}" and a one-line subtext pulling from real stats: *"You have 214 files stored across 8 topics."* Never a static filler line.
- Topic tag cards, horizontally scrollable strip, each showing: topic name, file count, a muted topic-colored icon (no avatar stacks — there are no collaborators in Phase 1).
- Below: **"My files"** section with type-filter pills (`All / PDF / DOCX / TXT`) and the file grid. Each file card shows: type badge, filename, size, "Uploaded {relative time}" — matches the reference screenshot's card anatomy closely since it already fits the product.

### 5.3 Upload (PRD Feature 1)
- Large, centered drop-zone as the primary element on this page (not a modal triggered from a "+" menu like the reference's "New Files" popover — a full upload page deserves a full-width drop-zone).
- On drop/select: inline progress per file, then an auto-detected topic-tag chip once extraction + embedding finish server-side, confirming Feature 1's "upload confirmation with auto-detected topic tags."

### 5.4 Search (PRD Feature 2 — the product's core screen)
- Search bar is the hero of this page: large, centered near the top, placeholder text using a real example from the PRD's own scenario: *"Find the report where I discussed Kafka and microservices."*
- Results render as cards, each with: filename, type badge, a **relevance score chip** (color-coded via `--success/--warning`), and a one-line "why this matched" explanation string from the API. This explanation line is unique to IntentCloud — it is the single most important piece of UI in the whole app per the PRD's differentiation claim; never let it be visually secondary to the filename.
- Empty state (no query yet): don't show a blank page — surface 3–4 example queries as tappable chips, sourced from real corpus topics once available.

### 5.5 Download
- Triggered from a result or file card, not a separate page. Direct browser download from the Pi/USB-served URL (PRD §5.3 step 7) — no intermediate "preparing your file" spinner unless the actual request is slow enough to need one.

---

## 6. Voice and copy

Match PRD language exactly where it exists — "Find the report where I discussed Kafka and microservices," "acting as an extended cognitive memory for the user" — real examples beat invented placeholder copy. Buttons say what they do: "Upload files," not "Get Started." Empty and error states explain what happened and what to do next, in plain language, never apologetic filler ("Oops!").

---

## 7. Before calling any screen done

- [ ] Built and screenshotted at 360px, 768px, 1280px, and 1920px
- [ ] Verified in both light and dark theme, plus the system-linked default
- [ ] Verified the theme toggle persists across a reload and doesn't flash the wrong theme on load
- [ ] Every element traces to a real PRD feature (Upload / Search / Dashboard / Download) — nothing copied from the reference screenshot that doesn't apply (no folders, no collaborators, no "Invite")
- [ ] Color contrast checked in both themes, not just light
- [ ] No horizontal scroll except the intentional topic-card strip and filter-pill row