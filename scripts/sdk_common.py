"""Local-only collection utilities. No Git checkout or network is consulted."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CHIP_IDS = frozenset((
    "ym2612", "ym2203", "ym2610", "ym2610b", "rf5c164", "ym2608",
    "gameboy", "segapsg", "ym2151", "pwm", "nes", "dx7", "snes", "spc",
    "huc6280", "okim6258", "ym3526", "ym3812", "y8950", "ymf262", "ym2413", "ay8910",
))
JAVASCRIPT_REFERENCE_IDS = frozenset(("msm5205", "okim6295"))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_record(path):
    data = Path(path).read_bytes()
    return {"sha256": sha256(data), "size": len(data)}


def local_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError(f"Invalid collection path: {name!r}")
    relative = PurePosixPath(name)
    if relative.is_absolute() or any(p in ("", ".", "..") for p in name.split("/")) or ":" in name:
        raise ValueError(f"Path must be relative to the collection: {name!r}")
    target = Path(root).joinpath(*relative.parts)
    for ancestor in (target, *target.parents):
        if ancestor == Path(root).parent:
            break
        if ancestor.is_symlink():
            raise ValueError(f"Symlinks are not collection inputs: {name}")
    if not target.is_file():
        raise ValueError(f"Missing collection file: {name}")
    return target


def metadata(root=ROOT):
    data = read_json(Path(root) / "sdk.json")
    if data.get("name") != "tetorica-soundchip-native" or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", data.get("version", "")):
        raise ValueError("sdk.json must contain the collection name and a safe semantic version")
    return data


def verify_record(root, name, expected):
    actual = file_record(local_path(root, name))
    if actual["sha256"] != expected["sha256"] or ("size" in expected and actual["size"] != expected["size"]):
        raise ValueError(f"Snapshot checksum mismatch: {name}")
    return actual


def check_collection(root=ROOT):
    root = Path(root)
    metadata(root)
    inventory = read_json(root / "catalog/source_inventory.json")
    native = read_json(root / "catalog/native_inventory.json")
    catalog = read_json(root / "catalog/chips.json")
    ids = [chip["id"] for chip in catalog["chips"]]
    if len(ids) != len(set(ids)) or set(ids) != CHIP_IDS:
        raise ValueError("catalog/chips.json must describe all 22 Playground chip IDs exactly once")
    if set(chip["id"] for chip in native["chips"]) != CHIP_IDS:
        raise ValueError("native_inventory.json is missing a Playground chip")
    count = 0
    recorded_sources = set()
    for component in inventory["components"]:
        if not component.get("licenseFiles"):
            raise ValueError(f"No license reference for component {component['id']}")
        for record in component["files"]:
            verify_record(root, record["path"], record)
            recorded_sources.add(record["path"])
            count += 1
    for entry in read_json(root / "native/reference/SOURCES.json")["entries"]:
        verify_record(root, entry["file"], entry)
        count += 1
    # Provenance URLs and originPath are descriptive metadata. Build/catalog
    # references, in contrast, must resolve to included local files.
    def check_references(value):
        if isinstance(value, dict):
            for key, content in value.items():
                if key in ("sourceFiles", "licenseFiles", "buildFiles"):
                    for name in content:
                        local_path(root, name)
                elif key == "buildScript":
                    local_path(root, content)
                elif key not in ("importedFiles", "origin", "files", "entries"):
                    check_references(content)
        elif isinstance(value, list):
            for item in value:
                check_references(item)
    for value in (inventory, native, catalog):
        check_references(value)
    javascript = inventory.get("javascriptReferences", [])
    javascript_ids = [entry["id"] for entry in javascript]
    if len(javascript_ids) != len(set(javascript_ids)) or set(javascript_ids) != JAVASCRIPT_REFERENCE_IDS:
        raise ValueError("JavaScript references must include MSM5205 and OKIM6295 exactly once")
    if catalog.get("javascriptReferences") != javascript:
        raise ValueError("JavaScript reference catalogs differ; run scripts/refresh_catalog.py")
    for entry in javascript:
        if entry.get("format") != "javascript-es-module":
            raise ValueError(f"Unsupported JavaScript reference format: {entry['id']}")
        if entry.get("native", {}).get("status") != "not-ported" or entry.get("wasm", {}).get("status") != "not-ported":
            raise ValueError(f"JavaScript reference must not claim a Native/WASM port: {entry['id']}")
        name = entry.get("entryPoint")
        local_path(root, name)
        if not entry.get("licenseFiles") or not entry.get("sourceFiles") or name not in entry["sourceFiles"]:
            raise ValueError(f"Incomplete JavaScript reference: {entry['id']}")
        if not set(entry["sourceFiles"]).issubset(recorded_sources):
            raise ValueError(f"JavaScript reference has no imported-source checksum: {entry['id']}")
    for chip in catalog["chips"]:
        if not chip.get("sourceFiles") or not chip.get("licenseFiles"):
            raise ValueError(f"Incomplete chip catalog entry: {chip['id']}")
    return {"chips": len(ids), "artifacts": len(inventory["artifacts"]), "javascriptReferences": len(javascript), "snapshotFiles": count}
