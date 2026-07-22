"""LLM プロバイダー抽象化レイヤーのテスト"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig
from md2map.llm.factory import build_llm_config_from_env, get_llm_provider
from md2map.parsers.markdown_parser import DEFAULT_AI_PROMPT_PARTS, MarkdownParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# LLMConfig テスト
# ---------------------------------------------------------------------------


class TestLLMConfig:
    """LLMConfig のテスト"""

    def test_create_openai_config(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.api_key == "sk-test"
        assert config.max_tokens == 800

    def test_create_anthropic_config(self):
        config = LLMConfig(provider="anthropic", model="claude-haiku-4-5-20251001", api_key="sk-ant-test")
        assert config.provider == "anthropic"
        assert config.model == "claude-haiku-4-5-20251001"

    def test_create_bedrock_config(self):
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            access_key_id="AKID",
            secret_access_key="SECRET",
            region="us-east-1",
        )
        assert config.provider == "bedrock"
        assert config.access_key_id == "AKID"
        assert config.region == "us-east-1"

    def test_custom_max_tokens(self):
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="sk-test", max_tokens=1200)
        assert config.max_tokens == 1200

    def test_default_optional_fields(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        assert config.api_key is None
        assert config.base_url is None
        assert config.access_key_id is None
        assert config.secret_access_key is None
        assert config.region is None

    def test_create_openai_compatible_config(self):
        config = LLMConfig(
            provider="openai",
            model="kimi-k2-turbo-preview",
            api_key="sk-test",
            base_url="https://api.moonshot.ai/v1",
        )
        assert config.base_url == "https://api.moonshot.ai/v1"

    def test_reasoning_effort_default_none(self):
        config = LLMConfig(provider="openai", model="gpt-4o-mini")
        assert config.reasoning_effort is None

    def test_create_config_with_reasoning_effort(self):
        config = LLMConfig(
            provider="openai",
            model="kimi-k3",
            api_key="sk-test",
            reasoning_effort="low",
        )
        assert config.reasoning_effort == "low"


# ---------------------------------------------------------------------------
# ファクトリ関数テスト
# ---------------------------------------------------------------------------


class TestGetLLMProvider:
    """get_llm_provider のテスト"""

    def test_unknown_provider_raises(self):
        config = LLMConfig(provider="unknown", model="test")
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm_provider(config)

    @patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False)
    def test_openai_provider_without_package(self):
        """openai パッケージがインポートできない場合"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(RuntimeError, match="openai"):
                get_llm_provider(config)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False)
    def test_anthropic_provider_without_package(self):
        """anthropic パッケージがインポートできない場合"""
        config = LLMConfig(provider="anthropic", model="claude-haiku-4-5-20251001", api_key="sk-test")
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(RuntimeError, match="anthropic"):
                get_llm_provider(config)

    def test_bedrock_provider_without_package(self):
        """boto3 パッケージがインポートできない場合"""
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            region="us-east-1",
        )
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(RuntimeError, match="boto3"):
                get_llm_provider(config)


