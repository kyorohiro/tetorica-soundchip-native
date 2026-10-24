# tetorica-soundchip-native

Tetorica で使用する音源コア、Native / WASM の接続コード、ビルド手順を、必要なソースとライセンスを含めて配布するリポジトリです。

利用側は**バージョンと SHA-256 を固定した配布 ZIP を取り込み、その内容を自分のリポジトリで保管**します。submodule、別リポジトリの checkout、ビルド中の GitHub アクセスは必要ありません。上流の URL は出典の記録です。

## 現在の段階

初期集約版です。Playground の追加生成で扱う **22 種類**のソースと Native の既存接続コードを収録しました。種類ごとのソース・ライセンス・ビルド状況は [catalog/chips.json](catalog/chips.json) を参照してください。

一部の Native 接続原本は、取り込み元でライセンスが未記載でした。[未確定箇所](LICENSES.md#native-接続原本の未確定箇所)を記録し、コアのライセンスから推定していません。現段階は公開前の整理・検証用です。

Native の独立 CMake target は、まず **YM2612（ymfm）** を提供します。他の Native 接続コードは `native/reference/` の移行用原本で、まだこの SDK 単独のビルド target にはなっていません。WASM は既存のビルド手順を収録し、代表の YM2612 を独立ビルドで検証します。ソース収録とビルド検証済みを区別しています。

既存の `tetorica-fm2612` と Playground Tauri は、まだこの配布物へ切り替えていません。JS の Synth / AudioWorklet と、Rust のスケジューラー・CPAL・音声デバイス処理は、それぞれ利用側が管理します。

## Native をビルドする

必要なものは CMake 3.20 以上と C++14 コンパイラーです。依存ソースのダウンロードは行いません。

```sh
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native -C Release --output-on-failure
```

利用側の CMake から `add_subdirectory()` し、`tetorica::ym2612` にリンクできます。[Native の API と制約](native/README.md)を参照してください。

## WASM をビルドする

ローカルにインストールした Emscripten と Node.js を使用します。Node.js はビルド記録の作成と生成物の検証に使用します。

```sh
sh scripts/build-wasm.sh ym2612 build/verified-wasm
```

生成された Emscripten の `.js` と `.wasm` は一緒に取り込みます。同期的な register read / PCM generate を含む従来の低レベル C ABI を維持します。Native と WASM の公開 API 全体を統一する作業は別段階です。

## 配布物を作る・検証する

```sh
python3 scripts/check_sdk.py
python3 scripts/package_release.py --out-dir releases --wasm-dir build/verified-wasm
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip
```

source ZIP はソース・ビルド手順・出典・ライセンス・試験を含みます。WASM ZIP は指定ディレクトリの生成物と、それに対応する source ZIP 自体を含みます。両方にファイルごとの SHA-256 を記録します。`--wasm-dir` を省略すれば source ZIP だけを作ります。

[配布と取り込みの手順](docs/releases.md) / [責務と移行方針](docs/architecture.md) / [検証記録](docs/verification.md) / [ライセンスの案内](LICENSES.md)
