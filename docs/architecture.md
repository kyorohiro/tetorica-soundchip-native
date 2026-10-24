# 責務と移行方針

`tetorica-soundchip-native` を、音源コアと Native / WASM 低レベル接続コードの編集元にします。利用側へ配るファイルは、バージョンを固定した配布用スナップショットとして扱います。

| 管理元 | 担当 |
| --- | --- |
| tetorica-soundchip-native | 音源コア、C/C++ 接続コード、低レベル ABI、WASM ビルド、出典・ライセンス、コア試験 |
| tetorica-fm2612（将来の tetorica-fm） | JS API、Synth、AudioWorklet、WASM / Native へ接続する adapter |
| Playground / Tauri | 設定、画面、プロジェクト、Native IPC、演奏スケジューラー、owner / voice 管理、CPAL、音声デバイス、ホスト側 FX |

## 二箇所にファイルを置く理由

利用側にもソースを保管しますが、そこで独自に編集する運用にはしません。修正はこのリポジトリに集約し、配布 ZIP の版を上げ、利用側で取り込み更新します。更新前の利用側は以前の版のまま動きます。別リポジトリ同士を同時に変更する必要はありません。

緊急に利用側で修正した場合は、その差分を明示し、ここへ反映した後に通常の配布版へ戻します。無記録の二重管理を避けます。

## 移行の順序

1. 全音源のソース・ライセンス・元の接続コードを集める。この段階では既存アプリの参照先を変更しない。
2. 代表 YM2612 を、元リポジトリの外に展開した source ZIP だけで Native / WASM ビルドし、PCM と状態操作を検証する。
3. 既存アプリの YM2612 一種類だけを、版と hash を記録した配布物へ切り替え、既存の出力・ビルドを比較する。
4. 他のコアを順に独立 target 化して移行する。Native / WASM の相違は黙って統合せず、差分を記録してから揃える。

`native/reference/tauri/` は収録時点の原本です。全 API の安定化や全種類の独立ビルド完了を表していません。Native の既存 resampling / mute / audition 処理を、WASM のコア生成処理と同じだと仮定しません。DX7 の Native 差分も別に保存しています。

WASM の `read()` / `generateStereo()` に相当する同期的な低レベル呼び出しは保持します。Native IPC の非同期性を理由に、AudioWorklet 用 API を削らない方針です。
