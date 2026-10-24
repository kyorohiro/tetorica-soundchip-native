# 初期集約の検証記録

2026-10-24、macOS のローカルコンパイラーで実施。Windows / Linux / ARM の実行確認や、全音源の独立 target 完成を示す記録ではありません。

## ソースと配布

`scripts/check_sdk.py` で、22 Playground ID、27 WASM recipe、229 個の取り込みファイルの SHA-256 と source / license 参照を確認しました。音源コアと Native 接続原本は元のデータを保持し、配置変更した include は出典原票に記録しています。

source / WASM ZIP を元リポジトリ外へ展開し、全 payload と manifest の一致、hash / size、安全な相対パス、出典カタログ、内包する source ZIP の一致を検査しています。CMake File API と compile_commands に、展開先以外の project source / include が含まれないことも確認します。

```sh
python3 scripts/check_sdk.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/package_release.py --out-dir releases --wasm-dir build/verified-wasm
python3 tests/check_standalone_release.py \
  --source-zip releases/tetorica-soundchip-native-0.1.0-sources.zip \
  --wasm-zip releases/tetorica-soundchip-native-0.1.0-wasm.zip \
  --build-wasm ym2612
```

コンパイラーと Node.js / Python / CMake はローカルの開発ツールを使用します。音源ソースや別アプリの checkout をダウンロードしません。ライセンス未記載箇所の利用条件は、この機械的検査で確定したものではありません。

## YM2612

- SDK 内および独立展開先の Native Release ビルド・CTest が成功。
- Native fixture は独立インスタンス、6FM、DAC、timer / status / IRQ、read、観測、clock、Stop / reset、mute、audition、source 取消しを検査。render 中の C++ new / delete が0回。
- SDK の Native fixture を既存アプリ側の実WASM比較へ渡した統合検証では、198 ケース・1,216,512 ステレオフレーム、status / IRQ / read が差分0。この大規模比較は元アプリ側の checker で実施。
- SDK のみの source と手順で Emscripten ビルドが成功。配布対象はこの新規生成物。`build-info.json` に compiler、source / output の hash を記録。
- 配布WASMと独立展開先で再ビルドしたWASMの両方で、Node から同期 read / status、有限で発音する stereo PCM、reset、save / load 後の PCM 完全一致を確認。

配布監査ツール自体の regression test は18件成功しました。最終 ZIP の内包ソースから監査と Node ABI smoke を再実行しています。

Emscripten の最適化時に、既存 ymfm のテンプレートで array-bounds warning が2箇所出ます。初期集約では原本を変更していません。

## DX7 と他の音源

DX7 は単独 WASM ビルドも成功し、生成 `msfa.wasm` の SHA-256 が既存の参照生成物と一致しました。初期 WASM ZIP へ含めるのは YM2612 だけです。

他の音源は source / license / build recipe の存在と取得元 hash を検査済みです。独立 Native build と全 WASM recipe の実ビルド・演奏比較は、今後種類ごとに追加します。
