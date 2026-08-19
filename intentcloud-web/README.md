# IntentCloud Frontend

Intent-aware cognitive cloud memory system - Next.js + React frontend with TypeScript, Tailwind CSS, and light/dark theme support.

## Overview

IntentCloud Frontend is a modern web interface for uploading documents, searching with natural language queries, and viewing document statistics. Built with Next.js 16+ (App Router), featuring semantic search capabilities powered by AI-driven intent parsing on the backend.

**Phase 1-3 Implementation:** Data ingestion, embeddings, intent parsing, and semantic search UI.

## Features

- **📤 Document Upload** - Drag-and-drop interface for PDF, DOCX, and TXT files
- **🔍 Semantic Search** - Natural language queries with AI intent understanding
- **📊 Dashboard** - Real-time statistics on stored documents and embeddings
- **🌓 Theme Switching** - Light/Dark/System theme with localStorage persistence
- **♿ Accessible Design** - WCAG AA compliance, keyboard navigation, screen reader support
- **📱 Responsive** - Mobile, tablet, desktop, and ultrawide breakpoints
- **⚡ Fast** - Next.js Turbopack, optimized fonts, efficient CSS

## Tech Stack

- **Framework:** Next.js 16.3.1 (App Router, TypeScript)
- **Styling:** Tailwind CSS 4, custom design tokens
- **Runtime:** Bun 1.3.14
- **Fonts:** Fraunces (headings), Inter (body)
- **State:** React hooks, localStorage
- **API Client:** Fetch API (native)

## Project Structure

```
intentcloud-web/
├── app/
│   ├── layout.tsx                 # Root layout with theme script
│   ├── page.tsx                   # Home page
│   ├── globals.css                # Design tokens + responsive rules
│   ├── upload/
│   │   └── page.tsx               # Upload page with drag-drop
│   ├── search/
│   │   └── page.tsx               # Search page with results display
│   └── dashboard/
│       └── page.tsx               # Stats and memory profile
├── components/
│   ├── Navbar.tsx                 # Navigation + theme toggle
│   └── ThemeProvider.tsx           # Client-side theme provider
├── .env.local                     # Frontend config (API URL)
├── package.json                   # Dependencies & scripts
├── next.config.ts                 # Next.js config
├── tailwind.config.ts             # Tailwind CSS config
├── tsconfig.json                  # TypeScript config
└── README.md                      # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ or Bun 1.3+
- Backend API running on `http://localhost:8000` (see `../intentcloud-api/`)

### Installation

```bash
# Install dependencies with Bun
bun install

# Or with npm
npm install
```

### Environment Setup

Create/update `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start dev server with Bun
bun run dev

# Or with npm
npm run dev
```

The app opens at `http://localhost:3000` with hot reload enabled.

### Build

```bash
# Build for production
bun run build

# Start production server
bun run start
```

## Pages

### Home (`/`)
Landing page with project description, feature overview, and call-to-action buttons to upload and search.

### Upload (`/upload`)
Drag-and-drop file upload interface. Supports PDF, DOCX, and TXT files up to 50 MB. Shows upload status and file metadata.

### Search (`/search`)
Natural language search interface. Queries are sent to the backend for intent parsing and semantic search. Results display relevance scores and document excerpts.

### Dashboard (`/dashboard`)
Statistics dashboard showing:
- Total vectors stored
- Total files indexed
- Collection metadata
- Memory profile and performance metrics

## Design System

### Colors (Design Tokens in `app/globals.css`)

**Light Theme (default):**
- Background: `#FAF9F6`
- Surface: `#FFFFFF`
- Text Primary: `#1C1917`
- Text Secondary: `#6B6560`
- Accent: `#B45F3C` (warm terracotta)

**Dark Theme (`.dark` class):**
- Background: `#15130F`
- Surface: `#1E1B17`
- Text Primary: `#F2EFE9`
- Text Secondary: `#A8A29A`
- Accent: `#E08556` (lighter terracotta)

### Responsive Breakpoints

- **Mobile:** 360–639px (base styles)
- **Tablet:** 768–1023px (medium adjustments)
- **Desktop:** 1024px+ (large layouts)
- **Ultrawide:** 1280px+ (max content width)

### Typography

- **Headings (h1-h6):** Fraunces serif, 600 weight
- **Body:** Inter sans-serif, 400 weight
- **UI Elements:** Inter sans-serif, 500 weight

