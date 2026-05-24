# Future Milestones from M4 Onward

This document preserves the post-v0.1 roadmap so it is easy to resume later.

Core positioning:

```text
SoftGNN = Graph-guided, runtime-proven, LLM-assisted PR testing.
Know what changed. Know what tests hit it. Generate what is missing.
```

The main differentiator is **not** multi-agent orchestration by itself. The moat is:

```text
code graph + runtime test graph + PR impact + LLM test generation + proof loop
```

---

## Current Baseline Before M4

Implemented by v0.1 alpha:

```text
M1  AST/code graph extraction
M2  Runtime coverage mapping
M2B Runtime edge persistence
M3  Semantic test generation
M3.1 Auto verify + rollback + runtime refresh + PR scan confirmation
M3.2 Gemini/OpenAI-compatible LLM generation + repair
```

Verified demo:

```text
Target: FUNC:is_edge_index_sorted
Provider: Gemini
pytest: 6 passed
runtime edges: 336
persisted: True
PR scan confirmation: pass
```

---

# M4 — Runtime-Proven Test Generation

## Goal

Upgrade acceptance criteria from:

```text
pytest pass
```

to:

```text
pytest pass + generated test proves it executes the intended target
```

## Core Idea

Every generated test should produce runtime evidence:

```text
TestFunction -> executes_runtime -> TargetFunction
```

If a generated test passes pytest but does not execute the target, SoftGNN should reject, repair, or rollback it.

## Planned Features

```text
--require-runtime-proof flag
target-level runtime verification
candidate must execute target
coverage delta before/after
proof report per generated test
quality gate against callable/hasattr smoke tests
rollback when runtime proof fails
```

## Example CLI

```powershell
python softgnn.py generate-tests `
  --project social-link `
  --repo-path "C:\path\to\repo" `
  --target-id "FUNC:is_edge_index_sorted" `
  --source-file "scripts/train_model.py" `
  --mode patch `
  --generation-strategy auto `
  --require-runtime-proof `
  --verify
```

## Expected Output

```text
Pytest: PASS
Runtime proof: PASS
Generated test: test_is_edge_index_sorted
Executes target: FUNC:is_edge_index_sorted
Runtime edges gained: +N
Decision: ACCEPT
```

## Why It Matters

Many tools can generate tests that pass. SoftGNN should prove that generated tests actually hit impacted code.

---

# M5 — Graph Impact Report / Dashboard

## Goal

Make SoftGNN's graph/runtime intelligence visible and easy to demo.

## Core Idea

After PR scan or test generation, output a report showing:

```text
changed nodes
impacted nodes
existing related tests
missing runtime coverage
generated tests
runtime proof edges
risk score
before/after status
```

## Planned Outputs

```text
Markdown report
HTML report
Mermaid graph
before/after coverage table
risk heatmap
runtime proof section
```

## Example Report Summary

```text
PR Impact Summary

Changed:
- scripts/train_model.py::is_edge_index_sorted

Generated:
- tests/test_train_model.py::test_is_edge_index_sorted

Proof:
- test_is_edge_index_sorted executes is_edge_index_sorted

Status:
- Missing runtime coverage resolved
```

## Why It Matters

A visual report makes the repo easier to understand, demo, and share. This is important for GitHub adoption.

---

# M6 — Learned GNN Ranking, CI Subset Selection, and Apply-Run Dataset

## Goal

Make the `GNN` part of SoftGNN research-relevant by learning from graph structure, runtime evidence, and real apply-run history to rank targets, select CI subsets, and improve test generation over time.

## Core Idea

Use graph structure and runtime edges to rank:

```text
which tests are related to a PR
which functions are risky
which missing tests should be generated first
which tests should be prioritized in CI
```

And learn from historical apply-run outcomes:

```text
Code graph + runtime test graph + PR changes + apply-run outcomes
  -> learned ranker
  -> better target selection
  -> better CI subset selection
  -> lower LLM cost
  -> stronger AI/research differentiation
```

