# Changelog

All notable changes to SoftGNN Advisor will be documented here.

The format loosely follows [Keep a Changelog](https://keepachangelog.com/), and this project uses alpha milestone versions during early development.

---

## v0.1.0-alpha — Developer Preview

### Added

- Code/test graph foundation for PR impact analysis.
- Runtime test mapping from pytest execution to source functions.
- PR scan workflow for impacted targets and missing runtime coverage.
- Semantic pytest generation for selected targets.
- Transactional generated-test patching with rollback.
- Generated block markers for safe rewrites.
- Pytest verification loop.
- Bounded repair loop for generated tests.
- Runtime coverage refresh after successful generation.
- PR scan confirmation after runtime refresh.
- LLM provider abstraction.
- Native Gemini provider.
- OpenAI-compatible provider.
- Template fallback provider.
- Structured JSON parsing and validation for LLM-generated tests.
- Safety validation for generated code patterns and test paths.
- CLI flags for generation strategy, provider config, repair, runtime refresh, and rollback policy.
- Internal tests for provider config and LLM schema validation.

### Verified

- Gemini generated semantic tests for `FUNC:is_edge_index_sorted`.
- Patch workflow produced `6 passed` on the demo repo.
- Runtime refresh persisted `336` runtime edges.
- PR scan confirmation completed successfully.

### Notes

- This is an alpha/developer preview.
- Generated tests should be reviewed before commit.
- Production-code fixes are not enabled in v0.1.
- Multi-agent testing swarm is roadmap, not v0.1 scope.
