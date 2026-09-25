---
name: auth-flow-visualizer
description: "Create artifact-style interactive visual documentation for TRACEBACK system architecture, domain workflows, API contracts, and lifecycle state transitions."
---

# TRACEBACK System Visualizer

Use this skill when documenting a TRACEBACK subsystem as a visual, reusable HTML
mini-site. It supports authentication, catalog/product management, commerce, and
future domains without reducing the explanation to a table or a prose-only page.

## Workflow

- Create or update a self-contained HTML artifact in a durable task-owned location.
- Treat it as a small documentation site: keep a shared shell, domain navigation,
  overview, and one visual section per documented subsystem. Preserve existing
  sections when adding a new domain.
- Make the explanation visual-first with SVG or CSS diagrams, lanes, arrows,
  highlights, and state transitions. Do not turn the main explanation into tables or
  prose cards.
- Add interaction when it clarifies behavior, such as domain tabs, branch selectors,
  step controls, focus highlighting, or expand/collapse details.
- Use restrained animation to communicate direction or state change, respect
  `prefers-reduced-motion`, and keep the initial frame understandable without input.
- Label ownership on every meaningful node: framework/library, TRACEBACK custom code,
  frontend, database, or external service. Show the actual method, endpoint, event,
  or state transition when known, and briefly explain what the node does.
- Mark short-circuit conditions, transaction boundaries, retries, and failure paths
  explicitly. Do not imply a callback or library hook runs unless the source proves it.
- Use semantic controls, visible labels, `aria-live` where state changes, text
  alternatives, keyboard operation, and responsive layout down to narrow widths.

## Accuracy checks

- Verify every node, edge, state, and transition against the current source before rendering.
- Include endpoint, source ownership, and the relevant source path when that removes ambiguity.
- Do not invent framework behavior, business rules, or future domain behavior. Mark
  planned sections as planned instead of filling them with assumptions.
- Keep detailed source paths in a compact reference area or accessible text, while
  keeping the diagram readable.
