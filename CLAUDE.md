# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude Instructions

## Project Intent
Slipstream is an early-stage prototype for analyzing cycling performance data from Strava.
Current scope is Phase 0: authentication and data ingestion only.

Do not assume analytics, Spark, Flink, or large-scale processing yet.

## Non-Goals (for now)
- No multi-user support
- No persistent credential storage
- No database integration unless explicitly requested
- No premature optimization or streaming frameworks

## Architecture Rules
- Credentials must be stateless and stored only in environment variables
- Token refresh may occur in-memory only and must not write to disk
- Configuration must flow through a single settings object
- Prefer explicit data flow over abstractions

## Tech Stack
- Python 3.11+
- Poetry
- Pydantic v2 + pydantic-settings
- Click for CLI
- requests for HTTP

## Claude Behavior
- Ask before introducing new infrastructure or storage layers
- Prefer small, incremental changes over large rewrites
- When proposing design changes, explain tradeoffs
