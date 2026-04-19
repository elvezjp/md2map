"""テキストに行番号を付与するユーティリティ

https://github.com/elvezjp/add-line-numbers の ``add_line_numbers_to_content``
を派生させたもの。PyPI 配布時に外部 Git 依存を持たないよう同梱している。
"""

from __future__ import annotations


def add_line_numbers_to_content(content: str) -> tuple[str, int]:
    """文字列に行番号を付与して返す。

    Args:
        content: 行番号を付与する元のテキスト。

    Returns:
        tuple: (行番号付きテキスト, 行数)
    """
    lines = content.splitlines()
    line_count = len(lines)

    numbered_lines = [f"{i:4d}: {line}" for i, line in enumerate(lines, 1)]

    return "\n".join(numbered_lines), line_count
