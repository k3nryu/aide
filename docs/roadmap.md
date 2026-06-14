# Roadmap

This roadmap describes the likely build order for Aide. It should stay practical and change as the product becomes clearer.

## Phase 1: Useful Local Prototype

Goal: make Aide useful for basic daily capture and review.

- Keep the FastAPI backend running reliably through Docker Compose
- Support task creation, listing, and completion
- Support CalDAV VTODO as the To-Do storage backend when configured
- Support not-to-dos as first-class task records
- Support thought capture and review
- Support activity/life log capture for things that happened outside the task list
- Support structured activity logs for a lightweight PDCA loop
- Support daily briefing
- Support lightweight money records
- Add basic README and project docs

Current status: mostly implemented.

## Phase 2: Backend Shape and Safety

Goal: make the backend easier to maintain before adding larger features.

- Split `backend/app/main.py` into focused modules
- Add database migration support
- Add a small test suite
- Add stricter validation for task, thought, and money inputs
- Add update/delete endpoints where useful
- Add pagination or date filtering for growing lists
- Add filters for activity logs by date and category
- Add filters for activity logs by SOP model, next action, and low-energy records
- Decide whether authentication is needed for the local deployment model
- Expand the CalDAV adapter to cover recurrence, calendar sync tokens, and conflict handling

## Phase 3: Frontend

Goal: create the main user experience.

- Build a web-first interface
- Make the daily briefing the default screen
- Add fast capture for tasks, not-to-dos, thoughts, and money records
- Add mobile-friendly layouts
- Add task completion and review workflows
- Add simple finance views

## Phase 4: AI Assistance

Goal: add AI where it improves daily use.

- Generate daily summaries
- Summarize recent thoughts
- Suggest follow-up tasks from thoughts
- Identify stale tasks or recurring themes
- Debate with the user from recent thoughts, actions, and PDCA records
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
