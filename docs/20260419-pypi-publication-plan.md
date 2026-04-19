# md2map PyPI 公開準備計画書

- 作成日: 2026-04-19
- 対象 Issue: [#14 PyPI パッケージ公開の準備](https://github.com/elvezjp/md2map/issues/14)
- 対象バージョン: `pyproject.toml` 記載の最新バージョン（現状 `0.4.2`）
- 作業ブランチ: `claude/pypi-publication-setup-dEByB`

## 1. 目的

`md2map` を PyPI に公開し、他の Python プロジェクトから
`pip install md2map` で利用可能な状態にする。

本計画書の対象は **最新バージョン（v0.4.2）のみ**。`versions/` 配下の旧
バージョンコードは対象外とする（sdist/wheel に含めない）。

## 2. 前提条件の確認

- パッケージ名 `md2map` は PyPI 未使用（Issue #14 で確認済み）
- ビルドバックエンドは `hatchling`（`pyproject.toml` に設定済み）
- ライセンスは MIT（`LICENSE` / `pyproject.toml` に設定済み）
- `README.md` / `README_ja.md` が整備済み

## 3. 公開に必要な仕様

### 3.1 配布物（wheel / sdist）の構成

| 項目 | 仕様 |
| --- | --- |
| パッケージ名 | `md2map` |
| バージョン | `pyproject.toml` の `project.version` を単一の正とする |
| 同梱モジュール | `md2map/` 以下のみ。`versions/`, `add-line-numbers/`, `tests/`, `docs/` は除外 |
| エントリポイント | `md2map = "md2map.cli:main"`（CLI コマンド） |
| Python 要件 | `>=3.9` |
| 必須依存 | なし（`add-line-numbers` の Git 依存は解消する） |
| optional 依存 | `nlp` / `ai` / `dev`（既存を維持） |
| ライセンス | MIT（`LICENSE` を sdist・wheel に同梱） |
| 長文説明 | `README.md`（`project.readme` 経由） |
| URLs | `Homepage`, `Repository`, `Issues`, `Changelog` |

### 3.2 コード変更仕様

- `md2map/__init__.py` の `__version__` を `pyproject.toml` と同期
  - 可能なら `importlib.metadata` から取得し、二重管理を避ける
- `add-line-numbers` への Git 依存（`[tool.uv.sources]`）を削除
  - `md2map/utils/line_numbers.py` として**同等実装を同梱**
    （オリジナルの `add_line_numbers_to_content` を MIT 下で取り込み）
  - 利用箇所（`md2map/parsers/markdown_parser.py`）を新モジュールに差し替え
- `pyproject.toml` の `dependencies` から `add-line-numbers` を除去
- `tool.hatch.build.targets` で `md2map/` のみを wheel に含めるよう明示

### 3.3 公開運用仕様

- GitHub Actions で Trusted Publisher を利用した自動公開ワークフロー
  - トリガ: `release: published` もしくは `v*` タグ push
  - ジョブ: `build`（uv でビルド）→ `publish`（`pypa/gh-action-pypi-publish@release/v1`）
  - 権限: `id-token: write`
  - TestPyPI 手動実行用の `workflow_dispatch` も用意
- PyPI 側の Trusted Publisher 登録（PyPI 管理画面作業、PR 外）

## 4. 公開までの全体計画

| # | 項目 | 担当 | 本 PR で実施 |
| --- | --- | --- | --- |
| 1 | バージョン整合（`__init__.py` ⇔ `pyproject.toml`） | 本 PR | ✅ |
| 2 | `add-line-numbers` を同梱化、Git 依存を削除 | 本 PR | ✅ |
| 3 | `pyproject.toml` に URLs・build target・依存整理 | 本 PR | ✅ |
| 4 | MANIFEST 相当（`include` / `exclude`）の設定 | 本 PR | ✅ |
| 5 | `uv.lock` の再生成 | 本 PR | ✅ |
| 6 | 単体テストを通す | 本 PR | ✅ |
| 7 | `publish.yml` の追加 | 本 PR | ✅ |
| 8 | PyPI の Trusted Publisher 登録 | 管理者 | ❌（PR 外作業） |
| 9 | TestPyPI 動作確認 | 管理者 | ❌ |
| 10 | 本番 PyPI 公開 | 管理者 | ❌ |

## 5. 本 PR のタスク詳細

1. `md2map/__init__.py` の `__version__` を `importlib.metadata` で取得するよう書き換え（fallback は `"0.0.0"`）
2. `add-line-numbers/add_line_numbers.py` の `add_line_numbers_to_content`
   関数部分のみを `md2map/utils/line_numbers.py` に内製化（MIT 下で取込）
3. `md2map/parsers/markdown_parser.py` の
   `from add_line_numbers import add_line_numbers_to_content` を
   `from md2map.utils.line_numbers import add_line_numbers_to_content` に置換
4. `pyproject.toml`
   - `dependencies` から `add-line-numbers` を削除
   - `[tool.uv.sources]` セクション削除
   - `[project.urls]` 追加（Homepage / Repository / Issues / Changelog）
   - `[tool.hatch.build.targets.sdist]` で `include` に `md2map`, `README.md`, `LICENSE`, `CHANGELOG.md` を指定し、`versions/`, `add-line-numbers/`, `docs/`, `tests/` を除外
   - `[tool.hatch.build.targets.wheel]` で `packages = ["md2map"]` を明示
5. `uv.lock` を削除して `uv lock` で再生成
6. `.github/workflows/publish.yml` を新規作成
   - `release: published` と `workflow_dispatch` で発火
   - `uv build` で sdist + wheel 生成、`pypa/gh-action-pypi-publish` で送信
7. `pytest` 実行、必要に応じてテスト側インポート調整

## 6. 管理者による検証・受け入れ確認項目

### 6.1 PR レビュー項目（コードベース）

- [ ] `md2map/__init__.py` の `__version__` が `pyproject.toml` の
      `0.4.2` と一致して表示されること
- [ ] `md2map/utils/line_numbers.py` の `add_line_numbers_to_content`
      が元の `add-line-numbers` 実装と同一の出力をすること
- [ ] `md2map/parsers/markdown_parser.py` が
      `md2map.utils.line_numbers` を参照していること
- [ ] `pyproject.toml` の `dependencies` に `add-line-numbers` が無いこと
- [ ] `[tool.uv.sources]` セクションが削除されていること
- [ ] `[project.urls]` に GitHub URL 群が設定されていること
- [ ] `uv.lock` が再生成され、`add-line-numbers` の git ソースが
      含まれていないこと
- [ ] `.github/workflows/publish.yml` が追加されていること
- [ ] `pytest` が全件パスすること

### 6.2 ローカルビルド確認手順

```bash
# 1) クリーンな仮想環境でビルド
uv build

# 2) 生成物確認
ls dist/  # md2map-0.4.2-py3-none-any.whl, md2map-0.4.2.tar.gz

# 3) sdist の中身に versions/, add-line-numbers/ が含まれていないこと
tar -tzf dist/md2map-0.4.2.tar.gz | grep -E "versions/|add-line-numbers/" && echo NG || echo OK

# 4) wheel をクリーン環境で install
python -m venv /tmp/md2map-venv
/tmp/md2map-venv/bin/pip install dist/md2map-0.4.2-py3-none-any.whl
/tmp/md2map-venv/bin/md2map --help
/tmp/md2map-venv/bin/python -c "import md2map; print(md2map.__version__)"
# => 0.4.2 と表示されること
```

### 6.3 TestPyPI 動作確認（管理者作業）

```bash
# GitHub Actions の publish ワークフローを workflow_dispatch で実行
# → TestPyPI に md2map 0.4.2 が公開されること

pip install --index-url https://test.pypi.org/simple/ md2map
md2map --help
```

### 6.4 本番 PyPI 公開確認（管理者作業）

- GitHub Release を作成し、公開ワークフローが成功すること
- `pip install md2map` で最新版が取得できること
- `md2map build <file>` が動作すること

## 7. 本 PR でスコープ外とする残タスク

- PyPI の Trusted Publisher 登録（PyPI 側 GUI 作業）
- TestPyPI での動作確認（管理者手動実行）
- 本番 PyPI への初回公開
- `add-line-numbers` をそれ自体 PyPI パッケージとして別途公開する案
  （本 PR では同梱方式を採用したため保留）
- 旧バージョン（`versions/` 配下）の取り扱いルールの整理

## 8. 実装記録

> 実装完了後に追記する。

### 8.1 変更ファイル一覧

- `md2map/__init__.py` — `importlib.metadata.version` で `__version__` を取得するよう変更
- `md2map/utils/line_numbers.py` — 新規。`add_line_numbers_to_content` を内製化（MIT、`add-line-numbers` からの派生）
- `md2map/parsers/markdown_parser.py` — import 先を `md2map.utils.line_numbers` に変更
- `pyproject.toml` — `add-line-numbers` 依存削除、`[tool.uv.sources]` 削除、`[project.urls]` 追加、`[tool.hatch.build.targets.{sdist,wheel}]` を追加
- `.github/workflows/publish.yml` — 新規。Trusted Publisher を用いた自動公開ワークフロー
- `uv.lock` — 依存変更に伴い再生成

### 8.2 確認した動作

- `uv sync --all-extras` が成功（`add-line-numbers` の git 依存解消を確認）
- `uv run pytest` が全件パス
- `uv build` で sdist/wheel が生成され、`versions/` / `add-line-numbers/` が同梱されないこと
