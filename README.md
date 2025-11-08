# Scanner - A tool for scanning and cataloging videos on video sites.

## Features
- Gathers video meteadata from multiple sources
  - web pages
    - handles pagination
    - Can process pages that require rendering (using selenium drivers)
    - page types:
      - search results
      - category or tag matches
      - actor pages
  - local files (json, csv, html, structured records)
  - other scanner instances
- Collects high-level metadata about videos (when available)
  - Title
  - Decription
  - Length (can read string formats, stores in seconds)
  - Tags
  - Categories
  - Actors
  - Source Site
  - Extra Info
- High-level consumer API for querying and seraching
- Extensible to add new metadata fields, data sources, web page formats, backends.

## Design
Losely coupled and modular, with strong API borders between
- Processing Engine (the glue of the different parts)
- Data source types
- Data source reading (eg. different html page layouts)
- backends (database, noSQL, files)
- Query API output formats
- Per-source config params
  - rate limits
  - timeouts
  - process count
- Onetime ingestion run vs. persistent service
- startup CLI params, config file, env vars to determine behavior
- Query API is a separate app from the backend.  Python API or stateful REPL.
- User added extensions are auto loaded when stored in a well-known location or pointed to through config.
- Structured logging with configurable destination. Default based on deployment context - system journal, stdout, etcx.



## Implementation
- Stores data in a relational database for quick lookups
- Suports full-text indexing across all text fields
- Managed database schema migrations (forward-only)
- API in both REST and GraphQL

## Tech Stack
- Python 3.12+
- Postgres 17
- Whatever else makes sense

## Developing

Code should have unit tests where it makes sense. There is no requirement for 100% coverage. Tests should cover the important and high-risk functionality.

Any credentials persisted need to be secure - either read from a secure vault-like system or encrypted at rest.


### Development Tools
- uv
- pytest
- mypy
- import linter
- black
- bandit
- flake8


# Continuous Integration
- GitHub pull request creation and updates will trigger a run of all static analysis and tests. It will also create a docker container and push it to ghcr.io.
- Merges to main will trigger a release creating all deployment artifacts.
- 

## Deployment
Scripts are provided to run Scanner
- Directly from code
- as a systemd service
- As a package (debian, arch, appimage)
- As a docker container (database and other components not included)
- As a GCP compute instance or cloud run
- Python wheel for the consumer API


## Legal
This software is release under the MIT License.  See [LICENSE](LICENSE) for the terms and conditions.