class TestBuildLLMConfigFromEnv:
    """build_llm_config_from_env のテスト"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=False)
    def test_openai_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.provider == "openai"
        assert config.api_key == "sk-env-key"
        assert config.model == "gpt-4o-mini"  # デフォルト

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key", "MD2MAP_AI_MODEL": "gpt-4o"}, clear=False)
    def test_openai_model_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.model == "gpt-4o"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=False)
    def test_openai_model_explicit(self):
        config = build_llm_config_from_env(provider="openai", model="gpt-4o-mini")
        assert config.model == "gpt-4o-mini"

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-env-key", "OPENAI_BASE_URL": "https://api.moonshot.ai/v1"},
        clear=False,
    )
    def test_openai_base_url_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.base_url == "https://api.moonshot.ai/v1"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=True)
    def test_openai_base_url_default_none(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.base_url is None

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=True)
    def test_openai_reasoning_effort_explicit(self):
        config = build_llm_config_from_env(
            provider="openai", reasoning_effort="low"
        )
        assert config.reasoning_effort == "low"

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-env-key", "MD2MAP_REASONING_EFFORT": "high"},
        clear=True,
    )
    def test_openai_reasoning_effort_from_env(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.reasoning_effort == "high"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-env-key"}, clear=True)
    def test_openai_reasoning_effort_default_none(self):
        config = build_llm_config_from_env(provider="openai")
        assert config.reasoning_effort is None

    @patch.dict(os.environ, {}, clear=True)
    def test_openai_missing_key_raises(self):
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            build_llm_config_from_env(provider="openai")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-key"}, clear=False)
    def test_anthropic_from_env(self):
        config = build_llm_config_from_env(provider="anthropic")
        assert config.provider == "anthropic"
        assert config.api_key == "sk-ant-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_anthropic_missing_key_raises(self):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            build_llm_config_from_env(provider="anthropic")

    @patch.dict(os.environ, {}, clear=True)
    def test_bedrock_from_env_defaults(self):
        config = build_llm_config_from_env(provider="bedrock")
        assert config.provider == "bedrock"
        assert config.region == "ap-northeast-1"
        # IAM ロール認証の場合は access_key は None
        assert config.access_key_id is None

    @patch.dict(
        os.environ,
        {"AWS_ACCESS_KEY_ID": "AKID", "AWS_SECRET_ACCESS_KEY": "SECRET", "AWS_REGION": "us-west-2"},
        clear=False,
    )
    def test_bedrock_from_env_with_keys(self):
        config = build_llm_config_from_env(provider="bedrock")
        assert config.access_key_id == "AKID"
        assert config.secret_access_key == "SECRET"
        assert config.region == "us-west-2"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            build_llm_config_from_env(provider="unknown")


# ---------------------------------------------------------------------------
# MarkdownParser への注入テスト
# ---------------------------------------------------------------------------


class MockLLMProvider(BaseLLMProvider):
    """テスト用の LLM プロバイダー"""

    def __init__(self, response_text: str = "[]"):
        self.response_text = response_text
        self.calls: list[tuple[str, str]] = []

    def send_message(self, system_prompt: str, user_message: str) -> str:
        self.calls.append((system_prompt, user_message))
        return self.response_text


# ---------------------------------------------------------------------------
# OpenAI プロバイダー API 呼び出しテスト
# ---------------------------------------------------------------------------


class TestOpenAIProviderAPICall:
    """OpenAI プロバイダーの API 呼び出しパラメータテスト"""

    def test_uses_max_completion_tokens(self):
        """max_completion_tokens パラメータで API が呼ばれることを確認"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test", max_tokens=800)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response

        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            # モジュールキャッシュをクリアして再インポート
            import importlib
            import md2map.llm.openai_provider as oai_mod
            importlib.reload(oai_mod)
            provider = oai_mod.OpenAIProvider(config)
            result = provider.send_message("system", "user")

        call_kwargs = mock_client.chat.completions.create.call_args
        assert "max_completion_tokens" in call_kwargs.kwargs
        assert "max_tokens" not in call_kwargs.kwargs
        assert call_kwargs.kwargs["max_completion_tokens"] == 800
        assert result == "test response"

    def test_base_url_passed_to_client(self):
        """base_url 指定時、OpenAI クライアントに base_url が渡ることを確認"""
        config = LLMConfig(
            provider="openai",
            model="kimi-k2-turbo-preview",
            api_key="sk-test",
            base_url="https://api.moonshot.ai/v1",
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response

        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            import importlib
            import md2map.llm.openai_provider as oai_mod
            importlib.reload(oai_mod)
            provider = oai_mod.OpenAIProvider(config)
            result = provider.send_message("system", "user")

        client_kwargs = mock_openai_module.OpenAI.call_args.kwargs
        assert client_kwargs["base_url"] == "https://api.moonshot.ai/v1"
        assert client_kwargs["api_key"] == "sk-test"
        # 互換 API では max_completion_tokens ではなく max_tokens を使う
        call_kwargs = mock_client.chat.completions.create.call_args
        assert "max_tokens" in call_kwargs.kwargs
        assert "max_completion_tokens" not in call_kwargs.kwargs
        assert call_kwargs.kwargs["max_tokens"] == 800
        assert result == "test response"

    def test_no_base_url_client_default(self):
        """base_url 未指定時、OpenAI クライアントに base_url が渡らないことを確認"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response

        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            import importlib
            import md2map.llm.openai_provider as oai_mod
            importlib.reload(oai_mod)
            oai_mod.OpenAIProvider(config)

        client_kwargs = mock_openai_module.OpenAI.call_args.kwargs
        assert "base_url" not in client_kwargs

    def _send_with_mock(self, config: LLMConfig) -> dict:
        """モックしたクライアントで send_message し、API 呼び出しの kwargs を返す"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_response

        mock_openai_module = MagicMock()
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            import importlib
            import md2map.llm.openai_provider as oai_mod
            importlib.reload(oai_mod)
            provider = oai_mod.OpenAIProvider(config)
            provider.send_message("system", "user")

        return mock_client.chat.completions.create.call_args.kwargs

    def test_reasoning_effort_sent_with_base_url(self):
        """reasoning_effort 指定時、互換 API（base_url あり）でも送信される"""
        kwargs = self._send_with_mock(
            LLMConfig(
                provider="openai",
                model="kimi-k3",
                api_key="sk-test",
                base_url="https://api.moonshot.ai/v1",
                reasoning_effort="low",
            )
        )
        assert kwargs["reasoning_effort"] == "low"
        assert kwargs["max_tokens"] == 800

    def test_reasoning_effort_sent_without_base_url(self):
        """reasoning_effort 指定時、公式 API（base_url なし）でも送信される"""
        kwargs = self._send_with_mock(
            LLMConfig(
                provider="openai",
                model="gpt-5.2",
                api_key="sk-test",
                reasoning_effort="medium",
            )
        )
        assert kwargs["reasoning_effort"] == "medium"
        assert kwargs["max_completion_tokens"] == 800

    def test_reasoning_effort_omitted_when_unset(self):
        """reasoning_effort 未指定時は送信されない（従来動作）"""
        kwargs = self._send_with_mock(
            LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        )
        assert "reasoning_effort" not in kwargs


# ---------------------------------------------------------------------------
# Bedrock プロバイダー API 呼び出しテスト
# ---------------------------------------------------------------------------


class TestBedrockProviderAPICall:
    """Bedrock プロバイダーの Converse API 呼び出しテスト"""

    def test_uses_converse_api(self):
        """converse API が正しいパラメータで呼ばれることを確認"""
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            region="us-east-1",
            max_tokens=800,
        )

        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": "test response"}],
                },
            },
        }

        mock_boto3_module = MagicMock()
        mock_boto3_module.client.return_value = mock_client

        with patch.dict("sys.modules", {"boto3": mock_boto3_module}):
            import importlib
            import md2map.llm.bedrock_provider as br_mod
            importlib.reload(br_mod)
            provider = br_mod.BedrockProvider(config)
            result = provider.send_message("system prompt", "user message")

        mock_client.converse.assert_called_once()
        call_kwargs = mock_client.converse.call_args.kwargs
        assert call_kwargs["modelId"] == "anthropic.claude-haiku-4-5-20251001-v1:0"
        assert call_kwargs["system"] == [{"text": "system prompt"}]
        assert call_kwargs["messages"] == [{"role": "user", "content": [{"text": "user message"}]}]
        assert call_kwargs["inferenceConfig"] == {"maxTokens": 800}
        assert result == "test response"

    def test_converse_empty_response_raises(self):
        """Converse API が空レスポンスを返した場合に RuntimeError"""
        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-haiku-4-5-20251001-v1:0",
            region="us-east-1",
        )

        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": []}},
        }

        mock_boto3_module = MagicMock()
        mock_boto3_module.client.return_value = mock_client

        with patch.dict("sys.modules", {"boto3": mock_boto3_module}):
            import importlib
            import md2map.llm.bedrock_provider as br_mod
            importlib.reload(br_mod)
            provider = br_mod.BedrockProvider(config)
            with pytest.raises(RuntimeError, match="empty response"):
                provider.send_message("system", "user")


