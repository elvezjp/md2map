# AI サブスプリット プロンプトカスタマイズ対応 計画書

作成日: 2026-03-11
関連Issue: #4（AIサブスプリットの分割位置が不適切になる場合がある）

## 1. 背景と目的

### 現状の課題

1. **プロンプトがハードコード**: `_select_chunks_ai()` 内にシステムプロンプトが直接記述されており、外部から変更・追記する手段がない
2. **構造ブロックの保護指示が不十分**: Mermaid ブロックやコードブロックの途中で分割されるケースがある
3. **分割観点の指定不可**: 分割数は `max_subsections` で制御できるが、「項番単位で分割」「処理フロー単位で分割」等の分割の観点を呼び出し元から指定できない
4. **外部アプリからの制御**: spec-code-ai-reviewer 等の外部アプリが `MarkdownParser` を呼び出す際、プロンプトをカスタマイズする手段がない

### 目的

- システムプロンプトを構造化し、`notes`（注意事項）パートへの追記を外部から行えるようにする
- CLI および外部アプリ（関数呼び出し）の両方からプロンプトカスタマイズを可能にする
- Issue #4 対応案 A（プロンプト改善）の土台を整備する

---

## 2. 現状分析

### 2.1 現在のシステムプロンプト構成

`md2map/parsers/markdown_parser.py` L644-671 に以下の 4 パートで構成：

| パートキー | 見出し | 内容 |
|-----------|--------|------|
| `role` | `# 役割` | 「文書構造の分析に特化したアシスタント」 |
| `purpose` | `# 目的` | 「意味的なまとまりが壊れないよう話題や内容の切れ目で区切る」+ タイトル付与 |
| `format` | `# 出力形式` | JSON 配列スキーマ（title, start_line, end_line） |
| `notes` | `# 注意事項` | 意味的グルーピング、カバレッジ、言語合わせ等 |

### 2.2 外部アプリからの呼び出し例

`spec-code-ai-reviewer` の `split.py` L99-103:

```python
parser = MarkdownParser(
    split_mode=request.splitMode,
    llm_config=md2map_llm_config,
    max_subsections=max_subsections,
)
```

現状プロンプトをカスタマイズするパラメータは存在しない。

### 2.3 CLI の呼び出し

`md2map/cli.py` L136-141:

```python
parser = MarkdownParser(
    split_mode=args.split_mode,
    split_threshold=args.split_threshold,
    max_subsections=args.max_subsections,
    llm_config=llm_config,
)
```

---

## 3. 設計

### 3.1 システムプロンプト構成の構造化

4 パートの構成を固定キーの辞書として定義する。各パートは「デフォルトテキスト」を持つ。

```python
# デフォルトのシステムプロンプトパート定義
DEFAULT_AI_PROMPT_PARTS: Dict[str, str] = {
    "role": (
        "あなたは文書構造の分析に特化したアシスタントです。"
    ),
    "purpose": (
        "行番号付きテキストを、意味的なまとまりが壊れないよう"
        "話題や内容の切れ目で区切ってください。\n"
        "各区間には、その内容を端的に表すタイトルを付与してください。"
    ),
    "format": (
        "JSON 配列のみを返してください。説明文やマークダウン装飾は不要です。\n"
        "各要素は以下のフィールドを持つオブジェクトです:\n"
        "- title (string): 区間の内容を表す簡潔なタイトル（文書の言語に合わせる）\n"
        "- start_line (integer): 区間の開始行番号\n"
        "- end_line (integer): 区間の終了行番号（inclusive）\n"
        "\n"
        "スキーマ:\n"
        "[{\"title\": \"...\", \"start_line\": 1, \"end_line\": ...}, ...]"
    ),
    "notes": (
        "- 意味的に関連する行は同じ区間に含め、話題の変わり目で区切ること\n"
        "- 最初の区間は行 1 から開始すること\n"
        "- 前の区間の end_line + 1 が次の区間の start_line と一致すること"
        "（隙間・重複の禁止）\n"
        "- タイトルは元の文書の言語（日本語の文書なら日本語）で付与すること"
    ),
}
```

**注意**: 実行時に変わる情報（`total_lines` 等）はユーザープロンプトに記載する方針のため、システムプロンプトには含めない。

### 3.2 カスタマイズ方法

`notes`（注意事項）パートへの **追記** のみを提供する。

他の 3 パート（`role`, `purpose`, `format`）は機能の根幹やレスポンスバリデーションと密結合しているため、外部からの変更は許可しない。

#### インターフェース

`MarkdownParser` に `Optional[str]` 型の `ai_prompt_extra_notes` 引数を追加する。指定された場合、`notes` パートのデフォルトテキスト末尾に改行区切りで追記される。

#### 使用例

```python
# 呼び出し元から notes に追記する例
parser = MarkdownParser(
    split_mode="ai",
    llm_config=llm_config,
    ai_prompt_extra_notes=(
        "- Mermaid ブロック（```mermaid ... ```）やコードブロックの途中では分割しないこと\n"
        "- 項番単位で分割すること"
    ),
)
```

### 3.3 `MarkdownParser` のインターフェース変更

```python
class MarkdownParser(BaseParser):
    def __init__(
        self,
        split_mode: str = "heading",
        split_threshold: int = 500,
        max_subsections: int = 5,
        llm_config: Optional["LLMConfig"] = None,
        llm_provider: Optional["BaseLLMProvider"] = None,
        ai_prompt_extra_notes: Optional[str] = None,  # 追加
    ) -> None:
        ...
        self._ai_prompt_extra_notes = ai_prompt_extra_notes
```

