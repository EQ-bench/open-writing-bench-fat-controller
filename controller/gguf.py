import os
import re
import requests
from pathlib import Path

def maybe_resolve_gguf(test_model: str) -> str:
    """
    If test_model looks like an HF raw file URL to a .gguf, download it and return local path.
    Otherwise return the original string.
    Accepted forms:
      - https://huggingface.co/<org>/<repo>/resolve/<rev>/<path>.gguf
      - https://huggingface.co/<org>/<repo>/blob/<rev>/<path>.gguf
    """
    if not test_model.lower().endswith(".gguf"):
        return test_model

    url = test_model
    # normalize blob -> resolve for direct download
    url = url.replace("/blob/", "/resolve/")

    target = Path("/workspace/models")
    target.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1]
    out = target / filename

    if out.exists() and out.stat().st_size > 0:
        return str(out)

    # Optional: HF token support if provided via env
    hdrs = {}
    hf = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if hf:
        hdrs["Authorization"] = f"Bearer {hf}"

    with requests.get(url, headers=hdrs, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    return str(out)
