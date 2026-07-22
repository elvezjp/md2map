# Changelog

[English](./CHANGELOG.md) | [日本語](./CHANGELOG_ja.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - Unreleased

### Changed

- **Moved version management to git tags** (#29): Removed the `versions/` directory that kept snapshots of older versions; only the latest code is now kept at the repository root
  - Snapshots of old versions (v0.1.0–v0.4.2) are preserved under `versions/` in the `v0.4.3` tag
  - Resolves duplicate Dependabot alerts caused by lockfiles under `versions/`
  - Added a "Version Management" section to the README (EN/JA) and updated the Dependabot alert policy in SECURITY (EN/JA)
- **Removed the `add-line-numbers/` directory (git subtree)** (#29): The dependency is now solely resolved as a git source via `[tool.uv.sources]` ([elvezjp/add-line-numbers](https://github.com/elvezjp/add-line-numbers)). The subtree layout is preserved in the `v0.4.3` tag
- Removed `/versions` and `/add-line-numbers` from the sdist exclude list in `pyproject.toml`

## [0.4.3] - 2026-05-12

Raised minimum supported Python version to 3.11 to resolve a `python-dotenv` vulnerability ([CVE-2026-28684](https://nvd.nist.gov/vuln/detail/CVE-2026-28684) / [GHSA-mf9w-mj56-hr94](https://github.com/theskumar/python-dotenv/security/advisories/GHSA-mf9w-mj56-hr94), CVSS 6.6 Medium). The fix in `python-dotenv 1.2.2` requires Python 3.10+, and we are aligning with other Elvez repositories on Python 3.11 as the minimum.

### Security

- **python-dotenv vulnerability fix**: All resolved versions of `python-dotenv` in `uv.lock` are now `>= 1.2.2`, which fixes a symlink-following file overwrite issue in `set_key()` / `unset_key()` (CWE-59 / CWE-61)
  - Resolves Dependabot alert #1

### Changed

- **Minimum Python version**: Raised from 3.9 to 3.11
  - `pyproject.toml`: `requires-python = ">=3.11"`, classifiers updated, `[tool.ruff]` `target-version = "py311"`, `[tool.mypy]` `python_version = "3.11"`
  - CI matrix updated from `["3.9", "3.13"]` to `["3.11", "3.13"]`
  - README / CONTRIBUTING (EN/JA) updated to reflect the new requirement

- **Version source unification**: `md2map/__init__.py` now reads `__version__` dynamically via `importlib.metadata.version("md2map")` (falls back to `"0.0.0"` when not installed). `pyproject.toml` becomes the single source of truth, resolving the previous `0.1.0` / `0.4.x` mismatch (refs #14)

### Added

- **PyPI publication metadata** (#14): Prepared `pyproject.toml` for PyPI distribution
  - Added `[project.urls]` (Homepage / Repository / Issues / Changelog)
  - Added classifiers: `Operating System :: OS Independent`, `Topic :: Software Development :: Documentation`, `Topic :: Text Processing :: Markup :: Markdown`
  - Added `[tool.hatch.build.targets.wheel]` with `packages = ["md2map"]`
  - Added `[tool.hatch.build.targets.sdist]` with explicit `include` / `exclude` lists so that `versions/`, `add-line-numbers/`, `docs/`, `tests/`, `main.py`, `spec.md`, and `.env.example` are not bundled in sdist/wheel
- **Automated PyPI publish workflow** (#14): Added `.github/workflows/publish.yml` for Trusted Publisher-based publication
  - Triggers on `release: published` (production PyPI) and `workflow_dispatch` (TestPyPI or PyPI, selectable)
  - Uses `pypa/gh-action-pypi-publish@release/v1` with `id-token: write`
- **PyPI publication plan**: Added `docs/20260419-pypi-publication-plan.md` recording the publication strategy and admin checklist

### Notes

- `add-line-numbers` remains a Git-sourced dependency via `[tool.uv.sources]` for local development. `[tool.uv.sources]` is a uv-local override and is **not** written to sdist/wheel METADATA; the published `Requires-Dist: add-line-numbers` resolves from PyPI. **Therefore `md2map` cannot be published to PyPI until `add-line-numbers` is published first.** Issue #14 (PyPI publication preparation) remains open to track the actual publish step.

## [0.4.2] - 2026-03-28

Updated OpenAI and Bedrock LLM provider API calls to latest specifications. OpenAI now uses `max_completion_tokens` parameter (required for gpt-5.2+). Bedrock migrated from `invoke_model` to Converse API for multi-model support.

### Changed

- **OpenAI provider**: Changed `max_tokens` parameter to `max_completion_tokens` in `chat.completions.create()` call
  - Required for newer OpenAI models (gpt-5.2 and later) that no longer support `max_tokens`

- **Bedrock provider**: Migrated from `invoke_model` (raw JSON body) to `converse` API
  - Replaced Anthropic-specific `anthropic_version` + `invoke_model` with model-agnostic Converse API
  - Token limit now specified via `inferenceConfig={"maxTokens": ...}` instead of JSON body
  - Supports Anthropic, Amazon Nova, and other Bedrock-compatible models
  - Removed `import json` dependency (no longer needed)

### Added

- **`.env` file support**: CLI now loads `.env` file at startup via `python-dotenv`
  - Existing environment variables take precedence (`override=False`)
  - `.env.example` template included for reference
  - `python-dotenv` added to `ai` optional dependencies

- **Authentication documentation**: Added credential setup guide to README
  - Required environment variables per provider (OpenAI / Anthropic / Bedrock)
  - `.env` file usage instructions
  - LLM config resolution order documented in spec.md

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.4.1] - 2026-03-26

Improved error reporting by including LLM call failure information in the `warnings` list returned by `parse()`. Callers (e.g., backend APIs) can now detect AI split and AI summary failures. Also fixed subsplits to inherit parent section's `section_overrides` settings.

### Added

- **LLM failure warnings**: When AI split or AI summary LLM calls fail, error messages are now added to the `warnings` list returned by `parse()`
  - Supported in both `_generate_ai_summary()` and `_select_chunks_ai()`
  - Existing `logger.warning()` log output is preserved

- **Subsplit override inheritance**: Fixed `_resolve_settings()` so that subsplits inherit parent section's `section_overrides` settings
  - `summary_mode` and other overrides specified on parent sections now apply to their subsplits

- **Sample output**: Added heading / nlp / ai / ai+summary mode output examples and `headings.json` to `docs/examples/v0.4.1/`

### Changed

- **parse()**: Introduced `self._warnings` instance variable to make `warnings` list accessible from LLM call methods
- **_resolve_settings()**: For subsplits (`is_subsplit=True`), falls back to parent section's `start_line` for override map lookup

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.4.0] - 2026-03-25

Improved INDEX.md summary generation. The character limit for rule-based summaries is now configurable, and an LLM-based summary generation mode has been added. Summary mode operates independently of split mode and can be configured per-section.

### Added

- **Summary character limit**: Added `--summary-max-chars` option
  - Configurable character limit for rule-based summaries (default: 100)
  - Per-section override via `--section-overrides` with `summary_max_chars` key

- **AI summary mode**: Added `--summary-mode` option
  - Choose between `text` (rule-based, default) and `ai` (LLM summary)
  - Per-section override via `--section-overrides` with `summary_mode` key
  - Operates independently of `--split-mode`

- **Summary sanitization**: Added newline removal and whitespace trimming for summary strings
  - Applied to both rule-based and AI outputs to protect INDEX.md Markdown structure

- **Sample output**: Added heading / nlp / ai mode output examples and `headings.json` to `docs/examples/v0.4.0/`

### Changed

- **_resolve_settings()**: Added `summary_max_chars` (default: `100`) and `summary_mode` (default: `"text"`) to defaults
- **_extract_section_info()**: Switches between rule-based and AI summary based on `summary_mode`
- **_extract_summary()**: Added `max_chars` parameter (replacing hardcoded 100), sanitized return value
- **AI initialization check**: `summary_mode` set to `"ai"` now triggers LLM provider initialization

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.3.2] - 2026-03-24

Added skip option to `section_overrides` for excluding specific sections (and their children) from parse results. Skipped sections are not processed by AI/NLP subsplitting, reducing LLM calls and token usage.

### Added

- **Section skip**: Added `skip` option to `section_overrides`
  - Specify `{"start_line": N, "skip": true}` to exclude a section and all its children from `parse()` results
  - Skipped sections are excluded before `_refine_sections()`, avoiding unnecessary AI/NLP processing
  - `extract_headings()` is not affected by skip settings

- **Sample output**: Added heading / nlp / ai mode output examples and `headings.json` to `docs/examples/v0.3.2/`

### Changed

- **_resolve_settings()**: Added `skip` key with default value `false`
- **parse()**: Added `_filter_skipped_sections()` call between `_build_sections()` and `_refine_sections()`
- **AI initialization check**: Skip-only overrides no longer trigger unnecessary LLM provider initialization

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.3.1] - 2026-03-20

Added heading list retrieval and per-section split setting overrides. You can now apply different split settings (split_mode, max_subsections, etc.) to specific sections individually.

### Added

- **Heading list retrieval**: Added `headings` subcommand / `MarkdownParser.extract_headings()` method
  - Lightweight heading list retrieval before splitting (no LLM required, fast processing)
  - JSON output with `title`, `level`, `start_line`, `end_line`, `estimated_chars`
  - Uses the same code path as the `build` command, guaranteeing `start_line` consistency

- **Per-section overrides**: Added `--section-overrides` CLI option / `section_overrides` parameter
  - Identify sections by `start_line` and override `split_mode`, `split_threshold`, `max_subsections`, `ai_prompt_extra_notes` individually
  - Specify as a JSON file path or inline JSON string
  - Unspecified fields inherit from constructor arguments (CLI options)

- **Lazy initialization**: Added lazy initialization for LLM provider / NLP tokenizer
  - Auto-initializes when `ai` / `nlp` mode is needed via overrides, even if default is `heading` mode

- **Sample output**: Added heading / nlp / ai mode output examples and `headings.json` to `docs/examples/v0.3.1/`

- **Examples README**: Added regeneration commands for each version to `docs/examples/README.md`

### Changed

- **_refine_sections()**: Changed to resolve settings per section before performing splits
- **_build_ai_system_prompt()**: Added support for per-section `ai_prompt_extra_notes` overrides
- **Specification**: Added `headings` command spec, `--section-overrides` option, settings resolution flow, and lazy initialization

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.3.0] - 2026-03-11

Added AI subsplit prompt customization. Redesigned prompt structure into 4-part composition and enabled appending to the notes section. Also changed subsplit naming from LLM-generated titles to static `part-N` format for improved stability.

### Added

- **AI prompt customization**: Added `--ai-prompt-extra-notes` CLI option / `ai_prompt_extra_notes` parameter
  - Append user-specified text to the AI subsplit system prompt `notes` section
  - Flexibly specify domain-specific split rules (e.g., "Do not split in the middle of Mermaid blocks")

### Changed

- **AI prompt structure**: Redesigned hardcoded prompt into 4-part dictionary `DEFAULT_AI_PROMPT_PARTS` (`role` / `purpose` / `format` / `notes`)
  - `role`, `purpose`, `format` are tightly coupled with core functionality and not externally modifiable
  - Only `notes` section allows appending
- **Subsplit naming**: Changed from `<section name>: <LLM-generated title>` to `<section name>: part-N`
  - LLM no longer generates titles; focuses solely on determining split positions
  - Removed `title` field from LLM response, simplified to `start_line` / `end_line` only
- **User message**: Changed to include total line count (`total_lines`) in the prompt

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.2.0] - 2026-02-19

Added multi-stage splitting and multi-LLM provider support. In addition to heading-based splitting, semantic re-splitting via NLP (morphological analysis) or AI (LLM) is now available.

### Added

- **Multi-stage splitting**: Added re-splitting for long sections on top of heading-based splitting
  - `--split-mode heading`: Conventional heading-based splitting (default)
  - `--split-mode nlp`: Semantic splitting via morphological analysis (SudachiPy)
  - `--split-mode ai`: Semantic splitting via LLM
  - `--split-threshold`: Specify minimum character/word count for re-splitting (default: 500)
  - `--max-subsections`: Specify maximum number of subsections per section (default: 5)

- **Multi-LLM provider**: Multiple LLM providers selectable in AI mode
  - `--ai-provider openai`: OpenAI API (default model: `gpt-4o-mini`)
  - `--ai-provider anthropic`: Anthropic API (default model: `claude-haiku-4-5-20251001`)
  - `--ai-provider bedrock`: Amazon Bedrock (default, default model: `global.anthropic.claude-haiku-4-5-20251001-v1:0`)
  - `--ai-model`: Explicitly specify model ID
  - `--ai-region`: Specify Bedrock region

- **LLM provider abstraction layer**: Added `md2map/llm/` module
  - `BaseLLMProvider`: Common provider interface
  - `OpenAIProvider` / `AnthropicProvider` / `BedrockProvider`: Provider implementations
  - `LLMConfig`: Provider configuration dataclass
  - Factory pattern for provider creation

- **add-line-numbers**: Integrated line numbering utility as a subtree

- **Tests**: Added unit tests for LLM providers (`tests/test_llm.py`)

- **Documentation**: Reorganized sample output to `docs/examples/v0.1/` and `docs/examples/v0.2/`, added output examples for heading / nlp / ai modes

### Changed

- **INDEX.md generation**: Added support for subsection (re-split section) display
- **MAP.json generation**: Added subsection information output
- **parts/ generation**: Added subsection file generation
- **Specification**: Added NLP mode and AI mode specifications

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.1.0] - 2026-02-06

Initial release. MVP version that transforms Markdown documents into semantic maps.

### Added

- **CLI command**: Implemented `md2map build` command
  - `--out`: Specify output directory (default: `./md2map-out`)
  - `--max-depth`: Specify maximum heading depth to process (1-6, default: 3)
  - `--id-prefix`: Specify section ID prefix (default: `MD`)
  - `--verbose`: Enable detailed log output
  - `--dry-run`: Preview plan without generating files

- **Markdown parser**: Heading-based document splitting
  - ATX-style heading (`#`, `##`, `###`, etc.) parsing support
  - Correctly skips headings inside code blocks
  - Japanese document character counting support

- **INDEX.md generation**: Markdown index for document structure visualization
  - Auto-generated structure tree
  - Section details (path, line numbers, summary, keywords, ID)

- **parts/ generation**: Split documents into section-level parts
  - Metadata header (original file, line numbers, section info)
  - Hierarchical splitting based on heading levels

- **MAP.json generation**: Machine-readable mapping (JSON format)
  - Complete section information mapping
  - Line number correspondence with original file
  - SHA-256 checksum calculation

- **Tests**: Unit tests, e2e tests, and edge case tests

- **CI/CD**: Automated testing via GitHub Actions (Python 3.9-3.12)

### Known Limitations

This version has the following limitations:

- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)
- Internal link auto-correction not supported (detection only)

