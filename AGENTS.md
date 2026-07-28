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
- Remove temporary implementation notes from docs or `AGENTS.md` once the implemented code makes them obsolete.
- Do not let planning-only instructions become permanent rules unless they still guide future work.

## Decision Points

- When implementation reaches an undecided product, API, model, UX, security, or infrastructure choice, do not silently choose unless the choice is low-risk and already implied by existing docs.
- Present 2-3 concrete options with the implementation impact and tradeoff of each option.
- Recommend one option when there is a clear engineering reason, but wait for the user's selection before implementing the decision.
- After the user chooses, record the decision in the relevant doc only if it will guide future work.
- If a decision note becomes unnecessary after implementation, remove or collapse it instead of leaving stale planning text.

## Frontend Work

- Frontend implementation lives in `../traceback-client`, even when the user gives the instruction from this backend repository session.
- Before starting frontend work, read `../traceback-client/AGENTS.md` and follow the client-side rules there.
- Check the branch and working tree in both repositories when a task crosses backend and frontend boundaries.
- Do not create frontend files inside this backend repository unless the user explicitly asks for backend-served assets.

## Model Documentation

- Models are the most important implementation artifact; after model work, document the purpose of each model and column in a readable artifact.
- The artifact can be Markdown or HTML, but it must be easy to scan in a new session.
- Each column purpose must be justified by the minimal MVP scope or an explicit requirement.
- If a column is only for future expansion and not required now, do not add it; record the deferred idea in the relevant docs instead.
- Keep the model-purpose document aligned with the actual migrations before stopping work.
