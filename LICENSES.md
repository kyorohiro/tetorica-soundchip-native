# Component licenses and provenance

このコレクション全体を一つのライセンスへ変更していません。音源コアと既存の接続コードは、それぞれの著作権表示・ライセンスを保持しています。

- [catalog/chips.json](catalog/chips.json): チップ単位で source / license を探す入口。
- [catalog/source_inventory.json](catalog/source_inventory.json): 上流・取得元の版・取り込み時のファイル SHA-256。WASM の参照生成物も、ソースと区別して記録。
- [native/reference/SOURCES.json](native/reference/SOURCES.json): 既存 Tauri C++ 接続コードと Native 差分の取得元・SHA-256。
- `vendor/<component>/`: 使用ソース、上流の README / NOTICE、ライセンス原文。
- [native/README.md](native/README.md): Native 用に保持した差分と、移行用コードの扱い。

出典に記録した URL へのアクセスはビルドに不要です。異なるライセンスのコアを一つの包括ライセンスで扱わず、利用・再配布する構成に対応する文書とソースを保持してください。配布用 WASM ZIP に対応ソース ZIP を同梱するのも、この記録を失わないためです。

## Native 接続原本の未確定箇所

取り込み元の Playground Tauri のルートには LICENSE / COPYING / NOTICE がなく、一部の接続コードにもファイル単位のライセンス宣言がありませんでした。明記された宣言は保持していますが、無宣言のファイルへ音源コアの BSD / LGPL 等を推定で適用していません。`catalog/native_inventory.json` の `licenseStatus` / `licenseNote` に記録しています。

この初期版はローカルでのソース整理・検証用です。Native 接続原本の利用・公開条件は、未記載ファイルの由来と権利者の意図を確認して確定させる必要があります。新しいツールの LICENSE.tools が、これらの原本へ自動適用されるものではありません。

このリポジトリで新規作成した集約用スクリプト・試験・CMake 設定・文書のみ [LICENSE.tools](LICENSE.tools) を適用します。収録元にあったコード、音源コア、その生成物へ適用範囲を広げるものではありません。