## Apply-Run Dataset

Persist every generation/apply attempt as structured training data:

```text
target_id
source_file
test_file
selected strategy
generated test names
pytest target
pytest return code
pass/fail/rollback status
rollback scope
repair attempts
error type
pytest output tail
runtime proof before/after
coverage delta
side-effect skip reason
replan iteration
final accepted/rejected decision
```

This dataset becomes the feedback loop for learned ranking.

## Graph Inputs

Train an optional GNN ranker over SoftGNN's heterogeneous graph:

```text
Nodes:
- File
- Function
- Class
- TestFunction
- Commit
- Developer
- ApplyRun
- PytestFailure

Edges:
- imports
- calls
- defines
- covers_static
- executes_runtime
- changed_in_pr
- generated_for
- failed_with
- repaired_by
- rolled_back
- accepted
```

Predictions:

```text
P(target should be tested)
P(generated test will pass)
P(target is side-effect risky)
P(test is relevant to PR)
P(existing test will fail)
```

## CI Test Subset Selection

Use the learned ranker to recommend a small, high-value subset of tests for a PR:

```text
changed nodes -> candidate related tests -> ranked subset -> CI shard
```

Example output:

```text
Recommended CI subset for this PR:
1. tests/test_ingestion.py::test_run_ingestion_pipeline  score=0.94
2. tests/test_structural_db.py::test_upsert_section      score=0.82
3. tests/test_graph_builder.py::test_route_start         score=0.71

Estimated subset size: 3 / 248 tests
Reason: high graph proximity + historical runtime relevance + apply-run outcomes
```

## Planned Commands

```powershell
softgnn collect-runs --project social-link
softgnn train-ranker --project social-link --model gnn
softgnn rank-targets --project social-link --base main --head HEAD --ranker gnn
softgnn select-tests --project social-link --base main --head HEAD --budget 20 --ranker gnn
```

## Why It Matters

This separates SoftGNN from generic LLM test generators. The system becomes graph-intelligent and adaptive:

```text
Generic LLM tools generate tests from prompts.
SoftGNN learns from graph structure, runtime proof, and historical apply outcomes.
```

The learned ranker makes the system improve over time:

```text
more usage -> better ranking -> fewer bad generations -> lower token cost -> better CI subsets
```

This is the clearest path to making SoftGNN a research-grade AI testing system rather than only a graph-guided LLM wrapper.

---

# M6.5 — Graph-Native Test Synthesis

## Goal

Shift the role of LLM from **test designer** to **test implementer** by using the code graph and runtime data as the primary reasoning substrate for test design.

Most tools — including multi-agent ones — fundamentally rely on:

```text
prompt -> LLM guesses test -> pytest
```

SoftGNN's unique position is that it owns the code graph, runtime execution graph, and apply-run history. M6.5 puts these at the center of test generation, not as context for LLM prompts, but as the actual reasoning engine.

## The Paradigm Shift

Instead of:

```text
"Write a test for function X"  ->  LLM guesses
```

SoftGNN does:

```text
Graph mines spec of X -> synthesizes test skeleton -> LLM only fills implementation
```

LLM moves from **designer** to **craftsman filling in a blueprint**.

## Specification Mining

Automatically derive behavioral specifications of a function from:

```text
Call graph:
  - who calls X, what does X call
  - preconditions implied by callers
  - postconditions implied by callees

Runtime traces:
  - actual argument shapes seen at runtime
  - actual return values observed
  - which code paths were exercised

Contract history:
  - signature changes across PRs
  - type annotation changes
  - docstring contracts

Apply-run history:
  - which kinds of tests for similar functions succeeded
  - which assertion patterns work for this function type
  - which edge cases historically caused failures
```

Output: a **behavioral spec** for the function:

```text
is_edge_index_sorted:
  - receives: Tensor[2, N], sorted_columns=bool
  - returns: bool
  - invariant: returns True iff edge_index[0] is non-decreasing
  - known edge cases: empty tensor, single edge, unsorted input
  - failure history: mock Tensor incorrectly causes false positive
```