# ---------------------------------------------------------------------------
# MarkdownParser への注入テスト
# ---------------------------------------------------------------------------


class TestMarkdownParserLLMInjection:
    """MarkdownParser への LLM プロバイダー注入テスト"""

    def test_heading_mode_no_llm_needed(self):
        """heading モードでは LLM 不要"""
        parser = MarkdownParser(split_mode="heading")
        assert parser._llm_provider is None

    def test_ai_mode_with_llm_provider(self):
        """llm_provider を直接注入"""
        provider = MockLLMProvider()
        parser = MarkdownParser(split_mode="ai", llm_provider=provider)
        assert parser._llm_provider is provider

    def test_ai_mode_with_llm_config(self):
        """llm_config を注入してプロバイダーが生成される"""
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        mock_provider = MockLLMProvider()
        with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
            parser = MarkdownParser(split_mode="ai", llm_config=config)
            assert parser._llm_provider is mock_provider

    def test_ai_mode_env_fallback(self):
        """llm_config / llm_provider なしの場合、bedrock にフォールバック"""
        mock_provider = MockLLMProvider()
        with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
            parser = MarkdownParser(split_mode="ai")
            assert parser._llm_provider is mock_provider

    def test_ai_mode_provider_priority_over_config(self):
        """llm_provider は llm_config より優先される"""
        provider = MockLLMProvider()
        config = LLMConfig(provider="openai", model="gpt-4o-mini", api_key="sk-test")
        parser = MarkdownParser(split_mode="ai", llm_config=config, llm_provider=provider)
        assert parser._llm_provider is provider

    def test_ai_mode_provider_called_on_parse(self):
        """AI モードで実際にプロバイダーが呼ばれ、行番号ベースで分割されることを確認"""
        # テスト用マークダウン: 10 行（L1=見出し, L2=空行, L3-L10=本文）
        # own_content 範囲は L2〜L10（9行）
        # AI には 1-based 相対番号（1〜9）で送信される
        ai_response = json.dumps([
            {"start_line": 1, "end_line": 5},
            {"start_line": 6, "end_line": 9},
        ])
        provider = MockLLMProvider(response_text=ai_response)

        content = "# Title\n\n"
        for i in range(4):
            content += "Paragraph " + str(i + 1) + " content. " * 50 + "\n\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            sections, warnings = parser.parse(temp_path)
            # プロバイダーが呼ばれたことを確認
            assert len(provider.calls) > 0
            # プロンプトに start_line が含まれていることを確認
            system_prompt = provider.calls[0][0]
            assert "start_line" in system_prompt
            assert "title" not in system_prompt.lower() or "タイトル" not in system_prompt
            # 仮想セクションが生成されていることを確認（part-N 形式）
            virtual_sections = [s for s in sections if s.is_subsplit]
            assert len(virtual_sections) == 2
            assert virtual_sections[0].subsplit_title == "Title: part-1"
            assert virtual_sections[1].subsplit_title == "Title: part-2"
        finally:
            os.unlink(temp_path)

    def test_ai_mode_no_env_no_config_uses_bedrock(self):
        """環境変数も llm_config もない場合、bedrock がデフォルトで使われる"""
        mock_provider = MockLLMProvider()
        with patch.dict(os.environ, {}, clear=True):
            with patch("md2map.llm.factory.get_llm_provider", return_value=mock_provider):
                parser = MarkdownParser(split_mode="ai")
                assert parser._llm_provider is mock_provider


