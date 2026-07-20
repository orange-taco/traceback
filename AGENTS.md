# Codex Working Rules

This repository implements the TRACEBACK commerce backend.

## Session Start

1. Read `docs/simple-build-guide.md` first.
2. Read the resume checkpoint in `docs/build-plan.md`.
3. Use only the relevant detailed docs for the current slice.
4. Verify the current branch and working tree before changing files.
5. Do not assume a phase is complete from conversation context alone.

## Phase Checks

- Treat `docs/simple-build-guide.md` and `docs/build-plan.md` as the phase scope authority.
- Before starting a new phase, compare the code, tests, and checkpoint against that phase's completion criteria.
- Start Phase 1 only after Phase 0 completion criteria are satisfied and recorded.
- If Phase 0 is incomplete, continue Phase 0 work instead of starting Catalog work.
- Keep the resume checkpoint aligned with the real code state before stopping work.
- After finishing development work, update `docs/current/README.md` so a new session can see the current state, next action, completed scope, and remaining validation without reading the full docs set.

## Branching

- Create task branches from `development`.
- Use branch names that make the phase obvious, such as `phase-0-foundation` or `phase-1-catalog`.
- Do not do feature work directly on `main` or `development`.
- Before switching or creating branches, check for existing user changes and preserve them.

## Change Scope

- Keep each slice independently testable and PR-sized.
- Follow the 30-file slice limit unless the user explicitly approves an exception.
- Update only the docs affected by the code or phase decision.
- If implementation reveals a design issue, record it in `docs/build-plan.md` before treating the work as complete.

## Model Documentation

- Models are the most important implementation artifact; after model work, document the purpose of each model and column in a readable artifact.
- The artifact can be Markdown or HTML, but it must be easy to scan in a new session.
- Each column purpose must be justified by the minimal MVP scope or an explicit requirement.
- If a column is only for future expansion and not required now, do not add it; record the deferred idea in the relevant docs instead.
- Keep the model-purpose document aligned with the actual migrations before stopping work.
