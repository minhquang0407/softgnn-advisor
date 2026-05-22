# Social Link Prediction Demo

This example shows a realistic SoftGNN workflow against a local `social-link-prediction` repository.

It reflects the current CLI model:

```text
setup/prepare need the repo path once
everyday commands use --project
```

---

## 1. Register the project once

From the SoftGNN repository:

```powershell
python softgnn.py setup C:\Users\nguye\social-link-prediction --project social-link
```

This builds the graph, extracts contracts, parses tests, saves a filesystem snapshot, and stores the source repo path in:

```text
data_output/social-link/metadata.json
```

After this, you normally do **not** need to pass `C:\Users\nguye\social-link-prediction` again.

---

## 2. One-command generation flow

For day-to-day use, run:

```powershell
python softgnn.py apply --project social-link
```

`apply` runs the full workflow:

```text
detect changes
run pr-scan
rank missing coverage targets
generate tests using LLM/template
patch test files
run pytest
repair if failing
rollback if still failing
run runtime map
run post-scan confirmation
```

---

## 3. Review-first flow

If you want to inspect the proposed tests before patching:

```powershell
python softgnn.py plan --project social-link
```

Then apply the reviewed plan:

```powershell
python softgnn.py apply --project social-link
```

When the saved plan is still valid, `apply` skips pre-scan and LLM generation and patches exactly what was reviewed.

---

## 4. Inspect-only scan

To inspect changed files, impacted nodes, related tests, and missing coverage without LLM calls or writes:

```powershell
python softgnn.py scan --project social-link
```

Properties:

```text
LLM: no
Writes files: no
Runs pytest: no
```

---

## 5. Targeted example

Example target:

```text
Project: social-link
Target: FUNC:is_edge_index_sorted
Source: scripts/train_model.py
Generation strategy: auto
Provider: Gemini when configured, template fallback otherwise
```

Plan only:

```powershell
python softgnn.py plan --project social-link --target FUNC:is_edge_index_sorted --file scripts/train_model.py
```

Apply reviewed plan:

```powershell
python softgnn.py apply --project social-link
```

Force fresh generation instead of using the saved plan:

```powershell
python softgnn.py apply --project social-link --ignore-plan --target FUNC:is_edge_index_sorted --file scripts/train_model.py
```

Template-only, no LLM:

```powershell
python softgnn.py apply --project social-link --strategy template --target FUNC:is_edge_index_sorted --file scripts/train_model.py
```

---

## 6. Fallback behavior without LLM

When no LLM provider is configured, SoftGNN can fall back to templates.

Warning:

```text
LLM provider not configured; falling back to template generation.
```

Fallback test shape:

```python
from scripts.train_model import is_edge_index_sorted


def test_is_edge_index_sorted_semantic():
    assert callable(is_edge_index_sorted)
```

This is safe, but shallow. Use it when you want deterministic generation without API calls.

---

## 7. Gemini-assisted behavior

With Gemini configured and `--strategy auto` or `--strategy llm`, SoftGNN can generate behavior-focused tests for:

```text
sorted edge_index
unsorted source ordering
unsorted target ordering within a source
single-edge input
invalid shape error path
```

Example generated test:

```python
import pytest
import torch
from scripts.train_model import is_edge_index_sorted


def test_is_edge_index_sorted():
    edge_index_sorted = torch.tensor([[0, 0, 1, 1, 2], [1, 2, 0, 1, 0]], dtype=torch.long)
    assert is_edge_index_sorted(edge_index_sorted) is True

    edge_index_unsorted_src = torch.tensor([[0, 2, 1], [1, 0, 0]], dtype=torch.long)
    assert is_edge_index_sorted(edge_index_unsorted_src) is False

    edge_index_unsorted_dst = torch.tensor([[0, 0, 1], [2, 1, 0]], dtype=torch.long)
    assert is_edge_index_sorted(edge_index_unsorted_dst) is False

    assert is_edge_index_sorted(torch.tensor([[0], [1]], dtype=torch.long)) is True

    with pytest.raises(ValueError):
        is_edge_index_sorted(torch.tensor([0, 1, 2]))
```

---

## 8. Verification result

A successful `apply` shows pytest and runtime mapping evidence:

```text
pytest: 6 passed, 18 warnings in 15.73s
```

Runtime refresh:

```text
Mode used: per-test
Discovered tests: 6
Runtime edges: 336
Persisted: True
```

PR scan confirmation:

```text
Missing coverage before: 0
Missing coverage after: 0
```

---

## 9. Other daily commands

Health check:

```powershell
python softgnn.py doctor --project social-link
```

Impact of one symbol:

```powershell
python softgnn.py impact --project social-link FUNC:is_edge_index_sorted
```

Developer triage:

```powershell
python softgnn.py triage --project social-link "edge index sorting bug in training"
```

Runtime test map only:

```powershell
python softgnn.py map --project social-link
```

---

## Why this matters

A passing smoke test can be trivial:

```python
assert callable(is_edge_index_sorted)
```

SoftGNN with an LLM provider can produce behavior tests and then verify them with pytest and runtime mapping.

This demonstrates the v0.1 thesis:

```text
Know what changed.
Know what tests hit it.
Generate what is missing.
```
