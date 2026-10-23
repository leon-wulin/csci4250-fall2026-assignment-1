"""Validate frozen Task 2 results before refreshing their handoff checksums."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.run_task2 import guard_environment
from src.task2_core import digest_file, write_json
from src.task3_distributions import load_frozen_task2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="publish verified current output checksums")
    args = parser.parse_args()
    guard_environment()
    # This validates graph topology, source identities, caches and numerical
    # tables without generating random graphs or computing shortest paths.
    load_frozen_task2(ROOT)
    path = ROOT / "results/tables/task2_artifact_manifest.json"
    original_hash = digest_file(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    refreshed, changed = [], []
    for entry in manifest["outputs"]:
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] not in {"data", "results"}:
            raise ValueError(f"Unexpected output path: {relative}")
        artifact = ROOT / relative
        checksum = digest_file(artifact)
        if checksum != entry["sha256"]:
            changed.append(entry["path"])
        refreshed.append({**entry, "bytes": artifact.stat().st_size, "sha256": checksum})
    print(f"PASS: six Task 2 graphs, caches and numerical tables verified; {len(changed)} output checksums differ.")
    if not args.write:
        print("Read-only check; no manifest or analytical output changed.")
        return 0
    backup = path.with_name(f"task2_artifact_manifest.before-refresh-{original_hash[:16]}.json")
    if not backup.exists():
        backup.write_bytes(path.read_bytes())
    manifest["outputs"] = refreshed
    # Original timestamps, report-integration evidence and historical source
    # snapshots remain historical; they are not silently relabeled as current.
    manifest["latest_output_refresh"] = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "previous_manifest_sha256": original_hash,
        "previous_manifest_backup": backup.relative_to(ROOT).as_posix(),
        "validation": "load_frozen_task2 passed; no graph generation or BFS",
        "changed_output_paths": changed,
    }
    write_json(path, manifest)
    print("Updated output checksums; preserved the previous manifest and historical documentation snapshots.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
