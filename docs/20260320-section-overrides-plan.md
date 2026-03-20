# セクション単位の分割設定オーバーライド機能 修正計画書

## 概要

セクション単位で分割設定をオーバーライドする機能を追加する。
デフォルトの分割設定に対して、特定セクションの設定（split_mode, max_subsections 等）を個別に上書きできるようにする。

セクションの識別には `start_line`（見出しの開始行番号）を使用し、同名見出しがある場合でも一意に識別可能とする。

## 背景

- 呼び出し元（AI レビュアー）で、特定セクションに異なる分割設定を適用したいユースケースが発生
- md2map としては汎用的な「セクション単位の設定オーバーライド」として実装し、呼び出し元の用途に依存しない設計とする

## 前提

- 現在の実装: md2map ルート（`md2map/`）、バージョン v0.3.0
- 今回の修正は v0.3.1 として実装する

---

## Step 0: v0.3.0 の退避と v0.3.1 の準備

### v0.3.0 の退避

現在の実装を `versions/v0.3.0` に退避する。

```
対象ファイル（v0.2.0 と同様の構成）:
  md2map/         → versions/v0.3.0/md2map/
  tests/          → versions/v0.3.0/tests/
  main.py         → versions/v0.3.0/main.py
  pyproject.toml  → versions/v0.3.0/pyproject.toml
  uv.lock         → versions/v0.3.0/uv.lock
  spec.md         → versions/v0.3.0/spec.md
```

### v0.3.1 の準備

- `pyproject.toml` の `version` を `"0.3.1"` に更新
- `spec.md` にバージョン番号を反映

---

## Step 1: 見出し一覧取得機能の追加

分割実行前に見出し一覧だけを軽量に取得する公開メソッドを追加する。
呼び出し元がセクション一覧を表示し、オーバーライド対象を選択するために使用する。

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `extract_headings(content, max_depth)` 公開メソッドを追加 |
| `md2map/cli.py` | `headings` サブコマンドを追加 |
| `tests/` | 見出し一覧取得のテストを追加 |

### 設計方針: 既存ロジックの再利用による整合性保証

`extract_headings()` は新規ロジックを書かず、既存の `_extract_headings()` + `_build_sections()` を内部で呼び出し、結果を軽量な形式に変換する。

これにより：
- **実装の重複なし**: 見出し解析・セクション構築のロジックは既存メソッドをそのまま使用
- **行番号の整合性保証**: `build` コマンドと同じコードパスを通るため、`start_line` が必ず一致。後から `section_overrides` のキーとして使用しても安全
- **省略されるのはサブスプリットとファイル生成のみ**: `_refine_sections()` と `_extract_section_info()` とファイル I/O をスキップするため高速

### 実装イメージ

```python
def extract_headings(self, content: str, max_depth: int = 6) -> list[dict]:
    """見出し一覧を軽量に取得する（ファイル生成・サブスプリットなし）"""
    lines = content.splitlines()
    # 既存ロジックをそのまま使用（重複なし・行番号の整合性保証）
    headings = self._extract_headings(lines, max_depth)
    sections = self._build_sections(headings, lines, "")
    # Section オブジェクトから必要なフィールドだけ抽出
    return [
        {
            "title": s.title,
            "level": s.level,
            "start_line": s.start_line,
            "end_line": s.end_line,
            "estimated_chars": sum(
                len(line) for line in lines[s.start_line - 1 : s.end_line]
            ),
        }
        for s in sections
    ]
```

### 入出力

```
入力:  markdown テキスト, max_depth（省略時: 6）
出力:  [{ title, level, start_line, end_line, estimated_chars }]
```

- `start_line`, `end_line` は `_build_sections()` が算出した値をそのまま使用
- `estimated_chars` はセクション内の文字数（見出し行を含む）
- LLM 不要、高速処理

### CLI

```
md2map headings input.md [--max-depth 2]
```

出力は JSON 形式で標準出力に出力する。

### Python API

```python
parser = MarkdownParser()
headings = parser.extract_headings(content, max_depth=2)
# → [{"title": "API仕様", "level": 2, "start_line": 79, "end_line": 110, "estimated_chars": 1084}, ...]
```

---

## Step 2: セクション単位の分割設定オーバーライド

### 設計

#### オーバーライド構造

```python
section_overrides = {
    "default": {
        "split_mode": "ai",
        "split_threshold": 500,
        "max_subsections": 5,
        "ai_prompt_extra_notes": ""
    },
    "overrides": [
        {
            "start_line": 79,
            "split_mode": "ai",
            "max_subsections": 10,
            "split_threshold": 300,
            "ai_prompt_extra_notes": "項番単位で分割する"
        },
        {
            "start_line": 111,
            "split_mode": "ai",
            "max_subsections": 10
            // 指定しないフィールドは default を継承
        }
    ]
}
```

- `default`: 全セクションに適用されるデフォルト設定（既存の CLI パラメータと同等）
- `overrides`: 特定セクションの設定を上書き。`start_line` で対象セクションを識別
- overrides で省略されたフィールドは `default` の値を継承

#### セクション識別

- `start_line`（見出しの開始行番号、1-based）で一意に識別
- `extract_headings()` の結果から取得した `start_line` をそのまま使用
- 同名見出しがある場合でも行番号で区別可能