## Test Skeleton Synthesis

From the spec, the graph synthesizes a structured test skeleton before LLM is invoked:

```text
target: is_edge_index_sorted
strategy: happy path + edge cases from spec
skeleton:
  test_is_edge_index_sorted_sorted_returns_true:
    arrange: real Tensor [2, N], sorted
    act: call is_edge_index_sorted(tensor)
    assert: result is True
    runtime_proof: required

  test_is_edge_index_sorted_unsorted_returns_false:
    arrange: real Tensor [2, N], NOT sorted
    act: call is_edge_index_sorted(tensor)
    assert: result is False

  test_is_edge_index_sorted_empty_edge_case:
    arrange: empty Tensor [2, 0]
    act: call is_edge_index_sorted(tensor)
    assert: result is True or raises ValueError
    note: from apply-run history
```

LLM only writes the implementation of each skeleton slot, not the design.

## Hybrid with Multi-Agent (M7)

This is where M6.5 and M7 combine into the strongest possible architecture.

Instead of prompt-driven agents:

```text
"Write a test for X" -> WriterAgent guesses -> ReviewerAgent critiques -> RepairAgent fixes
```

M6.5 + M7 hybrid runs spec-driven agents:

```text
Graph mines behavioral spec of X
  ↓
SkeletonAgent: synthesizes test structure from spec (no LLM, pure graph reasoning)
  ↓
WriterAgent: implements each skeleton slot (LLM, but guided by spec + skeleton)
  ↓
ReviewerAgent: checks implementation against the spec, not just style (LLM, spec-aware)
  ↓
CoverageAgent: verifies runtime proof matches expected paths from spec (deterministic)
  ↓
QualityGate: accepts only tests that prove spec properties hold (deterministic)
```

Key difference: agents work from a **spec and skeleton**, not from a raw prompt. Every agent has a contract to fulfill, not a vague instruction to interpret.

## Why This Stands Above Multi-Agent Alone

| | Multi-Agent (M7 alone) | Graph-Native + Multi-Agent (M6.5 + M7) |
|---|---|---|
| Test design source | LLM interpretation of prompt | Graph-derived behavioral spec |
| Agents' input | Raw function text | Structured spec + skeleton |
| Reviewer checks | Style, correctness (text-based) | Spec compliance (graph-grounded) |
| Improves over time | No | Yes (spec mines from apply-run history) |
| Can be copied | Yes (same prompts) | Hard (requires graph + runtime data) |
| Research story | Multi-agent orchestration | Program synthesis + causal test design |

## Planned Commands

```powershell
softgnn mine-spec --project social-link --target FUNC:is_edge_index_sorted
softgnn synthesize --project social-link --base main --head HEAD
```

`synthesize` runs the full M6.5 + M7 pipeline:

```text
spec mining -> skeleton synthesis -> spec-driven multi-agent -> runtime proof
```

## Why M6.5 Before M7

M6.5 changes what multi-agent works with. Running M7 before M6.5 means agents work from prompts. Running M7 after M6.5 means agents work from specs. The second is meaningfully stronger. M6.5 is the foundation that M7 should build on.

---

# M7 — Multi-Agent Quality Swarm

## Goal

Use role-specialized agents to improve generated test quality.

## Important Principle

Do **not** remove deterministic validators.

```text
Agents propose.
Validators enforce safety.
Pytest verifies correctness.
Runtime graph proves target execution.
QualityGate decides.
```

## Planned Agents

```text
ContextAgent
WriterAgent
ReviewerAgent
RepairAgent
CoverageAgent
Deterministic QualityGate
```

## Flow