## Version Comparison

| Version | Highlights |
| ------- | ---------- |
| 0.4.2 | OpenAI/Bedrock client APIs updated; `.env` loading; authentication docs |
| 0.4.1 | LLM failures surfaced in `parse()` warnings; subsplit inherits `section_overrides` |
| 0.4.0 | Configurable rule-based summaries; per-section AI summary mode |
| 0.3.2 | `section_overrides` `skip` to exclude sections (and children) from parsing |
| 0.3.1 | `headings` subcommand; `--section-overrides`; lazy LLM/NLP initialization |
| 0.3.0 | AI prompt `notes` customization; stable `part-N` subsplit naming |
| 0.2.0 | NLP and AI split modes; multi-provider LLM (OpenAI, Anthropic, Bedrock) |
| 0.1.0 | Initial release: heading-based split, INDEX.md, parts/, MAP.json |

For frozen source trees per release, see the corresponding git tag ([Tags](https://github.com/elvezjp/md2map/tags)). Snapshots of v0.4.2 and earlier are preserved under `versions/` in the `v0.4.3` tag.

## Links

- [Repository](https://github.com/elvezjp/md2map)
- [Issue Tracker](https://github.com/elvezjp/md2map/issues)

[0.4.2]: https://github.com/elvezjp/md2map/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/elvezjp/md2map/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/elvezjp/md2map/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/elvezjp/md2map/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/elvezjp/md2map/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/elvezjp/md2map/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/elvezjp/md2map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/elvezjp/md2map/releases/tag/v0.1.0
