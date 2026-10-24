"""Regression tests for release isolation and provenance checks; no compiler needed."""
import hashlib
import json
import copy
import importlib.util
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

from check_standalone_release import (AuditError, REQUIRED_ARTIFACTS, REQUIRED_CHIPS,
                                      REQUIRED_JAVASCRIPT_REFERENCES, REQUIRED_UPSTREAM_REFERENCES, audit_catalog,
                                      audit_local_sources, audit_manifest,
                                      audit_wasm, relative_path, unpack)


class ReleaseAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.root = self.work / "sdk"
        self.root.mkdir()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        return path

    def fixture(self):
        self.write("sdk.json", json.dumps({"name": "tetorica-soundchip-native", "version": "0.1.0"}))
        source = self.write("vendor/core.cpp", "int sound_chip() { return 1; }\n")
        self.write("vendor/LICENSE", "BSD-3-Clause fixture license\n")
        self.write("scripts/build-wasm.sh", "#!/bin/sh\nset -eu\nem++ vendor/core.cpp -o result.js\n")
        references = {"sourceFiles": ["vendor/core.cpp"], "licenseFiles": ["vendor/LICENSE"]}
        javascript = []
        javascript_components = []
        self.write("reference/javascript/package.json", '{"type":"module","private":true}\n')
        for identifier in sorted(REQUIRED_JAVASCRIPT_REFERENCES):
            entry = f"reference/javascript/{identifier}audioengine.js"
            path = self.write(entry, f"export const referenceId = '{identifier}';\n")
            license_file = f"vendor/{identifier}/LICENSE"
            self.write(license_file, "BSD-3-Clause JavaScript fixture license\n")
            record = {"id": identifier, "format": "javascript-es-module", "entryPoint": entry,
                      "sourceFiles": [entry], "licenseFiles": [license_file],
                      "native": {"status": "not-ported"}, "wasm": {"status": "not-ported"}}
            javascript.append(record)
            javascript_components.append({"id": identifier, "sourceFiles": [entry], "licenseFiles": [license_file],
                                          "files": [{"path": entry, "originPath": f"web/{identifier}audioengine.js",
                                                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]})
        upstream = []
        upstream_components = []
        for identifier in sorted(REQUIRED_UPSTREAM_REFERENCES):
            directory = f"vendor/{identifier}/upstream"
            entry = f"{directory}/core.c"
            path = self.write(entry, '/* BSD-3-Clause upstream source fixture */\n#include "support.h"\n')
            license_file = f"{directory}/LICENSE"
            notice = self.write(license_file, "BSD-3-Clause upstream fixture license\n")
            files = [{"path": "core.c", "upstreamPath": "emu/core.c", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
                     {"path": "LICENSE", "upstreamPath": "LICENSE", "sha256": hashlib.sha256(notice.read_bytes()).hexdigest()}]
            snapshot = {"repository": "https://example.invalid/upstream", "commit": "a" * 40,
                        "role": "upstream-source-reference", "files": files,
                        "buildStatus": "reference-only; framework dependencies omitted",
                        "omittedDependencies": [{"path": "support.h", "reason": "fixture dependency not included"}]}
            manifest_name = f"{directory}/snapshot-manifest.json"
            manifest_path = self.write(manifest_name, json.dumps(snapshot))
            record = {key: snapshot[key] for key in ("repository", "commit", "role", "buildStatus", "omittedDependencies")}
            record.update({"id": identifier, "snapshotManifest": manifest_name,
                           "sourceFiles": [entry], "licenseFiles": [license_file],
                           "sdkIntegration": {"native": "not-integrated", "wasm": "not-integrated"}})
            upstream.append(record)
            upstream_components.append({"id": identifier, "sourceFiles": [entry], "licenseFiles": [license_file],
                "files": [{"path": f"{directory}/{item['path']}", "originPath": item["upstreamPath"], "sha256": item["sha256"]} for item in files]
                    + [{"path": manifest_name, "originPath": "snapshot-manifest.json", "sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}]})
        catalog = {"schemaVersion": 1, "chips": [{"id": chip, **references} for chip in sorted(REQUIRED_CHIPS)],
                   "javascriptReferences": copy.deepcopy(javascript), "upstreamReferences": copy.deepcopy(upstream)}
        self.write("catalog/chips.json", json.dumps(catalog))
        inventory = {"schemaVersion": 1, "components": [{"id": "core", **references,
                     "files": [{"path": "vendor/core.cpp", "originPath": "src/core.cpp", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]}, *javascript_components, *upstream_components],
                     "javascriptReferences": copy.deepcopy(javascript),
                     "upstreamReferences": copy.deepcopy(upstream),
                     "artifacts": [{"id": artifact, "chipIds": sorted(REQUIRED_CHIPS), **references,
                                    "format": "emscripten-es-module", "buildScript": "scripts/build-wasm.sh"} for artifact in sorted(REQUIRED_ARTIFACTS)]}
        self.write("catalog/source_inventory.json", json.dumps(inventory))
        self.write("catalog/native_inventory.json", json.dumps({"schemaVersion": 1, "chips": [
            {"id": chip, "sourceFiles": ["vendor/core.cpp"], "status": "source-only"} for chip in sorted(REQUIRED_CHIPS)]}))
        self.write("native/reference/SOURCES.json", json.dumps({"schemaVersion": 1, "entries": [
            {"file": "vendor/core.cpp", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]}))
        return catalog, inventory

    def save_catalogs(self, catalog, inventory):
        self.write("catalog/chips.json", json.dumps(catalog))
        self.write("catalog/source_inventory.json", json.dumps(inventory))

    def manifest(self):
        files = {}
        for path in self.root.rglob("*"):
            if path.is_file() and path != self.root / "RELEASE-MANIFEST.json":
                files[path.relative_to(self.root).as_posix()] = {"size": path.stat().st_size,
                                                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        value = {"schemaVersion": 1, "name": "tetorica-soundchip-native", "version": "0.1.0", "kind": "source", "files": files}
        self.write("RELEASE-MANIFEST.json", json.dumps(value))

    def test_valid_manifest_and_every_catalog_source_and_license_can_be_followed(self):
        self.fixture()
        self.manifest()
        audit_manifest(self.root, "source")
        audit_catalog(self.root)
        audit_local_sources(self.root)

    def test_unsafe_paths_are_rejected(self):
        for name in ("../other", "/absolute", "C:/other", "a\\b", "a/../b", "a/./b", "a//b", ""):
            with self.subTest(name=name), self.assertRaises(AuditError):
                relative_path(name)

    def test_zip_traversal_is_rejected_before_any_member_is_extracted(self):
        archive = self.work / "bad.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("sdk/good.txt", "not yet extracted")
            output.writestr("sdk/../../outside.txt", "outside")
        with self.assertRaisesRegex(AuditError, "escapes"):
            unpack(archive, self.work / "unpacked")
        self.assertFalse((self.work / "unpacked").exists())
        self.assertFalse((self.work / "outside.txt").exists())

    def test_zip_symlink_is_rejected(self):
        archive = self.work / "link.zip"
        link = zipfile.ZipInfo("sdk/vendor/core.cpp")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(link, "../../checkout/core.cpp")
        with self.assertRaisesRegex(AuditError, "Symlink"):
            unpack(archive, self.work / "unpacked")

    def test_zip_multiple_roots_are_rejected(self):
        archive = self.work / "roots.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("sdk/core.cpp", "core")
            output.writestr("another/LICENSE", "license")
        with self.assertRaisesRegex(AuditError, "one SDK root"):
            unpack(archive, self.work / "unpacked")

    def test_same_size_source_tampering_breaks_hash(self):
        self.write("vendor/core.cpp", "one")
        self.manifest()
        self.write("vendor/core.cpp", "two")
        with self.assertRaisesRegex(AuditError, "SHA-256"):
            audit_manifest(self.root, "source")

    def test_missing_and_unlisted_files_are_rejected(self):
        self.write("LICENSE", "license")
        self.manifest()
        self.write("unlisted.cpp", "unlisted")
        with self.assertRaisesRegex(AuditError, "unlisted.cpp"):
            audit_manifest(self.root, "source")
        (self.root / "unlisted.cpp").unlink()
        (self.root / "LICENSE").unlink()
        with self.assertRaisesRegex(AuditError, "LICENSE"):
            audit_manifest(self.root, "source")

    def test_nested_manifest_named_file_is_still_hashed(self):
        self.write("vendor/RELEASE-MANIFEST.json", "component manifest")
        self.manifest()
        audit_manifest(self.root, "source")
        self.write("vendor/RELEASE-MANIFEST.json", "modified component")
        with self.assertRaises(AuditError):
            audit_manifest(self.root, "source")

    def test_missing_or_empty_license_is_rejected(self):
        self.fixture()
        self.write("vendor/LICENSE", "")
        with self.assertRaisesRegex(AuditError, "empty license"):
            audit_catalog(self.root)
        (self.root / "vendor/LICENSE").unlink()
        with self.assertRaisesRegex(AuditError, "licenseFiles"):
            audit_catalog(self.root)

    def test_public_chip_cannot_silently_disappear_from_both_catalogs(self):
        catalog, inventory = self.fixture()
        catalog["chips"] = [chip for chip in catalog["chips"] if chip["id"] != "y8950"]
        inventory["artifacts"][0]["chipIds"].remove("y8950")
        self.write("catalog/chips.json", json.dumps(catalog))
        self.write("catalog/source_inventory.json", json.dumps(inventory))
        with self.assertRaisesRegex(AuditError, "Public chip catalog changed.*y8950"):
            audit_catalog(self.root)

    def test_origin_inventory_hash_matches_packaged_source_bytes(self):
        self.fixture()
        self.write("vendor/core.cpp", "different source")
        with self.assertRaisesRegex(AuditError, "Imported source hash mismatch"):
            audit_catalog(self.root)

    def test_non_public_wasm_artifact_sources_cannot_silently_disappear(self):
        _, inventory = self.fixture()
        inventory["artifacts"] = [item for item in inventory["artifacts"] if item["id"] != "ym3438"]
        self.write("catalog/source_inventory.json", json.dumps(inventory))
        with self.assertRaisesRegex(AuditError, "artifact inventory changed.*ym3438"):
            audit_catalog(self.root)

    def test_javascript_reference_cannot_disappear_from_both_catalogs(self):
        catalog, inventory = self.fixture()
        for document in (catalog, inventory):
            document["javascriptReferences"] = [record for record in document["javascriptReferences"] if record["id"] != "msm5205"]
        self.write("catalog/chips.json", json.dumps(catalog))
        self.write("catalog/source_inventory.json", json.dumps(inventory))
        with self.assertRaisesRegex(AuditError, "JavaScript reference inventory changed"):
            audit_catalog(self.root)

    def test_javascript_catalogs_must_agree_on_source_and_backend_metadata(self):
        catalog, _ = self.fixture()
        catalog["javascriptReferences"][0]["native"]["status"] = "verified"
        self.write("catalog/chips.json", json.dumps(catalog))
        with self.assertRaisesRegex(AuditError, "differ between the two catalogs"):
            audit_catalog(self.root)

    def test_javascript_only_reference_cannot_claim_a_native_or_wasm_port(self):
        for backend in ("native", "wasm"):
            with self.subTest(backend=backend):
                catalog, inventory = self.fixture()
                for document in (catalog, inventory):
                    document["javascriptReferences"][0][backend]["status"] = "verified"
                self.write("catalog/chips.json", json.dumps(catalog))
                self.write("catalog/source_inventory.json", json.dumps(inventory))
                with self.assertRaisesRegex(AuditError, f"must remain {backend} not-ported"):
                    audit_catalog(self.root)

    def test_javascript_entry_point_must_be_present_and_provenanced(self):
        catalog, inventory = self.fixture()
        inventory["components"] = [record for record in inventory["components"] if record["id"] != "msm5205"]
        self.write("catalog/source_inventory.json", json.dumps(inventory))
        with self.assertRaisesRegex(AuditError, "JavaScript source missing from hash provenance"):
            audit_catalog(self.root)
        self.fixture()
        (self.root / "reference/javascript/msm5205audioengine.js").unlink()
        with self.assertRaisesRegex(AuditError, "msm5205audioengine.js"):
            audit_catalog(self.root)

    def test_javascript_source_tampering_breaks_imported_source_hash(self):
        self.fixture()
        self.write("reference/javascript/msm5205audioengine.js", "export const modified = true;\n")
        with self.assertRaisesRegex(AuditError, "Imported source hash mismatch.*msm5205"):
            audit_catalog(self.root)

    def test_javascript_reference_license_must_be_present(self):
        self.fixture()
        (self.root / "vendor/msm5205/LICENSE").unlink()
        with self.assertRaisesRegex(AuditError, "missing/outside licenseFiles.*msm5205"):
            audit_catalog(self.root)

    def test_upstream_reference_cannot_disappear_from_both_catalogs(self):
        catalog, inventory = self.fixture()
        for document in (catalog, inventory):
            document["upstreamReferences"].pop()
        self.save_catalogs(catalog, inventory)
        with self.assertRaisesRegex(AuditError, "upstream reference inventory changed"):
            audit_catalog(self.root)

    def test_upstream_catalogs_must_agree(self):
        catalog, inventory = self.fixture()
        catalog["upstreamReferences"][0]["commit"] = "b" * 40
        self.save_catalogs(catalog, inventory)
        with self.assertRaisesRegex(AuditError, "Upstream references differ"):
            audit_catalog(self.root)

    def test_upstream_reference_requires_full_immutable_commit(self):
        for commit in ("master", "a" * 39, "A" * 40):
            with self.subTest(commit=commit):
                catalog, inventory = self.fixture()
                for document in (catalog, inventory):
                    document["upstreamReferences"][0]["commit"] = commit
                self.save_catalogs(catalog, inventory)
                with self.assertRaisesRegex(AuditError, "full immutable upstream commit"):
                    audit_catalog(self.root)

    def test_upstream_reference_cannot_claim_an_sdk_runtime_port(self):
        for backend in ("native", "wasm"):
            with self.subTest(backend=backend):
                catalog, inventory = self.fixture()
                for document in (catalog, inventory):
                    document["upstreamReferences"][0]["sdkIntegration"][backend] = "verified"
                self.save_catalogs(catalog, inventory)
                with self.assertRaisesRegex(AuditError, "must not claim an SDK runtime port"):
                    audit_catalog(self.root)

    def test_upstream_source_and_manifest_require_hash_provenance(self):
        for source_name in ("core.c", "snapshot-manifest.json"):
            with self.subTest(source=source_name):
                catalog, inventory = self.fixture()
                reference = inventory["upstreamReferences"][0]
                component = next(item for item in inventory["components"] if item["id"] == reference["id"])
                component["files"] = [item for item in component["files"] if not item["path"].endswith("/" + source_name)]
                self.save_catalogs(catalog, inventory)
                with self.assertRaisesRegex(AuditError, "upstream (source|manifest) missing from hash provenance"):
                    audit_catalog(self.root)

    def test_upstream_source_tampering_is_rejected(self):
        _, inventory = self.fixture()
        self.write(inventory["upstreamReferences"][0]["sourceFiles"][0], "modified upstream source\n")
        with self.assertRaisesRegex(AuditError, "Imported source hash mismatch"):
            audit_catalog(self.root)

    def test_upstream_snapshot_cannot_hide_unlisted_sources(self):
        _, inventory = self.fixture()
        reference = inventory["upstreamReferences"][0]
        directory = Path(reference["snapshotManifest"]).parent
        self.write((directory / "unlisted.h").as_posix(), "/* unlisted */\n")
        with self.assertRaisesRegex(AuditError, "snapshot files differ from manifest"):
            audit_catalog(self.root)

    def test_upstream_dependency_limitations_must_be_preserved(self):
        catalog, inventory = self.fixture()
        for document in (catalog, inventory):
            document["upstreamReferences"][0].pop("omittedDependencies")
        self.save_catalogs(catalog, inventory)
        with self.assertRaisesRegex(AuditError, "manifest omittedDependencies differs"):
            audit_catalog(self.root)

    def test_upstream_reference_may_omit_documented_framework_dependencies(self):
        _, inventory = self.fixture()
        for reference in inventory["upstreamReferences"]:
            self.assertFalse((self.root / reference["snapshotManifest"]).parent.joinpath("support.h").exists())
        audit_catalog(self.root)
        audit_local_sources(self.root)

    def test_catalog_refresh_keeps_upstream_references_and_source_bytes(self):
        _, inventory = self.fixture()
        project = Path(__file__).resolve().parents[1]
        for filename in ("sdk_common.py", "refresh_catalog.py"):
            shutil.copyfile(project / "scripts" / filename, self.root / "scripts" / filename)
        originals = {record["path"]: (self.root / record["path"]).read_bytes()
                     for component in inventory["components"] for record in component["files"]}
        subprocess.run([sys.executable, self.root / "scripts/refresh_catalog.py"], check=True, capture_output=True)
        catalog = json.loads((self.root / "catalog/chips.json").read_text())
        self.assertEqual(catalog["upstreamReferences"], inventory["upstreamReferences"])
        self.assertEqual(len(catalog["chips"]), 22)
        for filename, content in originals.items():
            self.assertEqual((self.root / filename).read_bytes(), content)
        audit_catalog(self.root)
        spec = importlib.util.spec_from_file_location("fixture_sdk_common", self.root / "scripts/sdk_common.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.check_collection(self.root)["upstreamReferences"], 3)

    def test_parent_and_absolute_cpp_includes_are_rejected(self):
        for include in ('"../../outside.h"', '"..\\..\\outside.h"', '"/Users/developer/checkout/core.h"', '"C:/checkout/core.h"'):
            with self.subTest(include=include):
                self.write("vendor/core.cpp", f"#include {include}\n")
                with self.assertRaises(AuditError):
                    audit_local_sources(self.root)

    def test_internal_relative_include_is_allowed(self):
        self.write("vendor/core.cpp", '#include "../wasm/interface.h"\n')
        self.write("wasm/interface.h", "#pragma once\n")
        audit_local_sources(self.root)

    def test_cmake_and_shell_cannot_fetch_a_missing_checkout(self):
        for text in ('FetchContent_Declare(core URL https://example.invalid/core.zip)',
                     'ExternalProject_Add(core GIT_REPOSITORY https://example.invalid/core)',
                     'file(DOWNLOAD https://example.invalid/core core.cpp)'):
            with self.subTest(text=text):
                self.write("CMakeLists.txt", text)
                with self.assertRaisesRegex(AuditError, "Network/fetched CMake"):
                    audit_local_sources(self.root)
        (self.root / "CMakeLists.txt").unlink()
        self.write("scripts/build-wasm.sh", "curl https://example.invalid/core.cpp -o core.cpp\n")
        with self.assertRaisesRegex(AuditError, "Network/package download"):
            audit_local_sources(self.root)

    def wasm_fixture(self):
        _, inventory = self.fixture()
        wasm = self.work / "wasm"
        (wasm / "wasm").mkdir(parents=True)
        (wasm / "sources").mkdir()
        archive = self.work / "sources.zip"
        archive.write_bytes(b"companion source fixture")
        (wasm / "sources/sources.zip").write_bytes(archive.read_bytes())
        manifest = {"artifacts": ["ym2612"], "sourceRelease": {"path": "sources/sources.zip", "size": archive.stat().st_size,
                    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}}
        source_files = [{"path": name, "size": (self.root / name).stat().st_size,
                         "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}
                        for name in ("scripts/build-wasm.sh", "vendor/core.cpp")]
        outputs = []
        for name in ("ym2612_wasm.js", "ym2612_wasm.wasm"):
            file = wasm / "wasm" / name
            file.write_bytes(b"fixture output")
            outputs.append({"path": name, "size": file.stat().st_size, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
        info = {"schemaVersion": 1, "artifacts": [{"id": "ym2612", "sourceFiles": source_files, "outputs": outputs,
                "sourceFingerprint": hashlib.sha256(json.dumps(source_files, separators=(",", ":")).encode()).hexdigest(),
                "compiler": {"version": "fixture compiler"}}]}
        (wasm / "wasm/build-info.json").write_text(json.dumps(info))
        return wasm, manifest, archive, inventory

    def test_wasm_release_has_matching_companion_source_and_build_inputs(self):
        wasm, manifest, archive, inventory = self.wasm_fixture()
        audit_wasm(wasm, manifest, self.root, archive, inventory)
        self.write("vendor/core.cpp", "different companion source")
        with self.assertRaisesRegex(AuditError, "build input differs"):
            audit_wasm(wasm, manifest, self.root, archive, inventory)

    def test_wasm_release_cannot_embed_a_different_source_archive(self):
        wasm, manifest, archive, inventory = self.wasm_fixture()
        (wasm / "sources/sources.zip").write_bytes(b"wrong source archive")
        with self.assertRaisesRegex(AuditError, "companion source archive differs"):
            audit_wasm(wasm, manifest, self.root, archive, inventory)

    def test_wasm_release_cannot_include_undeclared_executables(self):
        wasm, manifest, archive, inventory = self.wasm_fixture()
        (wasm / "wasm/another_chip.wasm").write_bytes(b"not declared")
        with self.assertRaisesRegex(AuditError, "undeclared"):
            audit_wasm(wasm, manifest, self.root, archive, inventory)


if __name__ == "__main__":
    unittest.main()
