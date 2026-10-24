# Releases and vendoring

## Release artifacts

`scripts/package_release.py` uses the version in `sdk.json` to produce:

- `tetorica-soundchip-native-<version>-sources.zip`: cores, Native reference implementations, WASM bridges, JavaScript ADPCM references and examples, build recipes, catalogs, licenses and tests.
- `tetorica-soundchip-native-<version>-wasm.zip`: the generated artifacts selected through `--wasm-dir`, catalogs, license notices and the matching source ZIP itself.
- `SHA256SUMS`: the SHA-256 digest of each release ZIP.

Each ZIP contains `RELEASE-MANIFEST.json`, recording every payload file's path, SHA-256 and byte size. The WASM manifest also identifies the embedded source ZIP and its hash. Packaging avoids build timestamps and workstation-specific absolute paths; identical inputs produce identical archives.

Source archives include `.gitattributes` and the CI workflow. Git checkout conversion is disabled so Windows preserves the exact upstream bytes recorded in the inventories, including original line endings.

Previously imported WASM binaries have provenance records in `source_inventory.json`, such as `imported-reference-binary`. Import provenance alone does not establish that a binary was rebuilt from the SDK snapshot. The initial WASM release selects only YM2612, freshly compiled into `build/verified-wasm`.

Original Tetorica code uses BSD-3-Clause. Retain the license files, notices and existing explicit component licenses when vendoring either archive; [LICENSES.md](../LICENSES.md) describes the exceptions.

## Adopting a release

1. Obtain the source and, if needed, WASM ZIPs and verify them against `SHA256SUMS`.
2. From an extracted source package or SDK checkout, run the standalone release checker:

   ```sh
   python3 tests/check_standalone_release.py --source-zip <sources.zip>
   ```

   The normal verification builds both standalone Native libraries, YM2612 and YM2151, requires both CTest fixtures, and runs the JavaScript reference smoke using Node.js 22 or newer. Add `--wasm-zip <wasm.zip>` to audit the matching WASM release and run its Node ABI smoke test. See [tests/README.md](../tests/README.md) for tool requirements and optional rebuilds.

3. Vendor the required contents under a path such as `vendor/tetorica-soundchip-native/`, retaining licenses, notices, catalogs and the manifest. Importing the complete source archive is the simplest starting point for Native integration.
4. Record the SDK version, original archive SHA-256, selected chip and engine, and any downstream patches.
5. Build against the vendored files. Import another release only when intentionally updating the dependency.

The Native CMake targets are `tetorica::ym2612` and `tetorica::ym2151`, backed by `tetorica_native_ym2612` and `tetorica_native_ym2151`. Their public C++ headers are `<tetorica/ym2612.hpp>` and `<tetorica/ym2151.hpp>`. Choose the targets your host uses; the source archive contains both and the current reference ABIs. See the [Native guide](../native/README.md) for integration examples and scope.

Publishing a new SDK release does not update a consumer's pinned version. Normal builds and CI do not need to fetch sound-chip sources from GitHub, npm or an adjacent checkout. Consumers supply their compilers and other development tools.

## Incorporating application changes

1. Develop and verify a change in the `tetorica-fm2612` source repository or Playground Tauri, then select the revision to import.
2. Include the required cores, bridges and original license notices, recording their origins and hashes in the catalogs.
3. Update the [chip-specific differences](chip-differences.md): upstream adaptations, changes made during import and Native/WASM differences. Preserve shared and Native-specific implementations where they serve different requirements.
4. Run standalone SDK builds and tests, recording the verified chips and backends together with the remaining limits.
5. Update the SDK version and release archives. Consumers can adopt the new release separately.

Keep three verification states distinct: source is included, source works in its original application, and source has been built and tested independently through this SDK.

## Continuous verification

[Verify SDK](../.github/workflows/verify-sdk.yml) runs for every push, pull request, and manual dispatch. It has five Native jobs: Linux GCC on x64 and ARM64, Windows MSVC, and macOS Clang on Intel and Apple Silicon. Each packages a fresh source ZIP, extracts it under the runner's temporary directory, builds both YM2612 and YM2151 in the Release configuration, runs both CTest fixtures, and executes the JavaScript reference smoke. CMake File API and compiler-command checks enforce that project sources and explicit includes come from the extracted SDK. Build diagnostics are retained as per-platform artifacts. Consult the [verification record](verification.md) for completed runs; adding a target to the matrix does not itself establish platform success.

The Ubuntu WASM job installs the fixed Emscripten 6.0.6 toolchain, compiles YM2612, and packages its artifacts with the exact matching source ZIP. It verifies hashes and the synchronous Node ABI, then recompiles YM2612 from the independently extracted source archive and repeats the smoke. Verified archives and compiler/input/output records are uploaded as workflow artifacts; the workflow does not publish GitHub releases.

Compilers, Python 3.12, and Node.js 22 are CI tool dependencies. Chip sources come from the SDK checkout/archive. Native targets beyond YM2612/YM2151, the X68000 OKIM6258 integration, and the remaining WASM recipes are outside this workflow's compilation scope.

The MSM5205 and OKIM6295 entries under `javascriptReferences` are executable JavaScript snapshots, not Native or WASM artifacts. Include `reference/javascript/` and its component notices when selecting these sources. The packager includes them in the source ZIP; archive audits check both their presence and their explicit `not-ported` backend status.

## Next adoption step

The first planned application dependency switch is YM2612. Compare its existing output and build before migrating other Native targets and adapters. Package renaming and a complete API redesign are separate from this initial extraction and release workflow.
