# OSS 公開準備レビュー（2026-03-11）

PR#6・#7・#8 を反映した現在のブランチを、OSS 公開用ドキュメント要件に照らしてレビューした結果です。

---

## 総合判定

**結論: 公開して問題ない状態です。**
必須項目は満たしており、以下の軽微な改善を任意で行うとより安心です。

---

## 1. ある文書・整っている点

| 文書 | 状態 |
|------|------|
| **README.md / README_ja.md** | 両方あり。プロジェクト名・言語切替・バッジ・概要・ユースケース・開発の背景・特徴・ドキュメントリンク・セットアップ・使い方・主要オプション・出力例・ディレクトリ構成・制限事項・関連プロジェクト・セキュリティ・コントリビューション・変更履歴・ライセンス・問い合わせ先が揃っている。 |
| **CHANGELOG.md / CHANGELOG_ja.md** | 両方あり。冒頭の目的・Keep a Changelog / SemVer 準拠の明記、`[0.3.0]`・`[0.2.0]`・`[0.1.0]` のエントリ（日付・カテゴリ・Breaking Changes）、リンクセクションあり。日英対応。 |
| **CONTRIBUTING.md / CONTRIBUTING_ja.md** | 両方あり。貢献方法・バグ報告・機能提案・PR手順（フォーク・ブランチ命名・コーディングスタイル・テスト・ドキュメント・コミット・プッシュ・レビュー）・開発環境・テスト実行・コーディングガイドライン・問い合わせ先。実行可能なコマンド例あり。 |
| **SECURITY.md / SECURITY_ja.md** | 両方あり。サポートバージョン（0.3.x サポート、0.2.x 非サポート）・公開Issue禁止・報告方法（Security Advisories / メール）・報告に含める情報・対応スケジュール・考慮事項・ベストプラクティス・既知の制限・問い合わせ先・謝辞。 |
| **LICENSE** | ルートにあり。MIT License、Copyright (c) 2026 株式会社 エルブズ。README のライセンス表記と一致。 |
| **.github/workflows/ci.yml** | push/PR で `uv sync --all-extras` + `uv run pytest` を OS×Python マトリクスで実行。 |
| **pyproject.toml** | name, version (0.3.0), description, readme, license (MIT), requires-python (>=3.9), authors, classifiers が適切。 |

- README の「ドキュメント」セクションから CHANGELOG / CONTRIBUTING / SECURITY / spec.md へリンクされている（英語版は `.md`、日本語版は `_ja.md` で言語対応）。
- 各文書の先頭に `[English](./XXX.md) | [日本語](./XXX_ja.md)` の言語切替リンクあり。
- ディレクトリ構成に CHANGELOG_ja、CONTRIBUTING_ja、SECURITY_ja が含まれ、日英分離後のファイル名と一致。

---

## 2. 不足している文書

なし。公開に必要な主要文書は揃っています。

---

## 3. 内容が不十分な文書

特になし。必須項目は満たしています。

---

## 4. 優先して直すべき項目

**現時点で必須の修正はありません。** 以下は任意の改善です。

1. **CHANGELOG の「バージョン比較」セクション（推奨）**
   - 要件では「バージョンが2つ以上あると特に有用」として **## バージョン比較** の表が推奨されています。
   - 現在は `versions/README.md` にバージョン比較表があるため、CHANGELOG に短い表を追加するか、CHANGELOG の「リンク」付近で `versions/README.md` への参照を入れると、要件との整合がより明確になります。

2. **pyproject.toml の Python 3.13**
   - CI は Python 3.9 と 3.13 のマトリクスで回っていますが、`classifiers` には 3.12 までしかありません。
   - 「Programming Language :: Python :: 3.13」を追加すると、PyPI 等での表記と CI が一致します（任意）。

---

## 5. 軽微な不整合・確認済み事項

| 項目 | 状態 |
|------|------|
| README の画像 `docs/assets/example.png` | 存在確認済み。表示される想定。 |
| README 問い合わせ先 | Issues・info@elvez.co.jp・会社（Elvez Inc. / 株式会社エルブズ）が記載されている。 |
| SECURITY サポートバージョン | 0.3.x サポート・0.2.x 非サポートで、現行 v0.3.0 と一致。 |
| CONTRIBUTING のコマンド | `uv run pytest`、`uv run ruff format` 等、そのまま実行できる形で記載されている。 |

---

## 6. 公開前チェック（スキル「仕上げ」）

- [x] 公開用の主要文書が一式そろっている（README, CHANGELOG, CONTRIBUTING, SECURITY, LICENSE、各日英）
- [x] README から主要文書へ辿れる（ドキュメントセクション＋各セクション内リンク）
- [x] ライセンス・セキュリティ報告・貢献方法が利用者向けに明確
- [x] 文書の内容が現行の実装（v0.3.0・オプション・ディレクトリ構成）と矛盾しない

---

## 7. まとめ

- **LICENSE**・**README（日英）**・**SECURITY（日英）**・**CONTRIBUTING（日英）**・**CHANGELOG（日英）** はいずれも存在し、必須項目を満たしています。
- **CI** により push/PR 時のテストが実行される状態です。
- 上記の「優先して直すべき項目」は推奨・任意であり、実施しなくても OSS として公開して問題ありません。
必要に応じて、CHANGELOG のバージョン比較や pyproject.toml の 3.13 を追後に整備してください。
