# Releases and vendoring

## Release artifacts

`scripts/package_release.py` uses the version in `sdk.json` to produce:

- `tetorica-soundchip-native-<version>-sources.zip`: cores, Native reference implementations, WASM bridges, build recipes, catalogs, licenses and tests.
- `tetorica-soundchip-native-<version>-wasm.zip`: the generated artifacts selected through `--wasm-dir`, catalogs, license notices and the matching source ZIP itself.
- `SHA256SUMS`: the SHA-256 digest of each release ZIP.

Each ZIP contains `RELEASE-MANIFEST.json`, recording every payload file's path, SHA-256 and byte size. The WASM manifest also identifies the embedded source ZIP and its hash. Packaging avoids build timestamps and workstation-specific absolute paths; identical inputs produce identical archives.

Previously imported WASM binaries have provenance records in `source_inventory.json`, such as `imported-reference-binary`. Import provenance alone does not establish that a binary was rebuilt from the SDK snapshot. The initial WASM release selects only YM2612, freshly compiled into `build/verified-wasm`.

Original Tetorica code uses BSD-3-Clause. Retain the license files, notices and existing explicit component licenses when vendoring either archive; [LICENSES.md](../LICENSES.md) describes the exceptions.

## Adopting a release

1. Obtain the source and, if needed, WASM ZIPs and verify them against `SHA256SUMS`.
2. From an extracted source package or SDK checkout, run the standalone release checker:

   ```sh
   python3 tests/check_standalone_release.py --source-zip <sources.zip>
   ```

   Add `--wasm-zip <wasm.zip>` to audit the matching WASM release and run its Node ABI smoke test. See [tests/README.md](../tests/README.md) for tool requirements and optional rebuilds.

3. Vendor the required contents under a path such as `vendor/tetorica-soundchip-native/`, retaining licenses, notices, catalogs and the manifest. Importing the complete source archive is the simplest starting point for Native integration.
4. Record the SDK version, original archive SHA-256, selected chip and engine, and any downstream patches.
5. Build against the vendored files. Import another release only when intentionally updating the dependency.

Publishing a new SDK release does not update a consumer's pinned version. Normal builds and CI do not need to fetch sound-chip sources from GitHub, npm or an adjacent checkout. Consumers supply their compilers and other development tools.

## Incorporating application changes

1. Develop and verify a change in the `tetorica-fm2612` source repository or Playground Tauri, then select the revision to import.
2. Include the required cores, bridges and original license notices, recording their origins and hashes in the catalogs.
3. Update the [chip-specific differences](chip-differences.md): upstream adaptations, changes made during import and Native/WASM differences. Preserve shared and Native-specific implementations where they serve different requirements.
4. Run standalone SDK builds and tests, recording the verified chips and backends together with the remaining limits.
5. Update the SDK version and release archives. Consumers can adopt the new release separately.

Keep three verification states distinct: source is included, source works in its original application, and source has been built and tested independently through this SDK.

## Next adoption step

The first planned application dependency switch is YM2612. Compare its existing output and build before migrating other Native targets and adapters. Package renaming and a complete API redesign are separate from this initial extraction and release workflow.
