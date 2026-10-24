# Changelog

## 0.1.0 — bootstrap

- Playground の追加生成 22 種類に必要なコアと、既存 Native C++ 接続コードをソース付きで集約。
- 共通 ymfm ソースを一箇所へ配置し、チップ別カタログ・ライセンス・取得元・SHA-256 を収録。
- Native YM2612 の独立 CMake target と PCM 自動試験を追加。他の Native 接続コードは移行用原本として保持。
- WASM ビルド手順と、バージョン固定の自己完結した配布 ZIP・独立展開検証を追加。
- 既存 npm / Playground Tauri の参照先切り替えは次段階。
