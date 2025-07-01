# Security Policy

## Supported Versions

We actively maintain security updates for the following versions of ReportB24:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Security Context and Boundaries

### Deployment Considerations

ReportB24 is designed to be deployed as a **trusted application** within your organization's secure infrastructure. Please consider the following security boundaries:

#### ✅ Secure Deployment Context
- **Trusted Environment**: Deploy on secure servers/workstations within your network perimeter
- **Configuration Security**: Use `.env` files for secrets, never commit sensitive data to Git
- **Network Security**: Bitrix24 API calls should be made through secure HTTPS connections
- **Access Control**: Restrict access to configuration files and generated reports

#### ⚠️ Security Considerations
- **API Credentials**: Store Bitrix24 webhook URLs in `.env` files, not in `config.ini`
- **Generated Reports**: Excel files may contain sensitive business data - handle appropriately
- **Log Files**: Application logs mask sensitive URLs but may contain business information
- **Dependencies**: Keep Python dependencies updated to address security vulnerabilities

### Not Considered Security Issues

The following scenarios are **outside our security boundary** and should be addressed through proper deployment practices:

- Exposure of configuration files containing API credentials (use `.env` properly)
- Unauthorized access to generated Excel reports (implement access controls)
- Man-in-the-middle attacks on Bitrix24 API calls (ensure HTTPS)
- Privilege escalation through local file system access (deploy with appropriate permissions)

## Reporting a Vulnerability

We take security seriously and appreciate responsible disclosure of security vulnerabilities.

### How to Report

**For security vulnerabilities**, please use one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security](https://github.com/[your-org]/ReportB24/security) tab in our repository
   - Click "Report a vulnerability"
   - Fill out the security advisory form

2. **GitHub Issues** (For non-sensitive security concerns)
   - Use the [Issues](https://github.com/[your-org]/ReportB24/issues) section
   - Label with `security` tag
   - Provide detailed information about the issue

### What to Include

When reporting a security issue, please include:

- **Description**: Clear description of the vulnerability
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact and affected components
- **Environment**: Python version, OS, ReportB24 version
- **Proposed Solution**: If you have suggestions for fixes

### Response Timeline

- **Initial Response**: Within 48 hours
- **Assessment**: Within 5 business days
- **Resolution**: Varies based on complexity and severity
- **Disclosure**: Coordinated disclosure after fix is available

## Security Features

### Current Security Measures

- **🔐 Secure Configuration**: Hybrid `.env` + `config.ini` system with automatic secret migration
- **🔍 URL Masking**: Sensitive webhook URLs are masked in logs (`https://portal.bitrix24.ru/rest/12/***/`)
- **📝 Secure Logging**: No sensitive data exposed in application logs
- **⚡ Input Validation**: Comprehensive validation of configuration parameters
- **🛡️ Dependency Management**: Regular dependency updates via `requirements.txt`

### Hardening Recommendations

For enhanced security in production environments:

1. **Environment Variables**: Use OS environment variables for maximum security
2. **File Permissions**: Set restrictive permissions on `.env` and config files (600)
3. **Network Security**: Use VPN or secure networks for Bitrix24 API access
4. **Logging**: Implement centralized logging with appropriate retention policies
5. **Updates**: Regularly update ReportB24 and Python dependencies

## Security Auditing

We implement several automated security measures:

- **Dependency Scanning**: Monitor for known vulnerabilities in dependencies
- **Code Quality**: Automated testing with 261/261 tests passing
- **Security Reviews**: Manual security reviews for major changes
- **Best Practices**: Follow Python security best practices and PEP standards

## Contact

For questions about this security policy or security-related matters:

- **Security Issues**: Use GitHub Security Advisories or Issues
- **General Questions**: Create a regular GitHub Issue
- **Documentation**: Check our [README.md](README.md) for security setup instructions

---

**Note**: This security policy is effective as of the publication date and may be updated as needed. Check the repository for the latest version. 