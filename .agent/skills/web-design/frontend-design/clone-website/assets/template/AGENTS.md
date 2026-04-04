# Website Clone Workspace

## What This Is
This workspace is a team-info scaffold for rebuilding a target site into a clean Next.js 16 codebase.

## Commands
- `npm run dev` — Start dev server
- `npm run build` — Production build
- `npm run lint` — ESLint check
- `npm run typecheck` — TypeScript check
- `npm run check` — Run lint + typecheck + build

## Working Rules
- Match the target site first. Customize only after the clone is stable.
- Treat `docs/research/` as the source of truth for tokens, behaviors, and component specs.
- Save downloaded assets under `public/images/`, `public/videos/`, and `public/seo/`.
- Keep TypeScript strict, use named exports, and avoid `any`.
- Use real captured content and assets instead of placeholders whenever possible.

## Stack Notes
- Next.js 16, React 19, TypeScript strict
- Tailwind CSS 4
- shadcn/ui primitives

## Project Structure
- `src/app/` — routes and global CSS
- `src/components/` — reusable UI pieces
- `src/lib/` — shared utilities
- `src/types/` — extracted content types
- `docs/research/` — inspection output and component specs
- `docs/design-references/` — screenshots and crops
- `public/` — downloaded assets
