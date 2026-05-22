# End-to-End Usage Guide

This guide shows how to use SoftGNN Advisor from a fresh clone to graph build, PR scan, no-Git synthetic scan, test generation, runtime mapping, and verification.

SoftGNN is currently an alpha/developer preview. Start with `plan` mode, inspect output, then use `patch` mode on a feature branch.

---

## 0. Mental model

SoftGNN is not only an LLM test writer.

```text
code graph + runtime test graph + change detection + LLM generation + pytest verification
```

The core loop:

```text
prepare project
  -> detect changes
  -> map changed files to graph nodes
  -> find missing runtime/static coverage
  -> generate tests
  -> verify with pytest
  -> refresh runtime coverage
  -> confirm coverage again
```

Change detection can come from:

```text
git          normal PR/diff mode
filesystem   snapshot diff for no-Git projects
full-scan    first-run or entire-project scan
auto         choose best available source
```

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

> PyTorch/PyG can be platform-specific. If install fails, install PyTorch and PyTorch Geometric using their official commands for your platform, then rerun `pip install -r requirements.txt`.

---

## 2. Configure an LLM provider

SoftGNN can run with templates, but LLM mode produces better semantic tests.

### Gemini

```powershell
$env:SOFTGNN_LLM_PROVIDER="gemini"
$env:SOFTGNN_LLM_MODEL="gemini-3-flash"
$env:SOFTGNN_LLM_API_KEY="YOUR_GEMINI_API_KEY"
```

If your account uses another model ID:

```powershell
$env:SOFTGNN_LLM_MODEL="gemini-2.5-flash"
```

### OpenAI-compatible endpoint

```powershell
$env:SOFTGNN_LLM_PROVIDER="openai-compatible"
$env:SOFTGNN_LLM_BASE_URL="http://localhost:11434/v1"
$env:SOFTGNN_LLM_MODEL="qwen2.5-coder:7b"
$env:SOFTGNN_LLM_API_KEY="optional-if-your-endpoint-needs-it"
```

### Generation strategies

```text
template  deterministic templates only
llm       require an LLM unless fallback is allowed
auto      try LLM first, fallback to templates
```

---

## 3. Prepare a project

SoftGNN stores project-specific graph data under:

```text
data_output/<project>/
```

### Recommended first-run onboarding

Use `--skip-train` first. It builds graph data and a filesystem snapshot without training the HGT model.

```powershell
python softgnn.py prepare `
  --project my-app `
  --path "C:\path\to\my-app" `
  --skip-train
```

This does:

```text
parse Python source
extract function contracts
parse existing tests
parse Git history if Git exists
save graph/PyG data
save filesystem snapshot
skip HGT training
```

### Full prepare with training

If you want the experimental GNN ranking model:

```powershell
python softgnn.py prepare `
  --project my-app `
  --path "C:\path\to\my-app" `
  --with-train
```

You do **not** need to retrain every time a file changes. Normal workflows use change detection and graph context. Training can be done periodically.

---

## 4. Scan changes in a Git project

For a normal Git repo:

```powershell
python softgnn.py pr-scan `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --base main `
  --head HEAD `
  --change-source git
```

Auto mode is usually enough:

```powershell
python softgnn.py pr-scan `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --base main `
  --head HEAD `
  --change-source auto
```

Expected summary:

```text
Change source: git
Changed files: N
Changed graph nodes: N
Missing coverage: N
Suggested tests: N
```

---

## 5. Scan a project without Git

SoftGNN supports no-Git projects using filesystem snapshots.

### First run without Git

```powershell
python softgnn.py prepare `
  --project no-git-app `
  --path "C:\path\to\no-git-app" `
  --skip-train
```

Then:

```powershell
python softgnn.py pr-scan `
  --project no-git-app `
  --repo-path "C:\path\to\no-git-app" `
  --change-source auto
```

If no Git is detected, SoftGNN uses the filesystem snapshot fallback.

### After adding or editing files

If you add:

```text
src/new_feature.py
```

Run:

```powershell
python softgnn.py pr-scan `
  --project no-git-app `
  --repo-path "C:\path\to\no-git-app" `
  --change-source filesystem
```

SoftGNN treats snapshot changes like a synthetic PR:

```text
added    src/new_feature.py
modified src/calculator.py
deleted  src/old_feature.py
```

For a new Python file not yet in the graph, SoftGNN parses it incrementally and creates transient changed nodes for test planning.

---

## 6. First-run full-scan mode

Use full-scan when:

```text
project has no Git
project has no previous snapshot
you want to scan all Python files as candidate changes
```

```powershell
python softgnn.py pr-scan `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --change-source full-scan
```

Full-scan treats every Python file as added/changed. This is useful for onboarding, but for large repositories use a small `--max-impact` or explicit targets.

---

## 7. Generate tests in plan mode

Plan mode does not modify files.

### Explicit target

