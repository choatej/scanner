# Agent Entitlements

This document tracks the capabilities and responsibilities granted to the GPT-5 Codex agent collaborating on this project.

## Agent Identity
- **Name:** GPT-5 Codex
- **Context:** Interactive coding agent assisting with the Scanner project setup and implementation.

## Current Entitlements
- **Read/Inspect:** May read any files in the repository to understand project state and requirements.
- **Modify/Create:** May add or modify project files when requested by the user or required for assigned tasks.
- **Tooling:** May execute development tooling via project scripts (e.g., linting, testing) once available.
- **Environment:** May create and manage a local Python virtual environment under `.venv/`.
- **Documentation:** May create and update documentation under `docs/` and this `AGENTS.md` file.
- **Conversation Logging:** May summarize the assistant/user collaboration within the documentation space as requested.

## Constraints
- Must stage changes for commit but should not create commits unless explicitly instructed.
- Must not remove or override user-created content without confirmation.
- Must adhere to repository policies and security guidelines stated in `README.md` and other documentation.
- Must avoid introducing secrets, credentials, or unsafe code.

## Change Log
- **2025-11-08:** Initial entitlements recorded while bootstrapping project scaffolding.


