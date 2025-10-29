# 🔒 Security Deep Dive

Подробный технический обзор security implementation в ReportB24.

---

## 🎯 Security Model

### Defense in Depth

ReportB24 использует **многоуровневую защиту**:

```
┌─────────────────────────────────────┐
│   1. Configuration Security         │  ← .env, validation
├─────────────────────────────────────┤
│   2. Application Security           │  ← Input validation, sanitization
├─────────────────────────────────────┤
│   3. API Security                   │  ← HTTPS, rate limiting
├─────────────────────────────────────┤
│   4. Data Security                  │  ← Encryption, masking
├─────────────────────────────────────┤
│   5. Infrastructure Security        │  ← File permissions, isolation
└─────────────────────────────────────┘
```

---

## 🔐 Configuration Security

### Hybrid Configuration System

**Architecture**:

```python
# Priority: os.environ > .env > config.ini

class SecureConfigReader:
    """
    Secure configuration with prioritized loading
    
    Security features:
    - Secrets in .env (not in Git)
    - Public settings in config.ini
    - Environment variables override
    - Automatic validation
    """
    
    def get_webhook_url(self) -> str:
        # 1. Check os.environ (highest priority)
        if 'BITRIX_WEBHOOK_URL' in os.environ:
            return self._validate_url(os.environ['BITRIX_WEBHOOK_URL'])
        
        # 2. Check .env file
        if self._env_loaded and 'BITRIX_WEBHOOK_URL' in self._env:
            return self._validate_url(self._env['BITRIX_WEBHOOK_URL'])
        
        # 3. Check config.ini (lowest priority)
        if self._config.has_option('Bitrix24', 'webhook_url'):
            return self._validate_url(
                self._config.get('Bitrix24', 'webhook_url')
            )
        
        raise ValueError("Webhook URL not found in configuration")
```

---

### .env File Security

**.env structure**:

```env
# Secrets ONLY - never commit to Git
BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/abc123/

# Optional secrets
DATABASE_PASSWORD=your_db_password
API_SECRET_KEY=your_secret_key
```

**Security measures**:

1. **.gitignore**:
   ```
   # Environment files
   .env
   .env.*
   !.env-example
   ```

2. **File permissions** (Linux/Mac):
   ```bash
   chmod 600 .env  # Owner read/write only
   ```

3. **Validation**:
   ```python
   def _validate_url(self, url: str) -> str:
       """Validate webhook URL format"""
       if not url.startswith('https://'):
           raise ValueError("Webhook URL must use HTTPS")
       
       if not re.match(r'https://.+\.bitrix24\.ru/rest/\d+/.+/', url):
           raise ValueError("Invalid Bitrix24 webhook URL format")
       
       return url
   ```

---

## 🎭 URL Masking

### Implementation

**Automatic masking in logs**:

```python
import re
import logging

class SecureLogger:
    """Logger with automatic URL masking"""
    
    @staticmethod
    def mask_webhook_url(message: str) -> str:
        """
        Mask webhook URLs in log messages
        
        Example:
            https://portal.bitrix24.ru/rest/12/abc123def456/
            → https://portal.bitrix24.ru/rest/12/***/
        """
        pattern = r'(https://[^/]+/rest/\d+)/[^/]+(/)'
        return re.sub(pattern, r'\1/***/\2', message)
    
    def info(self, message: str):
        """Log info message with masked URLs"""
        masked = self.mask_webhook_url(message)
        logging.info(masked)
```

**Usage**:

```python
logger = SecureLogger()
logger.info(f"Connecting to {webhook_url}")
# Log output: "Connecting to https://portal.bitrix24.ru/rest/12/***/"
```

---

## 🛡️ Input Validation

### Validation Strategy

```python
from decimal import Decimal, InvalidOperation

def safe_decimal(value, default=Decimal('0.0')) -> Decimal:
    """
    Safely convert to Decimal
    
    Security: Prevents InvalidOperation exceptions
    """
    if value is None:
        return default
    
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logging.warning(f"Invalid decimal value: {value}")
        return default

def safe_float(value, default=0.0) -> float:
    """
    Safely convert to float
    
    Security: Prevents TypeError and ValueError
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        logging.warning(f"Invalid float value: {value}")
        return default
```

---

### INN Validation

**ФНС algorithm implementation**:

```python
def validate_inn(inn: str) -> bool:
    """
    Validate Russian INN (ИНН)
    
    Security: Prevents invalid data processing
    Algorithm: ФНС checksum validation
    """
    if not inn or not inn.isdigit():
        return False
    
    if len(inn) == 10:
        # Legal entity (10 digits)
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(inn[i]) * coefficients[i] for i in range(9)) % 11 % 10
        return checksum == int(inn[9])
    
    elif len(inn) == 12:
        # Individual (12 digits)
        coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        
        check1 = sum(int(inn[i]) * coefficients1[i] for i in range(10)) % 11 % 10
        check2 = sum(int(inn[i]) * coefficients2[i] for i in range(11)) % 11 % 10
        
        return check1 == int(inn[10]) and check2 == int(inn[11])
    
    return False
```

---

## 🌐 API Security

### HTTPS Enforcement

```python
def _make_request(self, url: str, method: str = 'GET', **kwargs):
    """
    Make HTTP request with security checks
    
    Security:
    - HTTPS only
    - SSL/TLS verification
    - Timeout enforcement
    """
    # Enforce HTTPS
    if not url.startswith('https://'):
        raise SecurityError("HTTPS required for API calls")
    
    # SSL verification (always True in production)
    kwargs['verify'] = True
    
    # Timeout to prevent hanging
    kwargs.setdefault('timeout', self.timeout)
    
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.SSLError as e:
        raise SecurityError(f"SSL verification failed: {e}")
```

