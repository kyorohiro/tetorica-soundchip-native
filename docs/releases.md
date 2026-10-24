# 配布と取り込み

## 配布物

`sdk.json` の版を基準に、`scripts/package_release.py` が次を生成します。

- `tetorica-soundchip-native-<version>-sources.zip`: コア、Native 接続原本、WASM 接続コード、ビルド手順、カタログ、ライセンス、試験。
- `tetorica-soundchip-native-<version>-wasm.zip`: `--wasm-dir` に指定した生成物、カタログ、ライセンス、および対応する source ZIP 自体。
- `SHA256SUMS`: ZIP ごとの SHA-256。

ZIP 内の `RELEASE-MANIFEST.json` は全 payload の path / SHA-256 / byte size を保持します。WASM 版には、対応する source ZIP の hash も記録します。日付や作業機の絶対パスを出力へ埋め込みません。同じ入力から同じ source ZIP を作れます。

参照用に取り込んだ過去の WASM バイナリーは、`source_inventory.json` で `imported-reference-binary` と表示しています。再ビルド済みとは扱いません。初期の検証用リリースは、`build/verified-wasm` に新しくビルドした YM2612 だけを指定して作ります。

## 利用側での更新

1. source / WASM ZIP を手元へ取得し、受け取った `SHA256SUMS` と照合する。
2. 独立検証を実行する。

   ```sh
   python3 tests/check_standalone_release.py --source-zip <sources.zip>
   ```

3. 必要な内容を利用側の `vendor/tetorica-soundchip-native/` などへ展開し、LICENSE / NOTICE とカタログ・manifest を残してコミットする。Native の最初の試行は source ZIP 全体の取り込みが簡単です。
4. 利用側の記録へ `version`、元 ZIP の `sha256`、使用した chip / engine とローカル差分の有無を残す。
5. 利用側のビルドはローカルファイルだけを参照する。更新時にのみ次の ZIP を取り込む。

新しい配布版を出しても、利用側の版は自動更新しません。CI や通常ビルドで GitHub / npm / 隣接 checkout から音源ソースを取得する処理は不要です。コンパイラーなどの開発ツールは利用側で用意します。

## 次段階

最初の取り込み先は既存アプリの YM2612 です。まず従来出力との比較を通してから、他の Native target と adapter を移します。ライブラリ名変更や全 API の再設計を、この初期集約と同時には行いません。
