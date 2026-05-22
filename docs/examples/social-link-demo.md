# Social Link Prediction Demo

This example documents a real SoftGNN v0.1 alpha smoke run against a local `social-link-prediction` repository.

The purpose is to show the difference between template fallback and LLM-assisted semantic generation.

---

## Target

```text
Project: social-link
Target: FUNC:is_edge_index_sorted
Source: scripts/train_model.py
Generation strategy: auto
Provider: Gemini
Mode: patch
```

---

## Fallback behavior without LLM

When no LLM provider is configured, SoftGNN still runs and falls back to templates.

Warning:

```text
LLM provider not configured; falling back to template generation.
```

Fallback test:

```python
from scripts.train_model import is_edge_index_sorted


def test_is_edge_index_sorted_semantic():
    assert callable(is_edge_index_sorted)
```

This is safe, but shallow.

---

## Gemini-assisted behavior

With Gemini configured and `--llm-required`, SoftGNN generated behavior-focused tests for:

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

## Verification result

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

## Why this matters

A passing smoke test can be trivial:

```python
assert callable(is_edge_index_sorted)
```

SoftGNN with an LLM provider produced behavior tests and then verified them with pytest and runtime mapping.

This demonstrates the v0.1 thesis:

```text
Know what changed.
Know what tests hit it.
Generate what is missing.
```
