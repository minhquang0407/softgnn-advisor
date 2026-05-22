# End-to-End Usage Guide

SoftGNN Advisor is graph-guided, runtime-aware, LLM-assisted test generation for Python projects.

This guide starts with the simple CLI and then shows the advanced commands underneath.

---

## 1. Install SoftGNN

```powershell
git clone https://github.com/minhquang0407/softgnn-advisor.git
cd softgnn-advisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
git clone https://github.com/minhquang0407/softgnn-advisor.git
cd softgnn-advisor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Optional: configure an LLM

`scan` never calls an LLM. `plan` and `apply` may call an LLM depending on strategy.

### Gemini

```powershell
$env:SOFTGNN_LLM_PROVIDER="gemini"
$env:SOFTGNN_LLM_MODEL="gemini-3-flash"
$env:SOFTGNN_LLM_API_KEY="YOUR_GEMINI_API_KEY"
```

### OpenAI-compatible endpoint

```powershell
$env:SOFTGNN_LLM_PROVIDER="openai-compatible"
$env:SOFTGNN_LLM_BASE_URL="http://localhost:11434/v1"
$env:SOFTGNN_LLM_MODEL="qwen2.5-coder:7b"
```

No LLM? Use templates:

```powershell
python softgnn.py plan C:\repo\my-app --strategy template
```

---

## 3. 60-second workflow

```powershell
python softgnn.py setup C:\repo\my-app
python softgnn.py scan C:\repo\my-app
python softgnn.py plan C:\repo\my-app
python softgnn.py apply C:\repo\my-app
```

What happens:

```text
setup = build graph + save filesystem snapshot, no training by default
scan  = PR/synthetic scan, no LLM, no writes
plan  = scan + generate proposed tests + save plan bundle
apply = reuse saved plan if valid, patch tests, run pytest, map runtime, confirm scan
```

The project name defaults to the repo folder name. Override it with:

```powershell
python softgnn.py setup C:\repo\my-app --project custom-name
```

---

## 4. Simple commands

### `setup`

```powershell
python softgnn.py setup C:\repo\my-app
```

Defaults:

```text
build graph/PyG data
extract contracts
parse tests
save filesystem snapshot
skip experimental HGT training
```

Train too:

```powershell
python softgnn.py setup C:\repo\my-app --train
```

---

### `scan`

```powershell
python softgnn.py scan C:\repo\my-app
```

Properties:

```text
LLM: no
Writes files: no
Runs pytest: no
Change source: auto
```

Force a source:

```powershell
python softgnn.py scan C:\repo\my-app --source git
python softgnn.py scan C:\repo\my-app --source filesystem
python softgnn.py scan C:\repo\my-app --source full-scan
```

---

### `plan`

```powershell
python softgnn.py plan C:\repo\my-app
```

Properties:

```text
runs scan first
may call LLM depending on --strategy
writes only plan cache
does not patch repo files
does not run pytest
```

Explicit target:

```powershell
python softgnn.py plan C:\repo\my-app --target FUNC:foo --file src/foo.py
```

Template-only, no LLM:

```powershell
python softgnn.py plan C:\repo\my-app --strategy template
```

Saved plan location:

```text
data_output/<project>/plans/latest_plan.json
data_output/<project>/plans/<plan_id>.json
```

---

### `apply`

```powershell
python softgnn.py apply C:\repo\my-app
```

Default behavior:

```text
load latest saved plan if available
validate source hashes / git HEAD
skip pre-scan and LLM generation when the plan is valid
patch tests from the reviewed plan
run pytest
repair generated block if needed
rollback if still failing
run runtime map
run post-scan confirmation
```

Force fresh generation instead of using saved plan:

```powershell
python softgnn.py apply C:\repo\my-app --ignore-plan
```

Apply a specific plan:

```powershell
python softgnn.py apply C:\repo\my-app --plan 20260522_180000
```

Apply a stale plan anyway:

```powershell
python softgnn.py apply C:\repo\my-app --force-stale-plan
```

---

### `map`

```powershell
python softgnn.py map C:\repo\my-app
```

Defaults:

```text
pytest args: tests
mode: per-test
persist: true
```

Custom pytest args:

```powershell
python softgnn.py map C:\repo\my-app --pytest "tests/test_api.py -q"
```

---

## 5. Git, no-Git, and full-scan

SoftGNN change detection supports:

```text
auto        choose best available source
git         Git diff mode
filesystem  no-Git snapshot diff mode
full-scan   treat all Python files as changed
```

### Normal Git project

```powershell
python softgnn.py setup C:\repo\my-app
python softgnn.py scan C:\repo\my-app --source auto
python softgnn.py plan C:\repo\my-app --source auto
python softgnn.py apply C:\repo\my-app --source auto
```

### No-Git project

```powershell
python softgnn.py setup C:\repo\no-git-app
python softgnn.py scan C:\repo\no-git-app --source filesystem
python softgnn.py plan C:\repo\no-git-app --source filesystem
```

### First-run full scan

```powershell
python softgnn.py scan C:\repo\new-app --source full-scan
python softgnn.py plan C:\repo\new-app --source full-scan --max-targets 3
```

---

## 6. Advanced commands

The simple commands are wrappers over advanced commands.

| Simple | Advanced |
|---|---|
| `setup` | `prepare --skip-train` |
| `scan` | `pr-scan --change-source auto` |
| `plan` | `generate-tests --mode plan` + plan cache |
| `apply` | `generate-tests --mode patch --verify --repair-iters 2 --confirm-pr-scan` |
| `map` | `test-map --mode per-test --persist` |

Advanced example:

```powershell
python softgnn.py generate-tests `
  --project my-app `
  --repo-path C:\repo\my-app `
  --base main `
  --head HEAD `
  --mode patch `
  --generation-strategy auto `
  --change-source auto `
  --verify `
  --repair-iters 2 `
  --runtime-mode per-test `
  --confirm-pr-scan
```

---

## 7. Safety recommendations

```text
run on a feature branch
start with plan before apply
review the saved plan output
apply reuses the reviewed plan when valid
use git diff before committing
commit only generated tests you want
never commit API keys or .env files
```

---

## 8. Troubleshooting

### `Data not found for project`

Run setup first:

```powershell
python softgnn.py setup C:\repo\my-app
```

### `LLM provider not configured`

Use templates:

```powershell
python softgnn.py plan C:\repo\my-app --strategy template
```

### Saved plan is stale

The source changed after planning. Re-run:

```powershell
python softgnn.py plan C:\repo\my-app
python softgnn.py apply C:\repo\my-app
```

or force it:

```powershell
python softgnn.py apply C:\repo\my-app --force-stale-plan
```

### New file not found in graph

SoftGNN can parse new Python files transiently. To persist them into the graph:

```powershell
python softgnn.py setup C:\repo\my-app
```

---

## 9. Current limitations

```text
new files are supported as transient scan/generation targets until setup is rerun
runtime-proof acceptance is planned for M4B
large-scale batch generation is planned for M8
production-code modification is disabled by design in v0.1
```
