# Changelog

## 0.1.0 — Initial SDK

- Collect source cores and existing Native C++ bridges for all 22 chips supported by Playground's additional-instance API.
- Consolidate shared ymfm sources and add chip catalogs, component licenses, origins and SHA-256 inventories.
- Add a standalone Native YM2612 CMake target and automated PCM tests. Retain other Native implementations as reference sources for subsequent integration.
- Add WASM build recipes, versioned source/WASM release archives and verification from independently extracted packages.
- Preserve existing npm and Playground Tauri dependency paths during the initial extraction; adopting SDK releases is a separate integration step.
- Document upstream adaptations, import changes and Native/WASM differences for all 22 chips and additional WASM artifacts, including six MSFA Native differences and the pending Game Boy Native header adaptation.
- Document the workflow for incorporating changes verified in the application repositories and distributing pinned SDK snapshots.
- License original Tetorica code under BSD-3-Clause, retaining third-party licenses and existing explicit file-level terms.
- Include the Analyzer's unchanged MSM5205 and OKIM6295 JavaScript references, BSD notices, provenance, a standalone synthetic-data WAV example, and source-archive verification. Record them separately from Native targets and WASM recipes.
- Collect separately pinned, BSD-declared upstream MSM5205/OKIM6295/ADPCM C/C++ originals with per-file hashes. Document missing framework dependencies and omit libvgm support/player files without explicit licenses; retain the JavaScript engines and existing build targets unchanged.