---

### Rate Limiting

```python
import time
from threading import Lock

class RateLimiter:
    """
    Rate limiter to prevent API abuse
    
    Security: Prevents DoS and API ban
    """
    
    def __init__(self, max_rate: float = 2.0):
        """
        Args:
            max_rate: Maximum requests per second (default: 2.0)
        """
        self.max_rate = max_rate
        self.min_interval = 1.0 / max_rate
        self.last_call = 0
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            elapsed = time.time() - self.last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_call = time.time()

# Usage
rate_limiter = RateLimiter(max_rate=2.0)  # Max 2 req/sec

def api_call(method: str):
    rate_limiter.wait_if_needed()
    return requests.post(f"{BASE_URL}/{method}")
```

---

### Retry with Backoff

```python
import time
from functools import wraps

def retry_on_failure(max_attempts=3, backoff=2.0):
    """
    Retry decorator with exponential backoff
    
    Security: Prevents rapid retry attacks
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    wait_time = backoff ** attempt
                    logging.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
        return wrapper
    return decorator
```

---

## 🔍 Security Auditing

### Security Checklist

**Configuration**:
- [ ] `.env` file не в Git (.gitignore)
- [ ] `.env` file permissions: 600 (owner only)
- [ ] Webhook URL использует HTTPS
- [ ] Все секреты в `.env`, не в config.ini
- [ ] Валидация всех config параметров

**Application**:
- [ ] Input validation для всех user inputs
- [ ] Safe type conversion (safe_decimal, safe_float)
- [ ] INN validation по алгоритму ФНС
- [ ] Error messages не раскрывают секреты
- [ ] Graceful error handling

**API**:
- [ ] HTTPS enforcement
- [ ] SSL/TLS verification enabled
- [ ] Rate limiting active (≤2 req/sec)
- [ ] Timeout настроен
- [ ] Retry with exponential backoff

**Logging**:
- [ ] Webhook URLs маскируются автоматически
- [ ] Секреты не логируются
- [ ] Log files имеют ограниченные права
- [ ] Log rotation настроен

**Infrastructure**:
- [ ] File permissions корректны
- [ ] Dependency audit регулярный
- [ ] Security updates применяются
- [ ] Backup секретов в безопасном месте

---

### Automated Security Tests

```python
# tests/security/test_url_masking.py
def test_webhook_url_masked_in_logs(caplog):
    """Test automatic URL masking"""
    import logging
    caplog.set_level(logging.INFO)
    
    logger = SecureLogger()
    webhook = "https://portal.bitrix24.ru/rest/12/secret123def456/"
    logger.info(f"Using webhook: {webhook}")
    
    # Assert: Secret part masked
    assert "secret123def456" not in caplog.text
    assert "***" in caplog.text
    assert "https://portal.bitrix24.ru/rest/12/***/" in caplog.text

# tests/security/test_config_security.py
def test_env_file_in_gitignore():
    """Test .env excluded from Git"""
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    assert '.env' in content
    assert '.env-example' not in content  # Example should be tracked

def test_https_enforcement():
    """Test HTTPS required for API"""
    client = Bitrix24Client("http://insecure.com/rest/12/abc/")
    
    with pytest.raises(SecurityError, match="HTTPS required"):
        client.call('profile')
```

---

## 🚨 Incident Response

### Security Incident Workflow

**1. Detection**:

```python
def detect_suspicious_activity():
    """Monitor for suspicious patterns"""
    # Multiple failed auth attempts
    # Unusual API usage patterns
    # Unexpected data access
    pass
```

**2. Response**:

```bash
# Immediate actions if webhook compromised:

# 1. Revoke webhook in Bitrix24
# 2. Generate new webhook
# 3. Update .env
BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/NEW_SECRET/

# 4. Rotate all secrets
# 5. Review logs for suspicious activity
grep "ERROR" logs/app.log | grep "$(date +%Y-%m-%d)"

# 6. Notify team
```

**3. Post-Incident**:
- [ ] Root cause analysis
- [ ] Update security procedures
- [ ] Implement additional controls
- [ ] Document lessons learned

---

## 🔐 Best Practices

### Development

1. **Never hardcode secrets**:
   ```python
   # ❌ Bad
   WEBHOOK_URL = "https://portal.bitrix24.ru/rest/12/abc123/"
   
   # ✅ Good
   WEBHOOK_URL = os.environ.get('BITRIX_WEBHOOK_URL')
   ```

2. **Use environment variables**:
   ```bash
   # Production server
   export BITRIX_WEBHOOK_URL="https://..."
   export DATABASE_PASSWORD="..."
   ```

3. **Validate all inputs**:
   ```python
   def process_data(data):
       if not validate_input(data):
           raise ValueError("Invalid input")
       # Process...
   ```

---

### Production

1. **Secure file permissions**:
   ```bash
   # Linux/Mac
   chmod 600 .env           # Owner read/write only
   chmod 755 reports/       # Owner full, others read/execute
   chmod 644 config.ini     # Owner read/write, others read
   ```

2. **Regular security audits**:
   ```bash
   # Check for known vulnerabilities
   pip install safety
   safety check
   
   # Dependency audit
   pip-audit
   ```

3. **Log monitoring**:
   ```bash
   # Monitor for errors
   tail -f logs/app.log | grep ERROR
   
   # Monitor for security events
   tail -f logs/app.log | grep -i "security\|auth\|fail"
   ```

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Bitrix24 Security](https://www.bitrix24.com/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

<div align="center">

[← Performance](performance.md) • [Architecture](architecture.md)

**Security concerns?** [Report Privately](../../SECURITY.md)

</div>
