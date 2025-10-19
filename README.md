Runs OWB inside a Runpod. Reads env:
- DATABASE_URL: OWB DB URL
- RUN_KEY: run identifier to pass through
- SUBMISSION_PARAMS_JSON: JSON from scheduler
- OWB_REPO, OWB_REF: source for open-writing-bench

Behavior:
- installs vllm then upgrades transformers
- installs OWB with uv
- resolves .gguf URLs by downloading to /workspace/models
- runs `uv run bench ...`
- streams stdout/stderr to run_logs every 30s