#### 設定のマージルール

```python
def resolve_settings(section, default_settings, override_map):
    """セクションに適用する設定を解決する"""
    override = override_map.get(section.start_line)
    if override is None:
        return default_settings
    # override のフィールドで default を上書き（未指定フィールドは default を維持）
    return {**default_settings, **override}
```

### 修正対象

| ファイル | 修正内容 |
|---|---|
| `md2map/parsers/markdown_parser.py` | `section_overrides` パラメータを受け取り、`_refine_sections()` 内でセクションごとに設定を切り替え |
| `md2map/cli.py` | `--section-overrides` オプションを追加（JSON ファイルパスまたは JSON 文字列） |
| `tests/` | セクション単位オーバーライドのテストを追加 |

### MarkdownParser の変更

```python
class MarkdownParser:
    def __init__(
        self,
        split_mode="heading",
        split_threshold=500,
        max_subsections=5,
        ai_prompt_extra_notes="",
        llm_config=None,
        section_overrides=None,  # 追加
    ):
        # 既存フィールド
        self.split_mode = split_mode
        self.split_threshold = split_threshold
        self.max_subsections = max_subsections
        self.ai_prompt_extra_notes = ai_prompt_extra_notes
        self.llm_config = llm_config
        # 新規: オーバーライドマップ（start_line → 設定 dict）
        self._override_map = {}
        if section_overrides and "overrides" in section_overrides:
            for o in section_overrides["overrides"]:
                self._override_map[o["start_line"]] = o
```

### _refine_sections() の変更

```python
def _refine_sections(self, sections, lines):
    for section in sections:
        # セクションごとに設定を解決
        settings = self._resolve_settings(section)
        split_mode = settings["split_mode"]
        threshold = settings["split_threshold"]
        max_subs = settings["max_subsections"]
        extra_notes = settings.get("ai_prompt_extra_notes", "")

        # 以降は既存ロジック（settings の値を使用）
        own_start, own_end = self._get_own_content_range(section, sections)
        total_count = self._count_words(own_text)

        if split_mode == "heading":
            continue  # 見出しモードではサブスプリットしない

        if total_count >= threshold:
            target_parts = min(max_subs, max(2, ceil(total_count / threshold)))
            if split_mode == "nlp":
                # NLP 分割（既存ロジック）
            elif split_mode == "ai":
                # AI 分割（既存ロジック、extra_notes を使用）
```

### CLI の変更

```
md2map build input.md \
  --split-mode ai --max-subsections 5 \
  --section-overrides overrides.json
```

- `--section-overrides`: JSON ファイルパスまたは JSON 文字列
- `--section-overrides` を指定した場合、`default` ブロックの値が `--split-mode` 等の既存オプションより優先される
- `--section-overrides` を指定しない場合、既存オプションがそのまま使用される（後方互換性維持）

### API（Python ライブラリとしての使用）

バックエンド等から直接 `MarkdownParser` を使用する場合：

```python
parser = MarkdownParser(
    split_mode="ai",
    max_subsections=5,
    section_overrides={
        "default": {"split_mode": "ai", "max_subsections": 5, "split_threshold": 500},
        "overrides": [
            {"start_line": 79, "split_mode": "ai", "max_subsections": 10},
            {"start_line": 111, "split_mode": "heading"},
        ]
    }
)
sections, warnings = parser.parse(file_path, max_depth=2)
```

---

## テスト計画

### Step 1: 見出し一覧取得

| テストケース | 内容 |
|---|---|
| 基本取得 | H1〜H4 の見出しを含む MD から正しく一覧取得 |
| max_depth 制限 | max_depth=2 で H3 以下が除外される |
| コードブロック内 | コードブロック内の `#` が見出しとして誤検出されない |
| 空ファイル | 見出しなしで空リストが返る |
| end_line 計算 | 最後のセクションの end_line が文書末尾になる |
| estimated_chars | 文字数が正しく算出される |
| build との整合性 | `extract_headings()` の `start_line` が `build` 実行時のセクションの `start_line` と一致する |

### Step 2: セクション単位オーバーライド

| テストケース | 内容 |
|---|---|
| override なし | 従来と同じ動作（後方互換性） |
| 単一 override | 指定セクションのみ異なる設定で分割される |
| 複数 override | 複数セクションにそれぞれ異なる設定が適用される |
| default 継承 | override で省略したフィールドが default から継承される |
| 存在しない start_line | 警告を出さず、default 設定で処理される |
| split_mode 混在 | あるセクションは AI、別のセクションは heading で分割 |
| JSON ファイル読み込み | CLI で JSON ファイルパスを指定して正しく読み込める |
| JSON 文字列 | CLI で JSON 文字列を直接指定して正しく解析される |

---

## 影響範囲

| 対象 | 影響 |
|---|---|
| `markdown_parser.py` | `extract_headings()` 追加、`_refine_sections()` にオーバーライド分岐追加 |
| `cli.py` | `headings` サブコマンド追加、`--section-overrides` オプション追加 |
| `section.py` | 変更なし（セクションモデルへのフィールド追加不要） |
| `map_generator.py` | 変更なし |
| 既存テスト | 影響なし（後方互換性維持） |
| CLI の後方互換性 | `--section-overrides` を指定しなければ従来通り動作 |