# ---------------------------------------------------------------------------
# 後方互換性テスト
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """後方互換性のテスト"""

    def test_default_parser(self):
        """引数なし MarkdownParser() が従来通り動作する"""
        parser = MarkdownParser()
        assert parser.split_mode == "heading"
        assert parser._llm_provider is None
        assert parser._nlp_tokenizer is None

    def test_default_parser_parses(self):
        """引数なし MarkdownParser() でパースが動作する"""
        parser = MarkdownParser()
        sections, warnings = parser.parse(str(FIXTURES_DIR / "simple.md"))
        assert len(sections) > 0

    def test_heading_mode_explicit(self):
        """heading モードの明示的指定"""
        parser = MarkdownParser(split_mode="heading")
        sections, warnings = parser.parse(str(FIXTURES_DIR / "simple.md"))
        assert len(sections) > 0
        virtual = [s for s in sections if s.is_subsplit]
        assert len(virtual) == 0


# ---------------------------------------------------------------------------
# 親セクション自身コンテンツ範囲テスト
# ---------------------------------------------------------------------------


class TestOwnContentRange:
    """親セクションの自身コンテンツ範囲の算出と再分割テスト"""

    def test_parent_section_with_large_own_content(self):
        """子セクションを持つ親セクションの自身コンテンツが分割される"""
        # L1: # Parent
        # L2: (空行)
        # L3-L10: 巨大テーブル（own content）
        # L11: ## Child
        # L12: child content
        # own_content 範囲は L2〜L10（9行）
        # AI には 1-based 相対番号（1〜9）で送信される
        ai_response = json.dumps([
            {"start_line": 1, "end_line": 5},
            {"start_line": 6, "end_line": 9},
        ])
        provider = MockLLMProvider(response_text=ai_response)

        content = "# Parent\n\n"
        content += "| Col A | Col B |\n"
        content += "|-------|-------|\n"
        for i in range(6):
            content += f"| row{i} | data{i} |\n"
        content += "\n## Child\n\nChild content.\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=10,
                llm_provider=provider,
            )
            sections, _ = parser.parse(temp_path)

            # プロバイダーが呼ばれたことを確認
            assert len(provider.calls) > 0

            # 子セクション（## Child）が保持されていることを確認
            child_sections = [s for s in sections if s.title == "Child"]
            assert len(child_sections) == 1

            # 親セクション（# Parent）が保持されていることを確認
            parent_sections = [s for s in sections if s.title == "Parent" and not s.is_subsplit]
            assert len(parent_sections) == 1

        finally:
            os.unlink(temp_path)

    def test_ai_mode_fallback_on_invalid_response(self):
        """AI の無効なレスポンスで行数ベースのフォールバック分割が行われる"""
        provider = MockLLMProvider(response_text="invalid json")

        content = "# Title\n\n"
        for i in range(4):
            content += "Line " + str(i + 1) + " content. " * 50 + "\n\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            sections, _ = parser.parse(temp_path)

            # フォールバックで仮想セクションが生成されること
            virtual_sections = [s for s in sections if s.is_subsplit]
            assert len(virtual_sections) >= 2

            # フォールバック時は threshold split
            for vs in virtual_sections:
                assert "ai threshold split" in vs.note
        finally:
            os.unlink(temp_path)

    def test_ai_mode_line_numbers_in_prompt(self):
        """プロンプトに正しい行番号が含まれることを確認"""
        provider = MockLLMProvider(response_text="[]")

        content = "# Title\n\n"
        content += "Big content. " * 100 + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            parser.parse(temp_path)

            assert len(provider.calls) > 0
            user_message = provider.calls[0][1]
            # 行番号が 1 始まりの add-line-numbers 形式で含まれていることを確認
            assert "   1:" in user_message or "1:" in user_message
        finally:
            os.unlink(temp_path)


