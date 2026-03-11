# Security Policy

[English](./SECURITY.md) | [日本語](./SECURITY_ja.md)

## Supported Versions

Security updates are provided for the following versions. We recommend using the latest version.

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, **DO NOT create a public Issue**.

### How to Report

Please use one of the following methods:

1. **GitHub Security Advisory** (Recommended)
   - Report privately via [Security Advisories](https://github.com/elvezjp/md2map/security/advisories/new)

2. **Email**
   - Contact the security team directly: security@elvez.jp

### Information to Include

- **Description**: Overview and type of vulnerability
- **Steps to Reproduce**: Specific steps to reproduce the issue
- **Potential Impact**: Expected scope of damage and severity
- **Suggested Fix** (if possible): Mitigation or fix proposal
- **Contact Information** (optional): Contact details for follow-up

### Report Example

```
Subject: [SECURITY] Vulnerability in file path handling

Description:
Insufficient validation of input file paths allows directory traversal attacks.

Steps to Reproduce:
1. Run md2map build "../../../etc/passwd" --out ./out
2. Unintended files are processed

Impact:
Arbitrary files may be read. Severity: High

Suggested Fix:
Add path normalization and validation to ensure files are within allowed directories.
```

## Response Schedule

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Based on severity
  - Critical: Within 14 days
  - High: Within 30 days
  - Medium: Within 60 days
  - Low: Next release cycle

## Security Considerations

### File Processing

- md2map reads specified Markdown files and writes analysis results to the output directory
- Exercise caution when processing files from untrusted sources
- Specify a safe location with appropriate write permissions for the output directory

### Input Validation

- Input files are expected to be in Markdown format (`.md`)
- Malformed files are handled as parse errors
- Exercise caution with symbolic link traversal

### Output Security

- Generated files contain fragments of the original Markdown document
- Handle output files carefully when processing documents containing sensitive information
- `MAP.json` contains path information of the source file

### Dependencies

- Dependencies are regularly scanned for vulnerabilities
- Use `uv sync` to obtain the latest dependencies

## Security Best Practices

To use md2map safely, please follow these recommendations:

1. **Use the latest version**: Security fixes may be included
2. **Verify input files**: Review content before processing files from untrusted sources
3. **Restrict the output directory**: Properly manage write destinations and avoid writing to sensitive directories
4. **Handle generated files with care**: Output files contain original document content, so set appropriate access controls
5. **Run in a sandbox environment**: Consider running in an isolated environment when processing untrusted documents

## Known Security Limitations

- This tool only performs static analysis of Markdown and does not access external links
- Malicious content pattern detection is not provided
- Markdown containing HTML tags is output as-is

## Contact

For security-related questions that are not vulnerabilities:

- Create an Issue on GitHub with the `security` label
- Use Discussions for general questions

## Acknowledgments

We thank security researchers who report vulnerabilities. With the reporter's consent, acknowledgments will be included in the fix release.
