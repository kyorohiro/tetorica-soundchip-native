#!/usr/bin/env python3
"""Audit release archives, then build the extracted SDK without another checkout.

Uses only Python's standard library, CMake and the installed C++ toolchain.
No dependency download or network package manager is run by this test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import zipfile


class AuditError(RuntimeError):
    pass


REQUIRED_CHIPS = frozenset("ym2612 ym2203 ym2610 ym2610b rf5c164 ym2608 gameboy segapsg ym2151 pwm nes dx7 snes spc huc6280 okim6258 ym3526 ym3812 y8950 ymf262 ym2413 ay8910".split())
REQUIRED_ARTIFACTS = frozenset("ay8910 gameboy_apu huc6280 k051649 nesapu nuked_opn2 okim6258 pwm32x rf5c164 segapcm segapsg spc y8950 ym2151 ym2203 ym2413 ym2608 ym2610b ym2612 ym3438 ym3526 ym3812 ymf262 ymf276 ymf278b ymf288 dx7".split())


def require(value, message):
    if not value:
        raise AuditError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value and "\0" not in value,
            f"Invalid release path: {value!r}")
    path = PurePosixPath(value)
    require(not path.is_absolute() and not re.match(r"^[A-Za-z]:", value)
            and all(part not in (".", "..", "") for part in value.split("/")),
            f"Release path escapes its root: {value}")
    return path


def within(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def read_json(path):
    require(path.is_file(), f"Missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unpack(archive, destination):
    """Validate every member before writing any archive content."""
    with zipfile.ZipFile(archive) as source:
        members = source.infolist()
        require(members, "Empty release archive")
        roots, names, folded_names = set(), set(), set()
        for member in members:
            name = member.filename.rstrip("/")
            path = relative_path(name)
            require(name not in names, f"Duplicate ZIP member: {name}")
            require(name.casefold() not in folded_names, f"Case-colliding ZIP member: {name}")
            names.add(name)
            folded_names.add(name.casefold())
            roots.add(path.parts[0])
            mode = member.external_attr >> 16
            require(not stat.S_ISLNK(mode), f"Symlink in release ZIP: {name}")
            require(not mode or stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR),
                    f"Non-regular ZIP member: {name}")
            require(not member.flag_bits & 1, f"Encrypted ZIP member: {name}")
        require(len(roots) == 1, "Release ZIP must contain one SDK root directory")
        root = destination / next(iter(roots))
        source.extractall(destination)
    require(root.is_dir(), "SDK release root is not a directory")
    return root


def audit_manifest(root, expected_kind):
    manifest = read_json(root / "RELEASE-MANIFEST.json")
    require(manifest.get("schemaVersion") == 1 and manifest.get("kind") == expected_kind,
            f"Unexpected release manifest schema/kind: {expected_kind}")
    require(manifest.get("name") == "tetorica-soundchip-native" and manifest.get("version"),
            "Missing SDK release identity")
    files = manifest.get("files")
    require(isinstance(files, dict) and files, "Manifest has no file inventory")
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"Symlink after extraction: {path}")
        if path.is_file() and path != root / "RELEASE-MANIFEST.json":
            actual.add(path.relative_to(root).as_posix())
    require(actual == set(files), f"Manifest inventory mismatch: missing={sorted(set(files)-actual)}, unlisted={sorted(actual-set(files))}")
    for name, metadata in files.items():
        path = root / relative_path(name)
        require(isinstance(metadata, dict) and isinstance(metadata.get("size"), int),
                f"Invalid manifest record: {name}")
        require(path.stat().st_size == metadata["size"], f"Size mismatch: {name}")
        require(digest(path) == metadata.get("sha256"), f"SHA-256 mismatch: {name}")
    return manifest


def check_references(root, owner, key, values):
    require(isinstance(values, list) and values, f"{owner}: no {key}")
    for name in values:
        path = root / relative_path(name)
        require(path.is_file() and within(path, root), f"{owner}: missing/outside {key} reference {name}")
        if key == "licenseFiles":
            require(path.stat().st_size > 0, f"{owner}: empty license file {name}")


def audit_catalog(root):
    catalog = read_json(root / "catalog/chips.json")
    require(catalog.get("schemaVersion") == 1, "Unsupported chip catalog schema")
    chips = catalog.get("chips")
    require(isinstance(chips, list) and chips, "Chip catalog is empty")
    ids = [chip.get("id") for chip in chips]
    require(all(isinstance(chip, str) and chip for chip in ids) and len(ids) == len(set(ids)),
            "Missing or duplicate chip catalog ID")
    require(set(ids) == REQUIRED_CHIPS, f"Public chip catalog changed: missing={sorted(REQUIRED_CHIPS-set(ids))}, extra={sorted(set(ids)-REQUIRED_CHIPS)}")
    for chip in chips:
        for key in ("sourceFiles", "licenseFiles"):
            check_references(root, chip["id"], key, chip.get(key))
    inventory = read_json(root / "catalog/source_inventory.json")
    for section in ("components", "artifacts"):
        records = inventory.get(section)
        require(isinstance(records, list) and records, f"Missing source inventory {section}")
        record_ids = [record.get("id") for record in records]
        require(len(record_ids) == len(set(record_ids)), f"Duplicate source inventory {section} ID")
        if section == "artifacts":
            require(set(record_ids) == REQUIRED_ARTIFACTS, f"WASM source artifact inventory changed: missing={sorted(REQUIRED_ARTIFACTS-set(record_ids))}, extra={sorted(set(record_ids)-REQUIRED_ARTIFACTS)}")
        for record in records:
            for key in ("sourceFiles", "licenseFiles"):
                check_references(root, record["id"], key, record.get(key))
            for item in record.get("files", []):
                path = root / relative_path(item["path"])
                require(path.is_file(), f"Missing imported source: {item['path']}")
                require(digest(path) == item.get("sha256"), f"Imported source hash mismatch: {item['path']}")
            # Imported reference binaries describe their original provenance;
            # source archives intentionally need not contain dist/ binaries.
            for item in record.get("importedFiles", []):
                relative_path(item["path"])
                require(re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", "")),
                        f"Invalid imported reference digest: {item['path']}")
            if section == "artifacts":
                check_references(root, record["id"], "buildScript", [record.get("buildScript")])
                require(isinstance(record.get("chipIds"), list) and record["chipIds"],
                        f"{record['id']}: absent chipIds")
    covered = {chip for artifact in inventory["artifacts"] for chip in artifact["chipIds"]}
    require(set(ids) <= covered, f"WASM inventory lost public chips: {sorted(set(ids)-covered)}")
    native = read_json(root / "catalog/native_inventory.json")
    require(native.get("schemaVersion") == 1 and {chip["id"] for chip in native.get("chips", [])} == REQUIRED_CHIPS,
            "Native reference inventory lost a public chip")
    for chip in native["chips"]:
        check_references(root, chip["id"], "sourceFiles", chip.get("sourceFiles"))
        require(chip.get("status") in ("source-only", "verified"), f"Unknown Native status: {chip['id']}")
    provenance = read_json(root / "native/reference/SOURCES.json")
    require(provenance.get("schemaVersion") == 1 and provenance.get("entries"), "Missing Native source provenance")
    for item in provenance["entries"]:
        path = root / relative_path(item["file"])
        require(path.is_file() and digest(path) == item.get("sha256"), f"Native source provenance hash mismatch: {item['file']}")
    native_files = {path.relative_to(root).as_posix() for path in (root / "native/reference").rglob("*")
                    if path.is_file() and path.suffix in (".c", ".cc", ".cpp", ".h", ".hpp", ".inc", ".ipp")}
    require(native_files <= {item["file"] for item in provenance["entries"]}, "Native reference source disappeared from provenance inventory")
    return catalog, inventory


def audit_local_sources(root):
    source_suffixes = {".h", ".hh", ".hpp", ".inc", ".ipp", ".inl", ".c", ".cc", ".cpp", ".cxx"}
    network_cmake = re.compile(r"\b(?:FetchContent_(?:Declare|Populate|MakeAvailable)|ExternalProject_Add)\s*\(|\bfile\s*\(\s*DOWNLOAD", re.I)
    network_shell = re.compile(r"\b(?:curl|wget)\s|\bgit\s+clone\b|\b(?:npm|pip3?|uv)\s+(?:install|sync)\b")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if path.suffix.lower() in source_suffixes:
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r'^\s*#\s*include\s*"([^"\n]+)"', text, re.M):
                include = match.group(1)
                require(not include.startswith(("/", "\\")) and not re.match(r"^[A-Za-z]:", include),
                        f"Absolute source include in {name}: {include}")
                if ".." in PurePosixPath(include.replace("\\", "/")).parts:
                    require(within(path.parent / include.replace("\\", "/"), root), f"Outside source include in {name}: {include}")
        if path.name == "CMakeLists.txt" or path.suffix == ".cmake":
            text = "\n".join(line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
            require(not network_cmake.search(text), f"Network/fetched CMake dependency in {name}")
            require(not re.search(r"(?:/Users/|/home/|[A-Za-z]:[\\/])", text), f"Host absolute path in {name}")
        if name.startswith("scripts/") and path.suffix in (".sh", ".py", ".cmake"):
            text = "\n".join(line.split("#", 1)[0] for line in path.read_text(encoding="utf-8").splitlines())
            require(not network_shell.search(text), f"Network/package download in {name}")


def audit_wasm(root, manifest, source_root, source_archive, inventory):
    source_release = manifest.get("sourceRelease")
    require(isinstance(source_release, dict), "WASM release has no companion source archive")
    embedded_source = root / relative_path(source_release.get("path"))
    require(embedded_source.is_file(), "WASM release companion source archive is absent")
    require(embedded_source.stat().st_size == source_release.get("size")
            and digest(embedded_source) == source_release.get("sha256") == digest(source_archive),
            "WASM release companion source archive differs from the audited source ZIP")
    selected = manifest.get("artifacts")
    require(isinstance(selected, list) and selected and len(selected) == len(set(selected))
            and set(selected) <= REQUIRED_ARTIFACTS, "Invalid released WASM artifact list")
    info = read_json(root / "wasm/build-info.json")
    require(info.get("schemaVersion") == 1 and {record["id"] for record in info.get("artifacts", [])} == set(selected),
            "WASM build provenance differs from the released artifacts")
    expected_outputs = set()
    for record in info["artifacts"]:
        recipe = next(item for item in inventory["artifacts"] if item["id"] == record["id"])
        expected_sources = set(recipe["sourceFiles"] + recipe.get("buildFiles", [recipe["buildScript"]]))
        require({item["path"] for item in record["sourceFiles"]} == expected_sources,
                f"{record['id']}: build provenance omitted a source/build input")
        for item in record["sourceFiles"]:
            path = source_root / relative_path(item["path"])
            require(path.is_file() and path.stat().st_size == item.get("size") and digest(path) == item.get("sha256"),
                    f"{record['id']}: build input differs from companion source: {item['path']}")
        fingerprint = hashlib.sha256(json.dumps(record["sourceFiles"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        require(fingerprint == record.get("sourceFingerprint"), f"{record['id']}: source fingerprint mismatch")
        names = {"msfa.wasm"} if recipe["format"] == "standalone-wasm" else {record["id"] + "_wasm.js", record["id"] + "_wasm.wasm"}
        require({item["path"] for item in record["outputs"]} == names, f"{record['id']}: missing WASM output")
        for item in record["outputs"]:
            path = root / "wasm" / relative_path(item["path"])
            require(path.is_file() and path.stat().st_size == item.get("size") and digest(path) == item.get("sha256"),
                    f"{record['id']}: WASM output provenance mismatch: {item['path']}")
        require(record.get("compiler", {}).get("version"), f"{record['id']}: missing compiler provenance")
        expected_outputs.update(names)
    actual_outputs = {path.name for path in (root / "wasm").iterdir() if path.suffix in (".js", ".wasm")}
    require(actual_outputs == expected_outputs, "WASM ZIP contains undeclared or missing executable artifacts")


def command(args, cwd, environment):
    print("+ " + shlex.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=environment, check=True)


def build_native(root, build, environment):
    query = build / ".cmake/api/v1/query"
    query.mkdir(parents=True)
    (query / "codemodel-v2").touch()
    command(["cmake", "-S", root, "-B", build, "-DCMAKE_BUILD_TYPE=Release",
             "-DBUILD_TESTING=ON", "-DTETORICA_NATIVE_BUILD_TESTS=ON",
             "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON",
             "-DCMAKE_FIND_USE_PACKAGE_REGISTRY=OFF", "-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=OFF"], root, environment)
    reply = build / ".cmake/api/v1/reply"
    indices = sorted(reply.glob("index-*.json"))
    require(indices, "Native CMake build has no File API source inventory")
    index = read_json(indices[-1])
    model = read_json(reply / index["reply"]["codemodel-v2"]["jsonFile"])
    targets = [target for configuration in model["configurations"] for target in configuration["targets"]]
    require(targets, "Native CMake build has no targets")
    for target in targets:
        detail = read_json(reply / target["jsonFile"])
        for source in detail.get("sources", []):
            path = Path(source["path"])
            if not path.is_absolute():
                path = (build if source.get("isGenerated") else root) / path
            require(within(path, root) or within(path, build), f"Native target borrows an outside source: {path}")
        for group in detail.get("compileGroups", []):
            for include in group.get("includes", []):
                path = Path(include["path"])
                require(within(path, root) or within(path, build), f"Native target borrows an outside include directory: {path}")
    entries = read_json(build / "compile_commands.json") if (build / "compile_commands.json").is_file() else []
    for entry in entries:
        require(within(Path(entry["file"]), root), f"Native compilation borrows an outside source: {entry['file']}")
        arguments = entry.get("arguments") or shlex.split(entry["command"], posix=os.name != "nt")
        for index, argument in enumerate(arguments):
            value = arguments[index + 1] if argument in ("-I", "-isystem", "/I") else argument[2:] if argument.startswith("-I") else None
            if value:
                include = Path(value.strip('"'))
                if not include.is_absolute():
                    include = Path(entry["directory"]) / include
                require(within(include, root) or within(include, build), f"Native build borrows an outside include directory: {include}")
    command(["cmake", "--build", build, "--config", "Release", "--parallel", "2"], root, environment)
    command(["ctest", "--test-dir", build, "-C", "Release", "--output-on-failure", "--no-tests=error"], root, environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--wasm-zip", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--wasm-smoke", action="store_true", help="Run the released YM2612 Node ABI smoke even with --audit-only")
    parser.add_argument("--build-wasm", metavar="ARTIFACT", help="Also rebuild one WASM artifact using installed Emscripten")
    args = parser.parse_args()
    work = args.work_dir or Path(tempfile.mkdtemp(prefix="tetorica SDK standalone "))
    work.mkdir(parents=True, exist_ok=True)
    require(not any(work.iterdir()), f"Standalone work directory must be empty: {work}")
    root = unpack(args.source_zip.resolve(), work / "source")
    manifest = audit_manifest(root, "source")
    require(root.name == f"{manifest['name']}-{manifest['version']}", "Source ZIP root differs from its release identity")
    catalog, inventory = audit_catalog(root)
    audit_local_sources(root)
    if args.wasm_zip:
        wasm = unpack(args.wasm_zip.resolve(), work / "wasm")
        wasm_manifest = audit_manifest(wasm, "wasm")
        require(wasm_manifest["version"] == manifest["version"], "Source and WASM versions differ")
        audit_wasm(wasm, wasm_manifest, root, args.source_zip.resolve(), inventory)
    environment = os.environ.copy()
    for key in ("CPATH", "CPLUS_INCLUDE_PATH", "C_INCLUDE_PATH", "LIBRARY_PATH", "LD_LIBRARY_PATH",
                "DYLD_LIBRARY_PATH", "CMAKE_PREFIX_PATH", "PKG_CONFIG_PATH", "NODE_PATH"):
        environment.pop(key, None)
    if not args.audit_only:
        build_native(root, work / "native-build", environment)
    if args.wasm_zip and (not args.audit_only or args.wasm_smoke):
        require(shutil.which("node"), "WASM ABI smoke requires Node.js")
        command(["node", root / "tests/wasm_smoke.mjs", wasm / "wasm"], root, environment)
    if args.build_wasm:
        require(shutil.which("em++"), "--build-wasm requires installed Emscripten")
        command(["sh", root / "scripts/build-wasm.sh", args.build_wasm, work / "rebuilt-wasm"], root, environment)
        require(any((work / "rebuilt-wasm").rglob("*.wasm")), "WASM build produced no WASM artifact")
        if args.build_wasm in ("ym2612", "all"):
            command(["node", root / "tests/wasm_smoke.mjs", work / "rebuilt-wasm"], root, environment)
    print(f"PASS: {len(catalog['chips'])} chips and {len(inventory['artifacts'])} WASM artifacts; standalone release at {root}")


if __name__ == "__main__":
    try:
        main()
    except (AuditError, subprocess.CalledProcessError, ValueError, OSError, zipfile.BadZipFile) as error:
        raise SystemExit(f"FAIL: {error}")