# ---------------------------------------------------------------------------
# プロンプトカスタマイズテスト
# ---------------------------------------------------------------------------


class TestAIPromptCustomization:
    """AI プロンプトカスタマイズのテスト"""

    def test_default_prompt_unchanged(self):
        """ai_prompt_extra_notes 未指定時、デフォルトプロンプトが使われる"""
        provider = MockLLMProvider()
        parser = MarkdownParser(split_mode="ai", llm_provider=provider)
        prompt = parser._build_ai_system_prompt()
        assert DEFAULT_AI_PROMPT_PARTS["role"] in prompt
        assert DEFAULT_AI_PROMPT_PARTS["purpose"] in prompt
        assert DEFAULT_AI_PROMPT_PARTS["format"] in prompt
        assert DEFAULT_AI_PROMPT_PARTS["notes"] in prompt

    def test_prompt_extra_appended(self):
        """ai_prompt_extra_notes が notes パート末尾に追記される"""
        extra = "- Mermaid ブロックの途中では分割しないこと"
        provider = MockLLMProvider()
        parser = MarkdownParser(
            split_mode="ai", llm_provider=provider, ai_prompt_extra_notes=extra
        )
        prompt = parser._build_ai_system_prompt()
        assert extra in prompt
        # デフォルトの notes も含まれている
        assert DEFAULT_AI_PROMPT_PARTS["notes"] in prompt

    def test_prompt_extra_none(self):
        """ai_prompt_extra_notes=None の場合、デフォルトと同一"""
        provider = MockLLMProvider()
        parser_default = MarkdownParser(split_mode="ai", llm_provider=provider)
        parser_none = MarkdownParser(
            split_mode="ai", llm_provider=provider, ai_prompt_extra_notes=None
        )
        assert parser_default._build_ai_system_prompt() == parser_none._build_ai_system_prompt()

    def test_total_lines_in_user_prompt(self):
        """ユーザープロンプトに total_lines が含まれる"""
        ai_response = json.dumps([
            {"start_line": 1, "end_line": 2},
        ])
        provider = MockLLMProvider(response_text=ai_response)

        content = "# Title\n\n"
        content += "Big content. " * 100 + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
            )
            parser.parse(temp_path)

            assert len(provider.calls) > 0
            user_message = provider.calls[0][1]
            assert "全" in user_message and "行です" in user_message
        finally:
            os.unlink(temp_path)

    def test_prompt_extra_passed_to_llm(self):
        """ai_prompt_extra_notes が実際の LLM 呼び出しに反映される"""
        extra = "- コードブロックの途中では分割しないこと"
        provider = MockLLMProvider(response_text="[]")

        content = "# Title\n\n"
        content += "Big content. " * 100 + "\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
                ai_prompt_extra_notes=extra,
            )
            parser.parse(temp_path)

            assert len(provider.calls) > 0
            system_prompt = provider.calls[0][0]
            assert extra in system_prompt
        finally:
            os.unlink(temp_path)

    def test_prompt_no_title_field(self):
        """システムプロンプトに title フィールドが含まれないことを確認"""
        provider = MockLLMProvider()
        parser = MarkdownParser(split_mode="ai", llm_provider=provider)
        prompt = parser._build_ai_system_prompt()
        assert "title" not in prompt
        assert "タイトル" not in prompt


