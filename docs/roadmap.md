# Roadmap

This roadmap describes the likely build order for Aide. It should stay practical and change as the product becomes clearer.

## Phase 1: Useful Local Prototype

Goal: make Aide useful for basic daily capture and review.

- Keep the FastAPI backend running reliably through Docker Compose
- Support CalDAV task listing and completion outcome capture
- Use CalDAV VTODO as the To-Do source of truth
- Support not-to-dos as CalDAV journal-backed boundary records
- Support thought capture and review
- Support activity/life log capture for things that happened outside the task list
- Support structured activity logs for a lightweight PDCA loop
- Support SOP-shaped review drafts for PDCA, STOW, SCAQ, SMART, AIDA, 5W2H, and debate prompts
- Support daily briefing
- Support lightweight money records
- Add basic README and project docs

Current status: mostly implemented.

## Phase 2: Backend Shape and Safety

Goal: make the backend easier to maintain before adding larger features.

- Split `backend/app/main.py` into focused modules
- Add database migration support
- Add a small test suite
- Add stricter validation for thought, activity, and money inputs
- Add update/delete endpoints where useful outside task/calendar authoring
- Add pagination or date filtering for growing lists
- Add filters for activity logs by date and category
- Add filters for activity logs by SOP model, next action, and low-energy records
- Decide whether authentication is needed for the local deployment model
- Expand the CalDAV adapter to cover recurrence reading, calendar sync tokens, and conflict handling

## Phase 3: Frontend

Goal: create the main user experience.

- Build a web-first interface
- Make the daily briefing the default screen
- Add fast capture for thoughts, activity logs, outcomes, and money records
- Add mobile-friendly layouts
- Add CalDAV task completion/outcome and review workflows
- Add simple finance views

## Phase 4: AI Assistance

Goal: add AI where it improves daily use.

- Generate daily summaries
- Summarize recent thoughts
- Suggest follow-up tasks from thoughts
- Identify stale tasks or recurring themes
- Debate with the user from recent thoughts, actions, PDCA records, money patterns, and long-term freedom goals
- Generate concise SCAQ reports and SMART goal drafts from recent behavior
- Keep AI output reviewable and editable

## Phase 5: Personal Memory and RAG

Goal: let Aide retrieve relevant personal context.

- Add embedding generation
- Add Qdrant or another vector store
- Store retrievable memory records
- Link memories back to source tasks, thoughts, and summaries
- Add memory inspection and correction workflows

## Phase 6: Hardening

Goal: make Aide dependable for long-term use.

- Add backups
- Improve observability
- Add import/export tools
- Add privacy and data retention controls
- Improve deployment documentation
- Add production-oriented configuration
