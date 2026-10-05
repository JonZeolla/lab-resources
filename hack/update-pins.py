#!/usr/bin/env python3
"""Bump the exact version pins in role defaults to their latest upstream releases.

Values are rewritten in place, so the comments around them survive. A pin only
moves forward, and everything tied to it (checksums, bundled versions, engine
floors) is recomputed for the new version before anything is written.
"""

import hashlib
import io
import json
import os
import re
import tarfile
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROLES = Path(__file__).resolve().parent.parent / "ansible/jonzeolla/labs/roles"
VERSION = re.compile(r"\d+(\.\d+)*")


def fetch(url: str) -> bytes:
    headers = {"User-Agent": "lab-resources-update-pins"}
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def fetch_json(url: str) -> dict | list:
    return json.loads(fetch(url))


def sha256(url: str) -> str:
    return f"sha256:{hashlib.sha256(fetch(url)).hexdigest()}"


def github_latest(repo: str, tag: str = r"v(\d+\.\d+\.\d+)") -> str | None:
    """The version in the latest release's tag, if the tag has the shape the role expects."""
    release = fetch_json(f"https://api.github.com/repos/{repo}/releases/latest")
    match = re.fullmatch(tag, release["tag_name"])
    return match.group(1) if match else None


def gitlab_latest(project: str, tag: str = r"v(\d+\.\d+\.\d+)") -> str | None:
    """The version in the latest release's tag, if the tag has the shape the role expects."""
    release = fetch_json(
        f"https://gitlab.com/api/v4/projects/{urllib.parse.quote(project, safe='')}"
        "/releases/permalink/latest"
    )
    match = re.fullmatch(tag, release["tag_name"])
    return match.group(1) if match else None


def npm_manifest(package: str, version: str = "latest") -> dict:
    return fetch_json(f"https://registry.npmjs.org/{package}/{version}")


def npm_latest(package: str) -> Callable[[], str]:
    return lambda: npm_manifest(package)["version"]


def pi_extras(version: str) -> dict[str, str]:
    # The role asserts node against the package's engines floor; keep it the
    # floor of the version being pinned. Anything but a plain ">=X.Y.Z" is left
    # for a human.
    engines = npm_manifest("@earendil-works/pi-coding-agent", version).get(
        "engines", {}
    )
    match = re.fullmatch(r">=\s*v?(\d+\.\d+\.\d+)", engines.get("node", "").strip())
    return {"pi_minimum_node_version": match.group(1)} if match else {}


def vscode_latest() -> str:
    return fetch_json("https://update.code.visualstudio.com/api/releases/stable")[0]


def nodejs_windows_latest() -> str:
    # Follow the major line the Linux side is on, so both platforms match.
    major = read_value(ROLES / "nodejs/defaults/main.yml", "nodejs_major_version")
    releases = fetch_json("https://nodejs.org/dist/index.json")
    return next(
        r["version"] for r in releases if r["version"].startswith(f"v{major}.")
    )[1:]


def bpftool_extras(version: str) -> dict[str, str]:
    # The bundle ships its own libbpf; the role's `creates:` names the shared
    # object libbpf's Makefile derives from the newest symbol version in libbpf.map.
    url = (
        f"https://github.com/libbpf/bpftool/releases/download/v{version}"
        f"/bpftool-libbpf-v{version}-sources.tar.gz"
    )
    bundle = fetch(url)
    with tarfile.open(fileobj=io.BytesIO(bundle)) as tar:
        member = next(
            m for m in tar.getmembers() if m.name.endswith("/libbpf/src/libbpf.map")
        )
        symbols = tar.extractfile(member).read().decode()
    libbpf = max(
        re.findall(r"^LIBBPF_(\d+\.\d+\.\d+)", symbols, re.MULTILINE), key=as_tuple
    )
    return {
        "ebpf_libbpf_version": libbpf,
        "ebpf_sources_checksum": f"sha256:{hashlib.sha256(bundle).hexdigest()}",
    }


def per_arch_checksums(
    role: str, key: str, url: Callable[[str], str]
) -> dict[str, str]:
    """Checksum every architecture already listed under `key`, using the role's URL."""
    defaults = ROLES / role / "defaults/main.yml"
    return {f"{key}.{arch}": sha256(url(arch)) for arch in read_mapping(defaults, key)}


def bpftrace_extras(version: str) -> dict[str, str]:
    return per_arch_checksums(
        "ebpf",
        "ebpf_bpftrace_checksums",
        lambda arch: (
            f"https://github.com/bpftrace/bpftrace/releases/download/v{version}/bpftrace-{arch}"
        ),
    )


def task_extras(version: str) -> dict[str, str]:
    arches = read_mapping(ROLES / "ebpf/defaults/main.yml", "ebpf_task_architectures")
    return per_arch_checksums(
        "ebpf",
        "ebpf_task_checksums",
        lambda arch: (
            f"https://github.com/go-task/task/releases/download/v{version}"
            f"/task_linux_{arches[arch]}.tar.gz"
        ),
    )


