import json
import shlex
from .gguf import maybe_resolve_gguf

def build_bench_command(params_json: str, run_key: str) -> list[str]:
    """
    Convert SUBMISSION_PARAMS_JSON to a deterministic `uv run bench ...` argv.
    Supports providers: 'vllm', 'transformers'.
    """
    p = json.loads(params_json)

    provider = str(p["test_provider"]).lower()
    if provider not in ("vllm", "transformers"):
        raise SystemExit(f"unsupported provider: {provider}")

    test_model = p["test_model"]
    test_model = maybe_resolve_gguf(test_model)

    judge_models = p.get("judge_models") or []
    if isinstance(judge_models, str):
        judge_models_arg = judge_models
    else:
        judge_models_arg = ",".join(judge_models)

    threads = int(p.get("threads", 96))
    iterations = int(p.get("iterations", 1))
    verbosity = str(p.get("verbosity", "INFO")).upper()
    redo_judging = bool(p.get("redo_judging", False))
    no_elo = bool(p.get("no_elo", False))
    vllm_params_file = p.get("vllm_params_file")

    argv = [
        "uv", "run", "bench",
        "--test-model", test_model,
        "--test-provider", provider,
        "--judge-models", judge_models_arg,
        "--run-id", run_key,
        "--threads", str(threads),
        "--verbosity", verbosity,
        "--iterations", str(iterations),
    ]
    if redo_judging:
        argv.append("--redo-judging")
    if no_elo:
        argv.append("--no-elo")
    if vllm_params_file:
        argv.extend(["--vllm-params-file", vllm_params_file])

    return argv