## Theme Switching

Theme preference is determined by:
1. User selection (Light/Dark/System) → stored in `localStorage`
2. System preference (if "System" selected) → `prefers-color-scheme` media query
3. Fallback → Light theme

Theme is applied via inline script in `<head>` to prevent hydration mismatch.

## API Integration

### Endpoints

All requests go to the backend at `NEXT_PUBLIC_API_URL`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/upload` | POST | Upload document (multipart/form-data) |
| `/search` | POST | Search documents (query, top_k params) |
| `/stats` | GET | Get collection statistics |
| `/files` | GET | List uploaded files (debug) |
| `/download/{file_id}` | GET | Download stored file |

### Example: Upload

```typescript
const formData = new FormData();
formData.append('file', fileInput);

const response = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData,
});

const { file_id, status } = await response.json();
```

### Example: Search

```typescript
const response = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'my search', top_k: 3 }),
});

const { results, parsed_intent } = await response.json();
```

## Accessibility

- ✓ WCAG AA compliant color contrast
- ✓ Semantic HTML (`<button>`, `<nav>`, `<main>`, etc.)
- ✓ Keyboard navigation (Tab, Enter, Escape)
- ✓ Screen reader labels (`aria-label`, `aria-describedby`)
- ✓ Focus indicators (visible focus rings)
- ✓ Reduced motion support (`prefers-reduced-motion`)
- ✓ Touch targets ≥ 44×44px

## Performance

- **Code Splitting:** Automatic per-route
- **Image Optimization:** Next.js `Image` component (not used yet, but available)
- **Font Optimization:** `next/font` for self-hosted fonts
- **CSS:** Tailwind purging + minification
- **Caching:** Static export friendly

## Development Notes

### Adding New Pages

Create a new folder in `app/` with `page.tsx`:

```typescript
// app/example/page.tsx
export default function ExamplePage() {
  return <h1>Example</h1>;
}
```

Routes are auto-generated based on file structure.

### Styling

Use Tailwind CSS utilities and design tokens:

```tsx
<div className="bg-[var(--bg-surface)] text-[var(--text-primary)]">
  ...
</div>
```

### Environment Variables

Prefix with `NEXT_PUBLIC_` to expose to the browser:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Non-public vars are server-side only.

## Debugging

### Hot Reload Issues
If changes don't reflect, restart the dev server:

```bash
bun run dev
```

### Theme Not Persisting
Check browser `localStorage` → ensure `localStorage.getItem('theme')` returns a value.

### API Connection Errors
Verify backend is running on `http://localhost:8000`:

```bash
curl http://localhost:8000/health
```

## Deployment

### Vercel (Recommended)

```bash
# Link to Vercel
bun dlx vercel

# Deploy
bun dlx vercel deploy
```

Set environment variable in Vercel dashboard:
- `NEXT_PUBLIC_API_URL` → production backend URL

### Self-Hosted

```bash
bun run build
bun run start
```

Or use Docker:

```dockerfile
FROM oven/bun:latest
WORKDIR /app
COPY . .
RUN bun install && bun run build
EXPOSE 3000
CMD ["bun", "run", "start"]
```

## Testing

Manual testing documented in `../TESTING_GUIDE.md`.

End-to-end tests (Task #17-18):
1. Upload a test PDF/DOCX
2. View stats on dashboard
3. Search with natural language
4. Verify results display correctly

## Known Limitations (Phase 1-3)

- No user authentication
- No mobile-specific app (web only)
- Search results limited to dense similarity (no hybrid/BM25 until Phase 4)
- No result filtering by date or document type
- Single-user system (all uploads stored globally)

## Future Work (Phase 4+)

- Hybrid search with sparse BM25 + dense reranking
- User authentication and per-user document storage
- Advanced filtering and faceting
- Export search results
- Document versioning and history
- Batch upload processing

## Contributing

See `../IMPLEMENTATION_PLAN.md` for development roadmap.

Phase 1-3 implementation: August 2026
Phase 4+: Later phases (not yet implemented)

## License

MIT (see root `LICENSE` if present)

## Support

For backend issues, see `../intentcloud-api/README.md` (if present).
For overall project details, see `../README_IMPLEMENTATION.md`.

---

**Last Updated:** August 19, 2026  
**Version:** 1.0.0 (Phase 1-3)  
**Status:** Beta - Ready for testing
