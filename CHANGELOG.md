# Changelog

[English](./CHANGELOG.md) | [日本語](./CHANGELOG_ja.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-11

Added AI subsplit prompt customization. Redesigned prompt structure into 4 parts and enabled appending to the notes section. Also changed subsplit naming from LLM-generated titles to static `part-N` format for improved stability.

### Added

- **AI Prompt Customization**: Added `--ai-prompt-extra-notes` CLI option / `ai_prompt_extra_notes` parameter
  - Allows appending user-specified text to the end of the AI subsplit system prompt `notes` section
  - Enables flexible specification of domain-specific splitting rules (e.g., "Do not split inside Mermaid code blocks")

### Changed

- **AI Prompt Structure**: Redesigned hardcoded prompt into a 4-part dictionary `DEFAULT_AI_PROMPT_PARTS` (`role` / `purpose` / `format` / `notes`)
  - `role`, `purpose`, and `format` are tightly coupled with core functionality and cannot be modified externally
  - Only the `notes` section allows appending
- **User Message**: Added total line count (`total_lines`) to the prompt

### Breaking Changes

- **Subsplit Naming**: Changed from `<section name>: <LLM-generated title>` to `<section name>: part-N`
  - Output file names, INDEX, and MAP.json naming format differ from v0.2.0 AI mode output
  - LLM is no longer asked to generate titles; it now focuses solely on determining split positions
  - Removed `title` field from LLM response, simplified to `start_line` / `end_line` only

## [0.2.0] - 2026-02-19

Added multi-stage splitting and multi-LLM provider support. In addition to heading-based splitting, semantic re-splitting via NLP (morphological analysis) or AI (LLM) is now available.

### Added

- **Multi-stage Splitting**: Support for re-splitting large sections beyond heading-based splitting
  - `--split-mode heading`: Traditional heading-based splitting (default)
  - `--split-mode nlp`: Semantic splitting via morphological analysis (SudachiPy)
  - `--split-mode ai`: Semantic splitting via LLM
  - `--split-threshold`: Minimum character count (Japanese) / word count (English) for re-splitting (default: 500)
  - `--max-subsections`: Maximum number of subsections per section (default: 5)

- **Multi-LLM Provider**: Multiple LLM providers selectable in AI mode
  - `--ai-provider openai`: OpenAI API (default model: `gpt-4o-mini`)
  - `--ai-provider anthropic`: Anthropic API (default model: `claude-haiku-4-5-20251001`)
  - `--ai-provider bedrock`: Amazon Bedrock (default, default model: `global.anthropic.claude-haiku-4-5-20251001-v1:0`)
  - `--ai-model`: Explicitly specify model ID
  - `--ai-region`: Specify AWS region for Bedrock

- **LLM Provider Abstraction Layer**: Added `md2map/llm/` module
  - `BaseLLMProvider`: Common provider interface
  - `OpenAIProvider` / `AnthropicProvider` / `BedrockProvider`: Provider implementations
  - `LLMConfig`: Provider configuration data class
  - Factory pattern for provider creation

- **add-line-numbers**: Integrated line numbering utility as a subtree

- **Tests**: Added unit tests for LLM providers (`tests/test_llm.py`)

- **Documentation**: Reorganized sample output into `docs/examples/v0.1/` and `docs/examples/v0.2/`, added output examples for heading / nlp / ai modes

### Changed

- **INDEX.md Generation**: Added display support for subsections (re-split sections)
- **MAP.json Generation**: Added subsection information output
- **parts/ Generation**: Added subsection file generation
- **Specification**: Added NLP mode and AI mode specifications

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.1.0] - 2026-02-06

Initial release. MVP for converting Markdown documents into semantic maps.

### Added

- **CLI Command**: Implemented `md2map build` command
  - `--out`: Specify output directory (default: `./md2map-out`)
  - `--max-depth`: Maximum heading depth to process (1-6, default: 3)
  - `--id-prefix`: Section ID prefix (default: `MD`)
  - `--verbose`: Output detailed logs
  - `--dry-run`: Preview plan without generating files

- **Markdown Parser**: Heading-based document splitting
  - ATX-style heading (`#`, `##`, `###`, etc.) parsing
  - Correctly skip headings inside code blocks
  - Japanese document character counting support

- **INDEX.md Generation**: Markdown index for visualizing document structure
  - Auto-generated structure tree
  - Section details (path, line numbers, summary, keywords, ID)

- **parts/ Generation**: Split documents into section-level parts
  - Metadata header (source file, line numbers, section info)
  - Hierarchical splitting based on heading levels

- **MAP.json Generation**: Machine-readable mapping (JSON format)
  - Complete section information mapping
  - Line number correspondence with source file
  - SHA-256 checksum calculation

- **Tests**: Unit tests, e2e tests, and edge case tests

- **CI/CD**: Automated testing via GitHub Actions (Python 3.9-3.12)

### Known Limitations

This version has the following limitations:

- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)
- Internal link auto-correction not supported (detection only)

## Links

- [Repository](https://github.com/elvezjp/md2map)
- [Issue Tracker](https://github.com/elvezjp/md2map/issues)
