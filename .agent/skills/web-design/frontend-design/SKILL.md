---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces and landing pages, including image-first LPs where generated/Figma-exported images are the primary page surface. Use when building web pages, LPs, dashboards, React components, posters, polishing UI, or preparing static pages for deployment.
---

# Frontend Design Skill

## Goal
- Build bold, intentional frontend UI that is ready for real use.
- Avoid generic boilerplate visuals.

## Workflow
1. Confirm stack and target page/component.
2. Implement design system tokens first (color, spacing, type scale).
3. Build layout and responsive behavior (desktop and mobile).
4. Add meaningful motion only where it improves clarity.
5. Verify build/lint and provide deploy command when requested.

## Image-first LP Rule
- If the user says images should be used as the LP itself, start by stacking the generated/exported images as `<img>` elements in the intended order.
- Do not rebuild image text as large HTML cards unless the user explicitly wants coded sections.
- Add code only where the image cannot provide behavior: CTA links, form anchors, tracking hooks, accessibility labels, responsive page framing.
- Keep image filenames stable and check every referenced image loads before styling around it.

## Deployment Guard
- For static HTML LPs, prefer deploying the exact output directory, not the whole repo.
- Before Vercel/Netlify commands that can send files externally, state the security risks and get chat approval if required by repo rules.
- Avoid long preflight commands that can hang. Use `command -v vercel` / `command -v netlify` first; do not run `vercel --version` or login/deploy commands without a short timeout or user approval.
- If the CLI is missing or login is interactive, give the user a one-line absolute-path command instead of blocking the session.

## Quality Rules
- Use purposeful typography and clear hierarchy.
- Prefer reusable components over one-off style blocks.
- Keep accessibility basics: contrast, focus, semantic structure.
- If project style already exists, follow it instead of reinventing.