```text
Target selection
  ↓
ContextAgent summarizes target behavior
  ↓
WriterAgent creates N candidates
  ↓
Hard schema/safety validation per candidate
  ↓
ReviewerAgent critiques each candidate
  ↓
Candidate sandbox evaluation
  ↓
Pytest + runtime proof
  ↓
RepairAgent if candidate fails
  ↓
QualityGate scores candidates
  ↓
Best candidate is applied
```

## Candidate Strategies

```text
behavior-focused
edge-case-focused
error-path-focused
integration-lite-with-mocks
```

## Same Key/Model Is Fine

M7 can use the same Gemini API key/model for all roles. It is still multi-agent if roles have:

```text
separate prompts
separate schemas
separate responsibilities
orchestrated workflow
```

## Why M7 Comes After M4/M5/M6

Multi-agent is an amplifier, not the core moat. Runtime proof and graph impact reporting should come first.

---

# M8 — Large-Scale Repo Automation

## Goal

Scale generation from one target to many targets across a repository.

## Planned Features

```text
batch target selection
LLM rate limiting
cost budget
checkpoint/resume
batch rollback
per-batch reports
parallel pytest shards
```

## Example CLI

```powershell
python softgnn.py generate-tests `
  --project social-link `
  --scope entire-repo `
  --max-targets 100 `
  --batch-size 5 `
  --budget-usd 2.00 `
  --resume
```

## Why It Matters

Single-target generation is useful for demos. Batch automation is necessary for real repo-wide adoption.

---

# M9 — Controlled Production-Code Fixes

## Goal

Allow SoftGNN to propose production-code fixes when generated tests reveal real bugs.

## Safety Model

Disabled by default.

```text
requires --allow-production-fixes
requires user approval
shows diff before applying
runs pytest after patch
rolls back on failure
```

## Flow

```text
generated test fails
RepairAgent cannot fix test
BugTriageAgent decides production bug is likely
FixAgent proposes production patch
user reviews diff
patch applied only after approval
pytest verifies
```

## Why It Comes Later

This is high-risk. SoftGNN should first mature its test generation, runtime proof, and quality gates.

---

# M10 — Provider/Auth/Enterprise Hardening

## Goal

Make SoftGNN easier to use in teams and enterprise environments.

## Planned Features

```text
Vertex AI auth
service account support
Azure OpenAI
Anthropic provider
OpenAI native provider
per-agent model routing
secret redaction
audit logs
provider retry/rate-limit handling
```

## Example Future Config

```powershell
$env:SOFTGNN_WRITER_MODEL="gemini-3-flash"
$env:SOFTGNN_REVIEWER_MODEL="gemini-3-pro"
$env:SOFTGNN_REPAIR_MODEL="qwen-coder-local"
```

---

# M11 — Local Model Management / Fine-Tuning

## Goal

Reduce cloud dependency and improve model quality using SoftGNN's own successful generation history.

## Planned Features

```text
Ollama/vLLM setup helper
local model health check
model quality benchmark
collect successful generation/repair pairs
build fine-tuning dataset
fine-tune code-test model
evaluate model improvement
```

## Why It Comes Last

This is a separate ML/model-ops layer and should come after the product workflow is proven.

---

---


# Recommended Priority Order

```text
1. Polish v0.1 GitHub release
2. M4 Runtime-Proven Test Generation
3. M5 Graph Impact Report / Dashboard
4. M6 Learned GNN Ranking, CI Subset Selection, and Apply-Run Dataset
5. M6.5 Graph-Native Test Synthesis
6. M7 Multi-Agent Quality Swarm (spec-driven, builds on M6.5)
7. M8 Large-Scale Repo Automation
8. M9 Controlled Production-Code Fixes
9. M10 Enterprise Provider/Auth Hardening
10. M11 Local Model Management / Fine-Tuning
```

---

# Key Product Thesis

Do not market SoftGNN as just another multi-agent test generator.

Market it as:

```text
Graph-guided, runtime-proven, LLM-assisted PR testing.
```

The strongest differentiator is:

```text
SoftGNN knows what changed, knows which tests actually hit it, and generates what is missing with runtime proof.
```
