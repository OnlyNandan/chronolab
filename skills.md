---
name: doc-first-ai-coding
description: Use when starting an AI coding project or setting up a repo.
version: 1.2.0
author: Nithin
license: MIT
metadata:
  hermes:
    tags: [ai-coding, documentation, agents, workflow, planning]
    related_skills: [plan, test-driven-development, systematic-debugging]
---

# Doc-First AI Coding System

The failure mode of AI-assisted coding is not lack of coding ability — it's lack of
discipline and context preservation. AI tools run with high capability but low
certainty. Without locked constraints and authoritative docs, they hallucinate
requirements, make unauthorized architectural decisions, and build things you
never asked for. Fix it with a documentation-first system.

## When to Use

- Starting a brand-new AI-assisted coding project from scratch.
- Setting up a repo so a coding agent (OpenCode, Claude Code, etc.) stays aligned across sessions.
- You keep hitting hallucinated requirements, random dependency picks, or inconsistent UI from the agent.
- You want a reusable doc-first scaffold instead of letting the agent freeform the architecture.

## Configuration (resolved for Nithin's stack)

The vendor/tool placeholders are now filled for your setup. Values you explicitly
chose are marked (pick); the rest are the guide's documented defaults, swappable
later.

| Value | Role | Source |
|---|---|---|
| `AGENTS.md` | root rules file OpenCode reads each session | pick |
| `CLAUDE.md` | root rules file Claude Code reads each session | pick |
| `.opencode/` | per-tool rules dir (OpenCode) | pick |
| `OpenCode CLI` | AI coding agent | pick |
| `Claude Code` | AI coding agent | pick |
| `Codex` | debug / finalize agent | pick |
| `React + Vite` | frontend framework (TypeScript) | pick |
| `Python (FastAPI)` | backend framework, venv/uv env | pick |
| `Supabase` | db + auth, via SQLAlchemy ORM | pick |
| `pnpm workspace` | TS monorepo tooling | pick |
| `Docker` | containerized dev/deploy | pick |
| `GitHub` | git host | pick |
| `Stripe` | payments | pick |
| `Tailwind CSS` | css framework | default |
| `shadcn/ui` | component library | default |
| `Deploy target` | **TBD — pick later** (Vercel, Docker/VPS, etc.) | pick |

## The sequence (never skip a step)

```
Interrogation  ->  Canonical Docs  ->  Code
```

### Phase 1 — Interrogation

Before writing any docs, make the agent tear your idea apart. Prompt:

> "Before writing any code, endlessly interrogate my idea. Assume nothing. Ask
> questions until there are no assumptions left."

Force it to surface gaps before building on a broken foundation. It should ask:

- Who is this for?
- What's the core action a user takes?
- What happens when they complete it?
- What data needs to be saved? Displayed?
- What happens on error? On success?
- Does this need a login? A database? Mobile support?

If you can't answer these, you're not ready to build. Those answers become the
raw material for the canonical docs. Example (recipe app): the user description
feeds `docs/PRD.md`, the data structure feeds `docs/BACKEND_STRUCTURE.md`, the flows feed
`docs/APP_FLOW.md`, the mobile requirement feeds `docs/FRONTEND_GUIDELINES.md`.

### Phase 2 — Canonical Docs (your knowledge base)

Write these BEFORE any code in a root-level `docs/` directory. Cross-reference them
with paths relative to that directory.

1. `docs/PRD.md` — full spec: what you're building, who it's for, in-scope and
   explicitly out-of-scope features, user stories, success criteria, non-goals.
   This is the contract; "done" is defined here.
2. `docs/APP_FLOW.md` — every page and navigation path in plain English: triggers,
   step-by-step sequences, decision points, success/error behavior, route
   inventory.
3. `docs/TECH_STACK.md` — every package/dependency/API/tool locked to EXACT versions.
   No "use React" — use `React 18.2.0, Vite 5.1.0, TypeScript 5.3.3`, and on the
   backend `FastAPI 0.110.0, SQLAlchemy 2.0.25`. Kills
   hallucinated dependencies.
4. `docs/FRONTEND_GUIDELINES.md` — the design system: fonts, exact hex codes, spacing
   scale, layout rules, component styles, responsive breakpoints, UI library.
   Every visual decision locked.
5. `docs/BACKEND_STRUCTURE.md` — DB schema (every table/column/type/relationship),
   auth logic, API contracts, storage rules, edge cases. Define the tables as
   `SQLAlchemy` models mapping to `Supabase` tables.
6. `docs/IMPLEMENTATION_PLAN.md` — step-by-step build sequence
   (`1.1 init`, `1.2 install per TECH_STACK.md`, `1.3 folder structure`,
   `2.1 build navbar per FRONTEND_GUIDELINES.md`, ...). More steps = less guessing.

Doc-generation prompt once interrogation is done:

> "Based on our interrogation, generate my canonical docs in `docs/`: PRD.md,
> APP_FLOW.md, TECH_STACK.md, FRONTEND_GUIDELINES.md, BACKEND_STRUCTURE.md,
> IMPLEMENTATION_PLAN.md. Use the conversation answers as source material. Be
> specific and exhaustive. No ambiguity."

