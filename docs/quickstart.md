# Quickstart

This guide walks through a safe first run of SoftGNN Advisor.

SoftGNN is currently a **v0.1 alpha**. Start in `plan` mode before patching files.

---

## 1. Install

```powershell
git clone https://github.com/YOUR_USER/softgnn-advisor.git
cd softgnn-advisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 2. Configure an LLM provider

### Gemini

```powershell
$env:SOFTGNN_LLM_PROVIDER="gemini"
$env:SOFTGNN_LLM_MODEL="gemini-3-flash"
$env:SOFTGNN_LLM_API_KEY="YOUR_GEMINI_API_KEY"
```

If the model ID is different for your account:

```powershell
$env:SOFTGNN_LLM_MODEL="gemini-2.5-flash"
```

### OpenAI-compatible endpoint

```powershell
$env:SOFTGNN_LLM_PROVIDER="openai-compatible"
$env:SOFTGNN_LLM_BASE_URL="http://localhost:11434/v1"
$env:SOFTGNN_LLM_MODEL="qwen2.5-coder:7b"
```

---

## 3. Run plan mode

Plan mode prints proposed tests and does not modify files.

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

Expected when an LLM is configured:

```text
semantic pytest tests based on the target source
no fallback warning
```

Expected without an LLM:

```text
LLM provider not configured; falling back to template generation.
```

---

## 4. Patch and verify

Run this only after reviewing the plan output.

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

The patch workflow:

```text
validate generated JSON
write tests/ transactionally
run pytest
repair generated block if needed
rollback if still failing
refresh runtime coverage if passing
confirm PR scan after refresh
```

---

## 5. Inspect the diff

```powershell
git diff
```

Generated test blocks are marked:

```python
# <softgnn-generated target="FUNC:..." start>
...
# <softgnn-generated target="FUNC:..." end>
```

---

## 6. Recommended release workflow

```text
run on a feature branch
start with --mode plan
use --mode patch after review
review generated tests manually
commit only tests and docs you want to keep
never commit API keys or .env files
```
