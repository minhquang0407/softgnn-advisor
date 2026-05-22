# SoftGNN Advisor

> **Know what changed. Know what tests hit it. Generate what is missing.**

SoftGNN Advisor is an experimental CLI for **graph-guided, runtime-proven, LLM-assisted PR testing**.

It builds a code/test graph, maps which tests actually execute which functions, scans PR impact, detects missing runtime coverage, and generates semantic pytest tests with a verification loop.

Current status: **v0.1 alpha / developer preview**.

---

## Why SoftGNN is different

Most AI test generators do this:

```text
read changed file -> ask an LLM for tests -> run pytest
```

SoftGNN adds graph and runtime evidence:

```text
build code graph
map runtime test execution
scan PR impact
find missing runtime coverage
generate semantic tests
verify with pytest
refresh runtime graph
confirm PR coverage again
```

The goal is not just to generate tests. The goal is to prove that generated tests hit the impacted code.

---

## Core capabilities

- **Code graph extraction** from Python source files.
- **Runtime test mapping** from pytest execution to source functions.
- **PR impact scanning** between Git revisions.
- **Missing coverage detection** at function/test-target level.
- **LLM-assisted semantic pytest generation**.
- **Gemini and OpenAI-compatible providers**.
- **Structured JSON validation** before writing generated tests.
- **Transactional patching and rollback** for generated test blocks.
- **Pytest verification and bounded repair loop**.
- **Runtime refresh after generated tests pass**.
- **PR scan confirmation after runtime refresh**.

---

## Safety model

SoftGNN is intentionally conservative in v0.1:

```text
writes tests/ only by default
wraps generated code in markers
validates LLM output before patching
runs pytest before accepting changes
rolls back failed generated edits by default
never requires committing API keys
```

Generated blocks look like:

```python
# <softgnn-generated target="FUNC:example" start>
...
# <softgnn-generated target="FUNC:example" end>
```

---

## Installation

```bash
git clone https://github.com/YOUR_USER/softgnn-advisor.git
cd softgnn-advisor
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

> PyTorch / PyTorch Geometric installs can be platform-specific. If installation fails, follow the official PyTorch and PyG installation guides for your environment.

---

## Configure Gemini

```powershell
$env:SOFTGNN_LLM_PROVIDER="gemini"
$env:SOFTGNN_LLM_MODEL="gemini-3-flash"
$env:SOFTGNN_LLM_API_KEY="YOUR_GEMINI_API_KEY"
```

If your account uses another model ID, set that instead:

```powershell
$env:SOFTGNN_LLM_MODEL="gemini-2.5-flash"
```

---

## Configure an OpenAI-compatible endpoint

```powershell
$env:SOFTGNN_LLM_PROVIDER="openai-compatible"
$env:SOFTGNN_LLM_BASE_URL="http://localhost:11434/v1"
$env:SOFTGNN_LLM_MODEL="qwen2.5-coder:7b"
$env:SOFTGNN_LLM_API_KEY="optional-if-your-endpoint-needs-it"
```

---

## Quick demo

Run plan mode first. This does not modify files:

```powershell
python softgnn.py generate-tests `
  --project social-link `
  --repo-path "C:\path\to\your\repo" `
  --base main `
  --head HEAD `
  --mode plan `
  --target-id "FUNC:is_edge_index_sorted" `
  --source-file "scripts/train_model.py" `
  --generation-strategy auto `
  --llm-required `
  --no-refresh-runtime
```

Then patch and verify:

```powershell
python softgnn.py generate-tests `
  --project social-link `
  --repo-path "C:\path\to\your\repo" `
  --base main `
  --head HEAD `
  --mode patch `
  --target-id "FUNC:is_edge_index_sorted" `
  --source-file "scripts/train_model.py" `
  --generation-strategy auto `
  --llm-required `
  --verify `
  --repair-iters 2 `
  --runtime-mode per-test `
  --confirm-pr-scan
```

Expected pipeline:

```text
Gemini/OpenAI-compatible LLM generates semantic tests
SoftGNN validates JSON and safety
SoftGNN patches tests transactionally
pytest verifies generated tests
runtime mapping refreshes test/function edges
PR scan confirms missing coverage status
```

---

## Example verified result

On the `social-link-prediction` demo repo, Gemini generated behavior tests for:

```text
FUNC:is_edge_index_sorted
```

Result:

```text
pytest: 6 passed
runtime mode: per-test
runtime edges: 336
persisted: True
missing coverage before: 0
missing coverage after: 0
```

See [docs/examples/social-link-demo.md](docs/examples/social-link-demo.md).

---

## CLI highlights

```powershell
python softgnn.py pr-scan --project social-link --repo-path "C:\path\to\repo" --base main --head HEAD
```

```powershell
python softgnn.py test-map --project social-link --repo-path "C:\path\to\repo" --mode per-test --persist
```

```powershell
python softgnn.py generate-tests --project social-link --repo-path "C:\path\to\repo" --mode plan --generation-strategy auto
```

---

## Provider behavior

Generation strategies:

```text
template  -> deterministic templates only
llm       -> require configured LLM unless fallback allowed
auto      -> try LLM, fallback to templates when unavailable
```

Without an LLM, SoftGNN still works, but targets without semantic templates may produce shallow smoke tests.

With Gemini/OpenAI-compatible providers, SoftGNN can generate richer semantic tests and repair failing generated blocks.

---

## Roadmap

Short version:

```text
v0.1  Single-agent LLM-assisted test generation
M4    Runtime-Proven Test Generation
M5    Graph Impact Report / Dashboard
M6    Learned Test Prioritization / GNN Ranking
M7    Multi-Agent Quality Swarm
M8    Large-scale repo automation
M9    Controlled production-code fixes
```

See [ROADMAP.md](ROADMAP.md).

---

## Release status

SoftGNN Advisor v0.1 is an alpha. It is intended for experimentation and developer workflows, not unattended production code modification.

Recommended first use:

```text
plan mode
inspect generated tests
patch mode on a feature branch
review diff before commit
```

---

## License

Add your preferred license before publishing publicly.
