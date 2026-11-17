"""Provisioning examples cover the storage resources used by the architectures."""
from __future__ import annotations

import re
import shlex
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def b2_commands():
    readme = (ROOT / "examples/README.md").read_text().replace("\\\n", " ")
    for line in readme.splitlines():
        if line.startswith("b2 "):
            yield shlex.split(line, comments=True)


def test_runtime_key_buckets_are_provisioned():
    commands = list(b2_commands())
    created = {token for command in commands if command[:3] == ["b2", "bucket", "create"]
               for token in command if token.startswith("$ORG-")}
    required = {command[i + 1] for command in commands if command[:3] == ["b2", "key", "create"]
                for i, token in enumerate(command) if token == "--bucket"}
    assert required <= created, f"Missing bucket creation: {required - created}"


def test_architecture_storage_buckets_are_provisioned():
    created = {token for command in b2_commands() if command[:3] == ["b2", "bucket", "create"]
               for token in command if token.startswith("$ORG-")}
    required = set()
    for architecture in (ROOT / "architectures").glob("*/architecture.md"):
        for line in architecture.read_text().splitlines():
            if line.startswith("|") and "optional" not in line.lower():
                required.update("$ORG-" + name for name in re.findall(r"<org>-([a-z][a-z-]+)", line))
    assert required <= created, f"Missing architecture buckets: {required - created}"
