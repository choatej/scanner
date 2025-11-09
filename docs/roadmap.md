# Roadmap

This roadmap outlines the planned feature progression for Scanner. Each iteration builds on the existing abstractions (source adapters → normalization → persistence → APIs) to expand coverage and capabilities.

## Milestone 1 — Web Ingestion Pipeline
- ✅ Implement HTML/scraper-based source adapters (static pages, optional Selenium rendering).
- ✅ Add configuration management foundation (TOML defaults, CLI/env overrides).
- ✅ Introduce asynchronous pipeline engine and CLI integration.
- Add configuration for source-specific parameters (rate limits, pagination).
- Provide basic error handling, retry logic, and structured logging extensions.

## Milestone 2 — Relational Persistence
- ✅ Introduce PostgreSQL 17 persistence backend with initial schema (sites, videos).
- Add schema migration tooling and seed data support.
- Provide basic querying utilities for testing/validation.

## Milestone 3 — API Layer
- Expose video metadata via REST and/or GraphQL endpoints.
- Add authentication/authorization scaffolding.
- Implement filtering/search endpoints (basic queries without full-text indexing initially).

## Milestone 4 — Advanced Features
- Integrate full-text search capabilities (e.g., Postgres `tsvector` or external search service).
- Support importing/exporting data to other Scanner instances.
- Add plugin/extension loading mechanism and documentation.

## Milestone 5 — Deployment Targets
- Deliver Docker image(s) with production configuration.
- Provide scripts/templates for systemd, package distribution, and cloud environments (e.g., GCP).
- Harden CI/CD with release tagging, artifact publication, and security scanning.

As milestones are completed, the roadmap will be revisited and expanded based on project needs. Contributions should align with the modular architecture and maintain the separation between domain logic, infrastructure, and API layers.