### 3.4 プロンプト組み立てメソッドの抽出

`_select_chunks_ai()` 内のプロンプト構築ロジックを専用メソッドに抽出する。

```python
def _build_ai_system_prompt(self) -> str:
    """AI サブスプリット用のシステムプロンプトを組み立てる

    実行時に変わる情報（total_lines 等）はユーザープロンプトに記載するため、
    システムプロンプトには含めない。
    """
    parts = dict(DEFAULT_AI_PROMPT_PARTS)

    # notes パートへの追記
    if self._ai_prompt_extra_notes:
        parts["notes"] = parts["notes"] + "\n" + self._ai_prompt_extra_notes

    return (
        f"# 役割\n{parts['role']}\n\n"
        f"# 目的\n{parts['purpose']}\n\n"
        f"# 出力形式\n{parts['format']}\n\n"
        f"# 注意事項\n{parts['notes']}\n"
    )
```

### 3.5 ユーザープロンプトの変更

現行のユーザープロンプトに、実行時に決まる制約（`total_lines`）を移動する。

**変更前:**
```
以下のテキストを、意味的なまとまりを保ちつつ最大 {target_parts} つに区切ってください。

{numbered_text}
```

**変更後:**
```
以下のテキストを、意味的なまとまりを保ちつつ最大 {target_parts} つに区切ってください。
テキストは全 {total_lines} 行です。最後の区間は行 {total_lines} で終了してください（すべての行を漏れなくカバー）。

{numbered_text}
```

方針: 実行ファイルに応じて変わる内容（行数等）はシステムプロンプトではなくユーザープロンプトに記載する。

### 3.6 CLI 対応

CLI には `--ai-prompt-extra-notes` オプションを追加し、`notes` パートへの追記を簡易に行えるようにする。

```
md2map build input.md --split-mode ai \
    --ai-prompt-extra-notes "- Mermaid ブロックの途中では分割しないこと"
```

```python
# cli.py に追加
build_parser.add_argument(
    "--ai-prompt-extra-notes",
    default=None,
    help="AI サブスプリットの注意事項に追記するテキスト",
)
```

`cmd_build()` 内:

```python
parser = MarkdownParser(
    split_mode=args.split_mode,
    split_threshold=args.split_threshold,
    max_subsections=args.max_subsections,
    llm_config=llm_config,
    ai_prompt_extra_notes=args.ai_prompt_extra_notes,
)
```

---

## 4. 変更対象ファイル

| ファイル | 変更内容 |
|---------|----------|
| `md2map/parsers/markdown_parser.py` | `DEFAULT_AI_PROMPT_PARTS` 定義、`__init__` に `ai_prompt_extra_notes` 引数追加、`_build_ai_system_prompt()` メソッド追加、`_select_chunks_ai()` のシステムプロンプト組み立てを置換、ユーザープロンプトに `total_lines` 制約を移動 |
| `md2map/cli.py` | `--ai-prompt-extra-notes` オプション追加、`cmd_build()` で `ai_prompt_extra_notes` を渡し |
| `tests/test_llm.py` | プロンプトカスタマイズ関連のテスト追加 |

---

## 5. テスト計画

### 5.1 ユニットテスト

| テストケース | 検証内容 |
|-------------|----------|
| `test_default_prompt_unchanged` | `ai_prompt_extra_notes` 未指定時、従来と同一のプロンプトが生成される |
| `test_prompt_extra_appended` | `ai_prompt_extra_notes` で指定したテキストが `notes` パートの末尾に追記される |
| `test_prompt_extra_none` | `ai_prompt_extra_notes=None` の場合、デフォルトのプロンプトがそのまま使用される |
| `test_total_lines_in_user_prompt` | ユーザープロンプトに `total_lines` が正しく含まれる |

### 5.2 結合テスト

| テストケース | 検証内容 |
|-------------|----------|
| `test_ai_mode_with_prompt_extra` | `ai_prompt_extra_notes` 付きで `MarkdownParser.parse()` が正常動作する |
| `test_cli_ai_prompt_extra_notes` | CLI の `--ai-prompt-extra-notes` が LLM 呼び出し時のプロンプトに反映される |

---

## 6. 対応案 A（プロンプト改善）への展望

本計画（対応案 B）の実装完了後、対応案 A として以下をデフォルトの `notes` に追加することを検討する。

```
- Mermaid ブロック（```mermaid ... ```）やコードブロック（``` ... ```）の途中では分割しないこと
- ネストされたリスト項目の途中で分割しないこと
- 論理的な区切り（項番、処理単位、定義単位等）を優先して分割すること
```

これはデフォルトの `DEFAULT_AI_PROMPT_PARTS["notes"]` への追記として実装し、本計画とは別の変更として管理する。対応案 A の具体的な文面やデフォルトに含める範囲については、本計画の実装後に改めて検討する。

---

## 7. 実装順序

1. `DEFAULT_AI_PROMPT_PARTS` 定数の定義
2. `_build_ai_system_prompt()` メソッドの実装
3. `MarkdownParser.__init__` に `ai_prompt_extra_notes` 引数追加
4. `_select_chunks_ai()` のシステムプロンプト組み立てを `_build_ai_system_prompt()` 呼び出しに置換
5. `_select_chunks_ai()` のユーザープロンプトに `total_lines` 制約を移動
6. ユニットテスト作成・実行
7. CLI の `--ai-prompt-extra-notes` オプション追加
8. 結合テスト作成・実行
