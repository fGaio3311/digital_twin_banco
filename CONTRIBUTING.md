Contributing and local linting

- This repository uses `pre-commit` for lightweight commit-time fixes (trailing whitespace, EOF fixer).
- Heavy checks (flake8, mypy, bandit) are run in CI via GitHub Actions and are configured as `manual` in `.pre-commit-config.yaml` to avoid blocking local commits.

To run checks locally in your venv:

```powershell
# activate venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install flake8 mypy bandit pre-commit
pre-commit run --hook-stage pre-commit --all-files
# run heavy checks manually
flake8 . --max-line-length=88
mypy .
bandit -r . -f txt -o bandit_output.txt
```

If you want to re-enable heavy checks on commit, remove `stages: [manual]` for the hooks in `.pre-commit-config.yaml` and run `pre-commit install`.