def gitlab_cli_extras(version: str) -> dict[str, str]:
    arches = read_mapping(
        ROLES / "gitlab_cli/defaults/main.yml", "gitlab_cli_architectures"
    )
    return per_arch_checksums(
        "gitlab_cli",
        "gitlab_cli_checksums",
        lambda arch: (
            f"https://gitlab.com/gitlab-org/cli/-/releases/v{version}/downloads"
            f"/glab_{version}_linux_{arches[arch]}.rpm"
        ),
    )


@dataclass
class Pin:
    role: str
    key: str
    latest: Callable[[], str | None]
    # Values that must change in lockstep with the version, keyed by YAML key
    # (a dotted key addresses one entry of a mapping).
    extras: Callable[[str], dict[str, str]] = field(default=lambda version: {})


PINS = [
    Pin("claude_code", "claude_code_version", npm_latest("@anthropic-ai/claude-code")),
    Pin("codex", "codex_version", npm_latest("@openai/codex")),
    Pin("copilot", "copilot_version", npm_latest("@github/copilot")),
    Pin("pi", "pi_version", npm_latest("@earendil-works/pi-coding-agent"), pi_extras),
    Pin("vscode", "vscode_version", vscode_latest),
    Pin("github_cli", "github_cli_version", lambda: github_latest("cli/cli")),
    Pin(
        "gitlab_cli",
        "gitlab_cli_version",
        lambda: gitlab_latest("gitlab-org/cli"),
        gitlab_cli_extras,
    ),
    # The role builds its download URL around a .windows.1 tag, so a later
    # .windows.N respin is skipped rather than written as a broken pin.
    Pin(
        "git",
        "git_windows_version",
        lambda: github_latest("git-for-windows/git", r"v(\d+\.\d+\.\d+)\.windows\.1"),
    ),
    Pin("nodejs", "nodejs_windows_version", nodejs_windows_latest),
    Pin(
        "ebpf",
        "ebpf_bpftool_version",
        lambda: github_latest("libbpf/bpftool"),
        bpftool_extras,
    ),
    Pin(
        "ebpf",
        "ebpf_bpftrace_version",
        lambda: github_latest("bpftrace/bpftrace"),
        bpftrace_extras,
    ),
    Pin(
        "ebpf", "ebpf_task_version", lambda: github_latest("go-task/task"), task_extras
    ),
]


SCALAR = (
    r"(?P<prefix>{indent}{key}:[ \t]*)(?P<quote>['\"]?)(?P<value>[^'\"\s#]*)(?P=quote)"
)


def find_value(text: str, key: str) -> re.Match:
    """Locate a top-level `key: value`, or `parent.child` inside a top-level mapping."""
    parent, _, child = key.rpartition(".")
    start, end = 0, len(text)
    if parent:
        block = re.search(
            rf"^{re.escape(parent)}:[ \t]*\n((?:[ \t]+.*\n?)+)", text, re.MULTILINE
        )
        if block is None:
            raise SystemExit(f"mapping {parent} not found")
        start, end = block.span(1)
    pattern = SCALAR.format(indent=r"[ \t]+" if parent else "", key=re.escape(child))
    match = re.compile(rf"^{pattern}", re.MULTILINE).search(text, start, end)
    if match is None:
        raise SystemExit(f"{key} not found")
    return match


def read_value(path: Path, key: str) -> str:
    return find_value(path.read_text(), key)["value"]


def read_mapping(path: Path, key: str) -> dict[str, str]:
    block = re.search(
        rf"^{re.escape(key)}:[ \t]*\n((?:[ \t]+.*\n?)+)", path.read_text(), re.MULTILINE
    )
    entries = re.findall(
        r"^[ \t]+([\w-]+):[ \t]*['\"]?([^'\"\s#]*)", block.group(1), re.MULTILINE
    )
    return dict(entries)


def write_values(path: Path, values: dict[str, str]) -> None:
    text = path.read_text()
    for key, value in values.items():
        match = find_value(text, key)
        replacement = f"{match['prefix']}{match['quote']}{value}{match['quote']}"
        text = text[: match.start()] + replacement + text[match.end() :]
    path.write_text(text)


def as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def update(pin: Pin) -> None:
    path = ROLES / pin.role / "defaults/main.yml"
    current = read_value(path, pin.key)
    latest = pin.latest()
    if latest is None or not VERSION.fullmatch(latest):
        print(f"{pin.key}: skipped, no usable upstream version ({latest!r})")
        return
    if as_tuple(latest) <= as_tuple(current):
        return
    # Resolve everything first so a failed lookup leaves the file untouched.
    values = {pin.key: latest, **pin.extras(latest)}
    write_values(path, values)
    print(f"{pin.key}: {current} -> {latest}")


def run() -> None:
    for pin in PINS:
        update(pin)


if __name__ == "__main__":
    run()