Review, correct vagueness, add gaps, then lock them as source of truth.

### Phase 3 — Session / Persistence Files

- `AGENTS.md` / `CLAUDE.md` — the files the agents read first, automatically, every
  session. `AGENTS.md` is what OpenCode reads; `CLAUDE.md` is what Claude Code
  reads. Condensed rules from all six docs: tech stack summary, naming
  conventions, file structure, component patterns, forbidden actions. Make them
  LIVING documents: after every correction, tell the agent "Edit
  `AGENTS.md` so you don't make that mistake again." Also keep a
  `lessons.md` the agent reviews at session start and updates after every
  correction — the self-improvement loop. If you use both `OpenCode CLI` and
  `Claude Code` on the same repo, keep `AGENTS.md` and
  `CLAUDE.md` aligned to one source of truth (mirror the same rules in both).
- `progress.txt` — the session bridge. Tracks COMPLETED / IN PROGRESS / NEXT /
  KNOWN BUGS. Update after every feature. The agent reads it first on every new
  session/terminal/branch so it picks up exactly where you left off. Without it,
  every session starts from zero.

Example `AGENTS.md`:

```
Monorepo: frontend/ (React+Vite, TS), backend/ (FastAPI, Python), docker-compose.yml
TS workspace: pnpm. Python env: venv/uv.
Frontend components go in frontend/src/components/
Backend routes go in backend/app/api/
Never use inline styles. Always use Tailwind CSS.
Design tokens: primary blue #3B82F6, background #F9FAFB
Mobile-first responsive approach
Backend talks to Supabase via SQLAlchemy models only — no raw SQL in routes.
Reference docs: docs/PRD.md, docs/APP_FLOW.md, docs/TECH_STACK.md, docs/FRONTEND_GUIDELINES.md, docs/BACKEND_STRUCTURE.md, docs/IMPLEMENTATION_PLAN.md
Read progress.txt at the start of every session. Update progress.txt after completing any feature.
Review lessons.md at session start. Update it after every correction.
```

`CLAUDE.md` mirrors `AGENTS.md` so both agents share the same rules.

Example `progress.txt`:

```
COMPLETED:
- User auth via Supabase (login, signup, Google OAuth)
- Dashboard layout with sidebar nav
- Products API (GET /api/products)
IN PROGRESS:
- Product detail page (/products/[id])
NEXT:
- Shopping cart
- Checkout with Stripe
KNOWN BUGS:
- Mobile nav doesn't close after clicking a link
```

## Vocabulary cheat sheet (use it in prompts)

- **UI vs UX** — UI = visual layer (colors, fonts, spacing). UX = how it feels
  (intuitive? stuck?). "Make it look better" = UI. "Make it easier to use" = UX.
- **Components** — reusable interface pieces (button, navbar, card). Tell the
  agent the exact component list so it doesn't build one giant mess.
- **Layout** — boxes in boxes. Header/nav, main, optional sidebar, footer.
  Specify: "sidebar left 250px fixed, main takes the rest."
- **State** — data that changes (menu open? logged in? cart items? loading?).
  "On click, set modal state to open; on outside click, set to closed."
- **Styling** — CSS controls appearance; `Tailwind CSS` is the class
  shortcut. Design tokens = consistent reusable values. Lock palette/spacing/
  font stack/radius/shadow/timing in `FRONTEND_GUIDELINES.md`.
- **Responsive** — works on all sizes. Mobile-first: design smallest first.
  Breakpoints: mobile 0–640, tablet 640–1024, desktop 1024+. Document nav/grid/
  font scaling rules.
- **Pages vs Routes** — page = what's seen; route = the URL (`/`, `/about`,
  `/products/[id]` dynamic). Give the full route list up front.
- **Frontend vs Backend** — frontend = browser UI (React+Vite in `frontend/`);
  backend = db/accounts/server logic (FastAPI in `backend/`). State which you
  need before the agent builds.
- **APIs** — how systems talk. GET/POST/PUT/DELETE. The frontend calls the
  FastAPI backend over REST: "On load, GET /api/products and render in a grid."
- **Databases** — permanent storage (else everything resets on refresh).
  `Supabase` is the backend's store. Need one if users
  create accounts / save content / data grows.
- **Auth** — login/logout. Don't roll your own; use `Supabase`
  Auth from the FastAPI backend.
- **File types** — `.html` structure, `.css` style, `.js`/`.jsx`/`.ts`/`.tsx`
  frontend logic, `.py` backend logic, `.json` data, `.md` docs, `.env` secrets
  (NEVER commit/share/screenshot), `.gitignore`.
- **Folder structure** — messy projects confuse the agent. Standard monorepo:

