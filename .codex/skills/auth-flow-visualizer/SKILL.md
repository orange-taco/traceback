---
name: auth-flow-visualizer
description: "Create or update visual HTML guides for TRACEBACK system flows, AWS deployment setup, API contracts, and lifecycle states."
---

# TRACEBACK System Visualizer

Use this skill when documenting a TRACEBACK subsystem as a visual, reusable HTML
mini-site. It supports authentication, catalog/product management, commerce, and
future domains without reducing the explanation to a table or a prose-only page.

## Workflow

- Create or update HTML artifacts under `docs/artifact/` in the repository.
  Use a descriptive filename such as `auth-flow.html` or `aws-ssm-access-guide.html`.
  Do not place generated artifacts inside `.codex/skills/`; that directory contains
  reusable skill instructions and resources. If an artifact is added or moved, update
  the relevant checkpoint or documentation links so readers can find it.
- Keep diagrams and interaction code in the HTML. Screenshots may live in
  `docs/artifact/images/`; verify their relative paths and include them in PDF
  output. Use inline `data:` images when a single portable HTML file is needed,
  accepting the larger HTML size and harder image replacement.
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
- Provide a visible PDF save action. Its print view must include content hidden
  behind tabs or closed details, preserve diagrams and screenshots, and omit
  navigation controls; restore the interactive state after printing.

## Accuracy checks

- Verify every node, edge, state, and transition against the current source before rendering.
- Include endpoint, source ownership, and the relevant source path when that removes ambiguity.
- Do not invent framework behavior, business rules, or future domain behavior. Mark
  planned sections as planned instead of filling them with assumptions.
- Keep detailed source paths in a compact reference area or accessible text, while
  keeping the diagram readable.

## Required artifact standard

Apply this standard whenever creating or updating an HTML artifact
under `docs/artifact/`. Do not consider the artifact complete until a new reader
can answer these questions from the page itself:

1. What is the end-to-end flow? Show it first with a labeled visual and explain
   the arrows, participants, and boundaries in plain language.
2. What do the underlying terms mean, what practical options exist, and what
   changes when each option is chosen? Present the general model before the
   TRACEBACK example. If the subject has no real alternative, say why.
3. Which option does TRACEBACK use, and why? Tie the decision to the actual
   code, configuration, and operational constraints.
4. Where is it implemented? Place relevant source/configuration excerpts next
   to their explanation, with a link to the current file. Explain who consumes
   each value and at what stage; do not leave a code dump without a purpose.
5. What works now, what is configured but untested, and what is still pending?
   Label these states explicitly, including security and deployment boundaries.

Keep the visual and its detailed explanation close enough to read together.
Use screenshots only when they add verifiable setup context; diagrams may explain
the general path. Verify the source and observed setup before asserting a current
state. An attractive page that omits a required answer is unfinished.

## AWS initial setup learning set

When editing the five AWS guides in `docs/artifact/`, maintain them as one learning
path: `traceback-system-guide.html` for the whole system and CI/CD map, then
`1-aws-ssm-ssh-learning-guide.html` for access and identities,
`2-dev-server-first-deployment.html` for deployment and infrastructure,
`3-development-ip-domain-guide.html` for IP and domain choices, and
`4-dns-resolution-map.html` for DNS resolution. Link forward and back where a
reader needs the companion explanation or code; do not make readers guess which
document owns a topic.

- Start each topic with a visual path that shows what talks to what and why.
  Explain general networking or AWS terms before showing TRACEBACK-specific IDs.
- Show setup dependencies in the order a first-time deployer must complete them.
  Place the status of each TRACEBACK step on that flow, including the first
  missing step that blocks a live request. Explain DNS, inbound routing, TLS
  certificate issuance/renewal, reverse proxy, runtime environment variables,
  database access, deployment, and frontend verification at their actual points
  in the path; do not collect omissions only in a final checklist.
- Define even basic terms at first use or in a nearby beginner glossary, while
  keeping general networking terms distinct from AWS product names.
- Next to the relevant visual, compare practical setup options, their tradeoffs,
  TRACEBACK's choice, and the reason for it. Put applicable configuration or
  source excerpts beside their explanation, with links to the current files.
  Explain who reads each setting and when, especially for environment files.
- Give enough console or terminal steps for a new AWS user to reproduce the
  setup. Distinguish a general procedure from values observed in this account.
- Mark each important setting as **configured and verified**, **configured but
  not yet tested**, or **still to do**. Show the current inbound, outbound,
  route-table, subnet, IAM, DNS, and runtime state where relevant. Name remaining
  checks such as NACL rules, narrow egress, HTTPS, and EC2-to-RDS connectivity
  instead of implying the initial deployment is complete.
- Recheck live-state claims or date them, and compare code excerpts with the
  current repository. Review screenshots before publishing: record visible
  account/resource identifiers and remove secrets or personal data. Show console
  screenshots large enough to read or give a direct full-resolution link; do not
  shrink dense settings pages into a two-column thumbnail grid.