# ---------------------------------------------------------------------------
# AI 呼び出し並列実行テスト（Issue #34）
# ---------------------------------------------------------------------------


class ThreadSafeMockProvider(BaseLLMProvider):
    """並列実行テスト用の LLM プロバイダー

    respond(system_prompt, user_message) の結果を返す。例外送出も可能。
    """

    def __init__(self, respond):
        import threading

        self.respond = respond
        self.calls: list[tuple[str, str]] = []
        self._lock = threading.Lock()

    def send_message(self, system_prompt: str, user_message: str) -> str:
        with self._lock:
            self.calls.append((system_prompt, user_message))
        return self.respond(system_prompt, user_message)


def _write_temp_md(content: str) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


def _multi_section_content(num_sections: int = 4) -> str:
    """複数セクションのテスト用マークダウンを生成する"""
    content = ""
    for i in range(num_sections):
        content += f"# Section{i + 1}\n\n"
        content += "内容のテキストです。" * 20 + "\n\n"
    return content


class TestAIConcurrency:
    """ai_concurrency 設定のテスト"""

    def test_default_is_sequential(self):
        """デフォルトは 1（逐次実行）"""
        parser = MarkdownParser()
        assert parser.ai_concurrency == 1

    def test_concurrency_clamped_to_one(self):
        """0 以下は 1 に丸められる"""
        parser = MarkdownParser(ai_concurrency=0)
        assert parser.ai_concurrency == 1
        parser = MarkdownParser(ai_concurrency=-5)
        assert parser.ai_concurrency == 1

    def test_concurrency_stored(self):
        parser = MarkdownParser(ai_concurrency=4)
        assert parser.ai_concurrency == 4


