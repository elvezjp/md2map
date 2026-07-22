"""LLM 設定データクラス"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """LLM 設定（外部アプリからの注入に対応）

    Attributes:
        provider: プロバイダー名 ("openai" | "anthropic" | "bedrock")
        model: モデルID
        api_key: API キー（Anthropic / OpenAI 用）
        base_url: OpenAI 互換 API（Moonshot AI 等）の接続先 URL（OpenAI 用、未指定時は公式 API）
        access_key_id: アクセスキーID（Bedrock 用）
        secret_access_key: シークレットアクセスキー（Bedrock 用）
        region: リージョン（Bedrock 用）
        max_tokens: 最大出力トークン数
    """

    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: Optional[str] = None
    max_tokens: int = 800