```
my-app/
├── frontend/          → React + Vite (TS)
│   ├── src/
│   │   ├── components/   → reusable UI pieces
│   │   ├── lib/          → utilities, helpers
│   │   ├── styles/       → CSS files
│   │   └── pages/        → page-level views
│   └── package.json
├── backend/           → FastAPI (Python)
│   ├── app/
│   │   ├── api/          → routes/endpoints
│   │   ├── models/       → SQLAlchemy models
│   │   ├── schemas/      → Pydantic schemas
│   │   └── services/     → business logic
│   ├── .venv/            → Python env (never share)
│   └── pyproject.toml
├── docker-compose.yml  → services (db, backend, frontend)
├── .env                → secrets (never share)
├── AGENTS.md  CLAUDE.md  → agent rules and context
├── progress.txt        → session tracking
├── docs/                  → canonical product, design, data, and implementation docs
│   ├── PRD.md
│   ├── APP_FLOW.md
│   ├── TECH_STACK.md
│   ├── FRONTEND_GUIDELINES.md
│   ├── BACKEND_STRUCTURE.md
│   └── IMPLEMENTATION_PLAN.md
├── package.json  README.md
```

Tell the agent where files go: "Create Button in `frontend/src/components/Button.tsx`."
Tell the agent where documentation goes: "Update `docs/APP_FLOW.md`, not a root-level copy."
Never commit `.venv/` — add it to `.gitignore`.

## Tool workflow (match tool to phase)

- `OpenCode CLI` — main build agent. Modes: Ask (read-only explore) -> Plan
  (architect) -> Agent (build) -> Debug (instrumented bug loop).
- `Claude Code` — parallel build / review agent. Reads `CLAUDE.md` for rules;
  good for a second pass on the same repo or running tasks while OpenCode builds.
- `Codex` — after architecture is built: find bugs, review, run tests
  to green. Can run multiple tasks in parallel.
- `GitHub` — version control, non-negotiable.
- `Docker` — `docker-compose.yml` to run db/backend/frontend together.
- `Deploy target` — TBD. When chosen, add its deploy/ci steps here.

Screenshot references beat written design descriptions: feed a reference UI
directly to `OpenCode CLI` or `Claude Code` with "match this layout."

## Build loop

1. Agent reads `AGENTS.md`/`CLAUDE.md`, `progress.txt`, `lessons.md` first.
2. Architect with Ask/Plan (or `Claude Code`).
3. Implement in small pieces, one feature at a time, referencing canonical docs.
4. Give specific, vocabulary-rich prompts ("Build step 4.2 of
   docs/IMPLEMENTATION_PLAN.md; login flow per docs/APP_FLOW.md §3; auth per
   docs/BACKEND_STRUCTURE.md §5; style per docs/FRONTEND_GUIDELINES.md").
5. Commit to `GitHub` after each working feature; update `progress.txt`.
6. After every correction: update `AGENTS.md` and `lessons.md`.
7. Use `Codex` to debug/review/finalize once architecture is in place.
8. Test on mobile regularly.

## Debugging loop

Read the error (file:line is in the trace). Understand the claim. Check the
obvious (typos, imports, names). Give the agent error + code + what you
expected. Iterate: agent code -> you try -> breaks -> paste error -> fix ->
repeat. For stubborn bugs, use `OpenCode CLI` Debug mode or `Codex`
(which reads the whole repo and traces cross-file root causes).

## Before shipping

- Works on mobile (open on a real phone)?
- Error states and empty states handled?
- Loading states for slow networks?
- Can't break it by clicking fast?
- Secrets hidden from browser dev tools?
- Main user flow works end-to-end?

## Scope / when to stop

Done when: core feature works, users complete the main action, common paths
don't break, it's deployed. Not done when chasing "perfect" or every imagined
feature. Ship the simple version, get feedback, iterate.

## Security basics

Never expose API keys in frontend code. Validate all inputs on the backend.
Use HTTPS (on your deploy host). Keep deps updated. Use auth services,
don't roll your own. Keep `.venv/` and `.env` out of git.

## Cost awareness

Free tiers are generous (Supabase). AI API calls and storage cost at scale.
Start free; don't architect for millions on day one.

## Complete checklist

**Before building**
- [ ] Run interrogation prompt; answer every question
- [ ] Generate the six canonical docs; review and lock
- [ ] Write `AGENTS.md`/`CLAUDE.md` + `lessons.md` self-improvement loop
- [ ] Create `progress.txt` with starting state
- [ ] Gather UI screenshots for reference
- [ ] Init git, push to `GitHub`

**While building**
- [ ] Agent reads `AGENTS.md`/`CLAUDE.md`/`progress.txt`/`lessons.md` every session
- [ ] Architect with Ask/Plan before coding
- [ ] Implement one feature at a time, referencing canonical docs
- [ ] Screenshot references for UI work
- [ ] Commit after each working feature; update `progress.txt`
- [ ] Update `AGENTS.md`/`CLAUDE.md`/`lessons.md` after every correction
- [ ] `Codex` to debug/review/finalize
- [ ] Test on mobile

**Before shipping**
- [ ] Mobile, error/empty states, hidden secrets, end-to-end flow, perf

**After shipping**
- [ ] Update docs to reflect what was built
- [ ] Keep deps/permissions updated
- [ ] Iterate on real feedback
- [ ] Keep `progress.txt`/`lessons.md` current; turn repeats into skills