class TestParallelAISummary:
    """AI要約の並列実行テスト"""

    def _run_parse(self, concurrency: int, respond):
        provider = ThreadSafeMockProvider(respond)
        temp_path = _write_temp_md(_multi_section_content(4))
        try:
            parser = MarkdownParser(
                summary_mode="ai",
                llm_provider=provider,
                ai_concurrency=concurrency,
            )
            sections, warnings = parser.parse(temp_path)
            return sections, warnings, provider
        finally:
            os.unlink(temp_path)

    def test_parallel_summaries_match_sequential(self):
        """並列実行の要約・警告が逐次実行と一致する"""

        def respond(system, user):
            # セクション名をエコーして呼び出しを区別可能にする
            for i in range(1, 5):
                if f"Section{i}" in user:
                    return f"要約{i}"
            return "要約"

        seq_sections, seq_warnings, _ = self._run_parse(1, respond)
        par_sections, par_warnings, par_provider = self._run_parse(4, respond)

        assert [s.summary for s in par_sections] == [
            s.summary for s in seq_sections
        ]
        assert par_warnings == seq_warnings
        assert len(par_provider.calls) == 4

    def test_partial_failure_does_not_affect_others(self):
        """一部セクションの失敗が他セクションに影響しない"""

        def respond(system, user):
            if "Section2" in user:
                raise RuntimeError("simulated failure")
            return "要約OK"

        sections, warnings, _ = self._run_parse(4, respond)

        summaries = [s.summary for s in sections]
        assert summaries[0] == "要約OK"
        assert summaries[1] is None  # 失敗したセクション
        assert summaries[2] == "要約OK"
        assert summaries[3] == "要約OK"
        assert len(warnings) == 1
        assert "Section2" in warnings[0]

    def test_warnings_preserve_section_order(self):
        """並列実行でも警告がセクション順に並ぶ"""
        import time

        def respond(system, user):
            # 逆順で完了するように遅延を入れる
            if "Section1" in user:
                time.sleep(0.05)
                raise RuntimeError("fail-1")
            if "Section3" in user:
                raise RuntimeError("fail-3")
            return "要約OK"

        sections, warnings, _ = self._run_parse(4, respond)

        assert len(warnings) == 2
        assert "Section1" in warnings[0]
        assert "Section3" in warnings[1]

    def test_text_mode_not_parallelized(self):
        """summary_mode=text では LLM 呼び出しなし（並列化パスに入らない）"""
        provider = ThreadSafeMockProvider(lambda s, u: "unused")
        temp_path = _write_temp_md(_multi_section_content(3))
        try:
            parser = MarkdownParser(
                summary_mode="text",
                llm_provider=provider,
                ai_concurrency=4,
            )
            sections, warnings = parser.parse(temp_path)
            assert len(provider.calls) == 0
            assert all(s.summary for s in sections)
        finally:
            os.unlink(temp_path)


class TestParallelAISplit:
    """AI分割の並列実行テスト"""

    def _two_section_content(self) -> str:
        """同一行数の 2 セクション（own content 9 行ずつ）を生成する"""
        section = "".join(
            "Paragraph " + str(i + 1) + " content. " * 50 + "\n\n"
            for i in range(4)
        )
        return f"# First\n\n{section}# Second\n\n{section}"

    def _run_split(self, concurrency: int, respond):
        provider = ThreadSafeMockProvider(respond)
        temp_path = _write_temp_md(self._two_section_content())
        try:
            parser = MarkdownParser(
                split_mode="ai",
                split_threshold=50,
                llm_provider=provider,
                ai_concurrency=concurrency,
            )
            sections, warnings = parser.parse(temp_path)
            return sections, warnings, provider
        finally:
            os.unlink(temp_path)

    def test_parallel_split_matches_sequential(self):
        """並列実行の分割結果が逐次実行と一致する"""
        ai_response = json.dumps([
            {"start_line": 1, "end_line": 5},
            {"start_line": 6, "end_line": 9},
        ])

        seq_sections, seq_warnings, _ = self._run_split(1, lambda s, u: ai_response)
        par_sections, par_warnings, par_provider = self._run_split(
            4, lambda s, u: ai_response
        )

        assert len(par_provider.calls) == 2

        def describe(sections):
            return [
                (s.title, s.is_subsplit, s.subsplit_title, s.start_line, s.end_line)
                for s in sections
            ]

        assert describe(par_sections) == describe(seq_sections)
        assert par_warnings == seq_warnings

        # 各親セクションに 2 つずつ仮想セクションが生成される
        virtual = [s for s in par_sections if s.is_subsplit]
        assert len(virtual) == 4

    def test_parallel_split_failure_falls_back(self):
        """並列実行でも AI 呼び出し失敗時は閾値ベースにフォールバックする"""

        def respond(system, user):
            raise RuntimeError("simulated API failure")

        sections, warnings, _ = self._run_split(4, respond)

        # フォールバックで仮想セクションが生成される
        virtual = [s for s in sections if s.is_subsplit]
        assert len(virtual) >= 2
        for vs in virtual:
            assert "ai threshold split" in vs.note
        # 失敗ごとに警告が記録される
        assert len(warnings) == 2
        assert all("AI API call failed" in w for w in warnings)
