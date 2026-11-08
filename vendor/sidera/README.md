# sidera 1.1.1 in the optional SID 8580 instrument

This SDK adopts the already marked Tetorica adaptation of MIT-licensed
[sidera](https://codeberg.org/sbechet/sidera), revision
`15041709d26c2bc36667ba27f729332c9f523696`, published crate 1.1.1.
The original 28 crate files remain unchanged under `upstream/`.
[SOURCES.json](SOURCES.json) records their hashes and the original archive
SHA-256 `b043512b891bdb03ad21b0205723dabb88ada23e3043c21f6a7f88b26defba35`.
The original [MIT license](LICENSE) remains in both source copies.

`adapted/src/` preserves the parent's marked adaptation, byte for byte.
[PATCHES.json](PATCHES.json) records the two changed library files: access to
one existing chip cycle and independent optional resonance/cutoff research
profiles. Both profiles stay **Off by default**. Their coefficients, derivation
and limitations remain in the adjacent calibration JSON files. No new DSP
change is made by this SDK integration.

Only the library at `adapted/src/lib.rs` and its direct Rust modules compile.
No optional player, Cargo dependencies, C64 CPU, ROM, game music, recorded PCM,
GPL reference emulator or device API is linked. Original player/example sources
are retained for provenance; their presence does not add a player to the SDK.
Combined waves, filter curves and bus decay remain approximations. Native/WASM
agreement verifies this port, not physical-chip fidelity or analogue variation.

The exact CPU-free batch adapter and current build/use guide are in
[../tetorica-sid8580/](../tetorica-sid8580/README.md). The parent checkout's older
research notes remain verbatim in [ORIGIN.md](ORIGIN.md), for historical context;
its parent-only commands and former adoption status do not describe this SDK.

[toolchain-notices/](toolchain-notices/README.md) retains complete standard-library
notices from the checked Rust 1.91.1 toolchain. Consumers using another toolchain
must retain the corresponding notices for that distribution. No reference-engine
code is included by these standard-library notices.
