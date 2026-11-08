# Pinned chips / m6581

The zlib-licensed 6581 core is pinned to
[floooh/chips](https://github.com/floooh/chips), revision
`9e88298ce56319953ac7a43213a1120359f7a3a6`. The header credits Andre Weissflog
and Attila Grosz (tedplay). `upstream/m6581.h` and `LICENSE` are unmodified.
`PROVENANCE.json` records their SHA-256 hashes and the compiled adapted header.

`m6581.h` is the exact adaptation already used by Tetorica's browser SID engine.
[PATCHES.md](PATCHES.md) describes its seven marked changes. Reconstruct or verify
it without a parent checkout or network access:

```sh
python3 vendor/chips-m6581/prepare.py --check
# To reconstruct: python3 vendor/chips-m6581/prepare.py
```

The historical parent README is retained as `upstream/TETORICA_README.md`; its
application-relative links and statements about SDK membership describe that
older checkout, rather than this SDK. Current integration and limitations are
documented in [the SID host README](../tetorica-sid/README.md).