```powershell
python softgnn.py generate-tests `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --mode plan `
  --target-id "FUNC:is_edge_index_sorted" `
  --source-file "scripts/train_model.py" `
  --generation-strategy auto `
  --change-source auto `
  --no-refresh-runtime
```

### Auto target selection from changed files

```powershell
python softgnn.py generate-tests `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --base main `
  --head HEAD `
  --mode plan `
  --max-targets 3 `
  --generation-strategy auto `
  --change-source auto `
  --no-refresh-runtime
```

Without an LLM, you may see:

```text
LLM provider not configured; falling back to template generation.
```

---

## 8. Patch, verify, repair, and refresh runtime coverage

Run patch mode only after reviewing the plan output.

```powershell
python softgnn.py generate-tests `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --base main `
  --head HEAD `
  --mode patch `
  --max-targets 3 `
  --generation-strategy auto `
  --verify `
  --repair-iters 2 `
  --runtime-mode per-test `
  --confirm-pr-scan `
  --change-source auto
```

Patch workflow:

```text
validate generated JSON
validate safety constraints
write tests under generated markers
run pytest
repair generated block if pytest fails
rollback if still failing
refresh runtime coverage when passing
run PR scan confirmation again
```

Generated blocks look like:

```python
# <softgnn-generated target="FUNC:example" start>
...
# <softgnn-generated target="FUNC:example" end>
```

Inspect before commit:

```powershell
git diff
```

---

## 9. Map runtime coverage directly

Runtime mapping records which tests actually execute which source functions.

```powershell
python softgnn.py test-map `
  --project my-app `
  --repo-path "C:\path\to\my-app" `
  --pytest-args "tests" `
  --mode per-test `
  --persist
```

Expected output:

```text
Discovered tests: N
Mapped tests: N
Runtime edges: N
Persisted: True
```

Runtime edges are persisted as:

```text
TestFunction -> executes_runtime -> Function
```

---

## 10. Common workflows

### A. Normal Git PR workflow

```powershell
python softgnn.py prepare --project my-app --path "C:\repo\my-app" --skip-train
python softgnn.py pr-scan --project my-app --repo-path "C:\repo\my-app" --base main --head HEAD --change-source auto
python softgnn.py generate-tests --project my-app --repo-path "C:\repo\my-app" --base main --head HEAD --mode plan --change-source auto
python softgnn.py generate-tests --project my-app --repo-path "C:\repo\my-app" --base main --head HEAD --mode patch --verify --repair-iters 2 --confirm-pr-scan --change-source auto
git diff
```

### B. No-Git project workflow

```powershell
python softgnn.py prepare --project no-git-app --path "C:\repo\no-git-app" --skip-train
python softgnn.py pr-scan --project no-git-app --repo-path "C:\repo\no-git-app" --change-source filesystem
python softgnn.py generate-tests --project no-git-app --repo-path "C:\repo\no-git-app" --mode plan --change-source filesystem
```

### C. New project / first-run full scan

```powershell
python softgnn.py prepare --project new-app --path "C:\repo\new-app" --skip-train
python softgnn.py pr-scan --project new-app --repo-path "C:\repo\new-app" --change-source full-scan
python softgnn.py generate-tests --project new-app --repo-path "C:\repo\new-app" --mode plan --change-source full-scan --max-targets 3
```

### D. Explicit target workflow

```powershell
python softgnn.py generate-tests `
  --project my-app `
  --repo-path "C:\repo\my-app" `
  --mode plan `
  --target-id "FUNC:my_function" `
  --source-file "src/my_module.py" `
  --generation-strategy auto
```

---

## 11. Safety recommendations

```text
run on a feature branch
start with --mode plan
patch only after reviewing the plan
use --verify and --confirm-pr-scan
review git diff manually
commit only generated tests you want to keep
never commit API keys or .env files
```

---

## 12. Troubleshooting

### `Data not found for project`

Run prepare first:

```powershell
python softgnn.py prepare --project my-app --path "C:\repo\my-app" --skip-train
```

### `LLM provider not configured`

Either configure an LLM or use templates:

```powershell
python softgnn.py generate-tests --project my-app --repo-path "C:\repo\my-app" --mode plan --generation-strategy template
```

### `Changed Python file not found in graph`

This can happen for new files. SoftGNN will parse the file incrementally and create transient scan targets. To persist the file into the graph, rerun:

```powershell
python softgnn.py prepare --project my-app --path "C:\repo\my-app" --skip-train
```

### No Git repository

Use:

```powershell
--change-source filesystem
```

or:

```powershell
--change-source full-scan
```

---

## 13. Current limitations

```text
M4A handles new files as transient scan/generation targets.
Persisting fully incremental graph updates without ETL is a future optimization.
Runtime-proof acceptance is planned for M4B.
Large-scale batch generation is planned for M8.
Production-code fixes are disabled by design in v0.1.
```
