"""Check publishable files and reachable Git history without printing secret values."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOTS = {"src", "tests", "tools", "scripts", "docs", "assets", ".github"}
ALLOWED_FILES = {".env.example", ".gitignore", ".gitattributes", "README.md", "README.en.md",
                 "LICENSE", "COPYRIGHT", "CITATION.cff", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md",
                 "SECURITY.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml", "publish.cmd"}
SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ps1", ".bat", ".cmd", ".svg", ".png", ".ico", ".cff"}
PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "cloud-access-key": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "service-token": re.compile(rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{32,}|xox[baprs]-[A-Za-z0-9-]{20,})"),
    "credential-url": re.compile(rb"https?://[^\s/:@]+:[^\s/@]+@"),
    "assigned-secret": re.compile(rb"(?im)^\s*(?:api_key|secret_key|access_token|password|client_secret)\s*[=:]\s*[\"']?[A-Za-z0-9_+/=-]{16,}"),
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def candidate_files() -> list[str]:
    return sorted({p.decode("utf-8") for p in git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")
                   if p and ((ROOT / p.decode("utf-8")).exists() or (ROOT / p.decode("utf-8")).is_symlink())})


def scan(data: bytes, location: str) -> list[str]:
    return [f"{name}: {location}" for name, pattern in PATTERNS.items() if pattern.search(data)]


def check(history: bool = True) -> dict:
    findings = []
    files = candidate_files()
    total = 0
    for name in files:
        path = ROOT / name
        rel = Path(name)
        permitted = (name in ALLOWED_FILES or
                     (rel.parent == Path('.') and re.fullmatch(r"requirements(?:-[a-z]+)?\.txt", name)) or
                     (rel.parts[0] in ALLOWED_ROOTS and path.suffix.lower() in SUFFIXES))
        if not permitted or any(part in {"__pycache__", "node_modules", ".venv"} for part in rel.parts):
            findings.append(f"unexpected-file: {name}")
        if path.is_symlink():
            findings.append(f"symlink: {name}")
            continue
        data = path.read_bytes()
        total += len(data)
        if len(data) > 5 * 1024 * 1024:
            findings.append(f"over-5-MiB: {name}")
        if path.suffix.lower() in {".png", ".ico", ".svg"} and rel.parts[0] != "assets":
            findings.append(f"unexpected-image: {name}")
        findings.extend(scan(data, name))
    blobs = 0
    if history:
        objects = git("rev-list", "--objects", "--all").splitlines()
        for row in objects:
            oid, _, name = row.partition(b" ")
            kind = git("cat-file", "-t", oid.decode()).strip()
            if kind not in {b"blob", b"commit", b"tag"}:
                continue
            data = git("cat-file", "-p", oid.decode())
            findings.extend(scan(data, f"history:{oid.decode()[:12]}:{name.decode('utf-8', errors='replace')}"))
            if kind == b"blob":
                blobs += 1
                if len(data) > 5 * 1024 * 1024:
                    findings.append(f"historical-large-blob: {oid.decode()[:12]}")
                if Path(name.decode('utf-8', errors='replace')).suffix.lower() in {'.pt', '.pth', '.onnx', '.zip', '.pem', '.key'}:
                    findings.append(f"historical-restricted-file: {name.decode('utf-8', errors='replace')}")
                basename = Path(name.decode('utf-8', errors='replace')).name
                if basename == '.env' or (basename.startswith('.env.') and basename != '.env.example'):
                    findings.append(f"historical-local-config: {name.decode('utf-8', errors='replace')}")
    return {"files": len(files), "bytes": total, "history_blobs": blobs, "findings": findings,
            "scope": "Candidate working tree and reachable local Git refs; pattern scan, not a guarantee of absence."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-history', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check(not args.no_history)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    return int(bool(result['findings']))


if __name__ == '__main__':
    raise SystemExit(main())
