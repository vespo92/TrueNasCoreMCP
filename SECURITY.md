# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

We take the security of TrueNAS MCP Server seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: security@example.com

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Policy

We follow the principle of [Coordinated Vulnerability Disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure).

## Security Best Practices

When using TrueNAS MCP Server:

1. **API Keys**: 
   - Generate unique API keys for each installation
   - Rotate API keys regularly
   - Never commit API keys to version control

2. **Network Security**:
   - Use HTTPS/TLS for all TrueNAS connections
   - Restrict TrueNAS API access to trusted networks
   - Consider using VPN for remote access

3. **Permissions**:
   - Create dedicated TrueNAS users with minimal required permissions
   - Avoid using root/admin API keys
   - Regularly audit user permissions

4. **Updates**:
   - Keep TrueNAS MCP Server updated to the latest version
   - Monitor security advisories
   - Test updates in a non-production environment first

## Security Features

TrueNAS MCP Server includes several security features:

- Environment variable configuration (no hardcoded credentials)
- SSL/TLS certificate verification
- API key authentication
- No storage of sensitive data
- Minimal permission requirements

## Acknowledgments

We would like to thank the following individuals for responsibly disclosing security issues:

- Your name here - be the first to report a vulnerability!
