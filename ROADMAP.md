# Roadmap

SoftGNN Advisor's long-term direction is:

```text
Graph-guided, runtime-proven, LLM-assisted PR testing.
```

Multi-agent workflows are planned, but the core differentiator is graph/runtime proof.

---

## v0.1 — Single-Agent LLM-Assisted Test Generation

Status: **implemented / alpha**

Includes:

```text
code graph extraction
runtime test mapping
PR impact scan
semantic pytest generation
Gemini provider
OpenAI-compatible provider
structured JSON validation
transactional patching
pytest verification
LLM repair hook
runtime refresh
PR scan confirmation
```

---

## M4 — Runtime-Proven Test Generation

Goal:

```text
generated tests must prove they execute the intended target
```

Planned features:

```text
target-level runtime proof gate
reject passing tests that do not hit target
coverage delta before/after
proof report per generated test
quality gate against smoke-only tests
```

---

## M5 — Graph Impact Report / Dashboard

Goal:

```text
make PR impact and generated test proof visible
```

Planned outputs:

```text
Markdown report
HTML report
Mermaid graph
before/after coverage table
risk heatmap
runtime proof section
```

---

## M6 — Learned Test Prioritization / GNN Ranking

Goal:

```text
use the code/test graph to rank tests and generation targets
```

Planned features:

```text
rank impacted functions by risk
predict related tests for a PR
rank missing tests to generate first
learn from static + runtime graph edges
```

---

## M7 — Multi-Agent Quality Swarm

Goal:

```text
improve generated test quality using role-specialized agents
```

Planned roles:

```text
ContextAgent
WriterAgent
ReviewerAgent
RepairAgent
CoverageAgent
Deterministic QualityGate
```

Principle:

```text
agents propose
validators enforce safety
pytest verifies correctness
runtime graph proves target execution
```

---

## M8 — Large-Scale Repo Automation

Goal:

```text
scale from one target to many targets across a repo
```

Planned features:

```text
batch target selection
LLM rate limiting
cost budget
checkpoint/resume
batch rollback
parallel pytest shards
```

---

## M9 — Controlled Production-Code Fixes

Goal:

```text
optionally fix production bugs revealed by generated tests
```

Safety model:

```text
disabled by default
requires explicit flag
requires user approval
shows diff before applying
rollback on failure
```

---

## M10 — Provider/Auth/Enterprise Hardening

Planned features:

```text
Vertex AI auth
service accounts
Azure OpenAI
Anthropic
per-agent model routing
secret redaction
audit logs
retry/rate-limit handling
```

---

## M11 — Local Model Management / Fine-Tuning

Planned features:

```text
Ollama/vLLM setup helper
local model health checks
model quality benchmark
successful generation/repair dataset
fine-tuning pipeline
```
