import shutil
import subprocess
import sys

def sh(cmd: list[str]):
    return subprocess.run(cmd, check=True).returncode

def ensure_uv():
    # Install uv with pip if not present, then verify.
    try:
        subprocess.run(["uv", "--version"], check=True, stdout=subprocess.DEVNULL)
        return
    except Exception:
        pass
    sh([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    sh([sys.executable, "-m", "pip", "install", "--upgrade", "uv"])
    subprocess.run(["uv", "--version"], check=True)  # verify

def install_core_deps():
    # Pure pip path for core deps.
    sh([sys.executable, "-m", "pip", "install", "--upgrade", "pip<25.3", "setuptools>=77,<80", "wheel"])

    sh([sys.executable, "-m", "pip", "install", "--upgrade", "vllm"])
    # Upgrade transformers after vllm to ensure the newest version wins.
    sh([sys.executable, "-m", "pip", "install", "--upgrade", "transformers"])

def install_open_writing_bench(owb_repo: str, owb_ref: str):
    path = "/workspace/open-writing-bench"
    shutil.rmtree(path, ignore_errors=True)
    sh(["git", "clone", "--depth", "1", "--branch", owb_ref, owb_repo, path])
    # Use uv to install OWB so the `bench` console script is wired up cleanly.
    sh(["uv", "pip", "install", "-e", path])
