"""
Detección heurística de patrones típicos de SQLi / XSS en strings de entrada.
No sustituye WAF ni ORM parametrizado; complementa logging y rechazo temprano.
"""
import re
from dataclasses import dataclass

# Patrones “severos”: bloqueo + log SECURITY
_SQLI_SEVERE = re.compile(
    r"(?is)"
    r"(\bOR\b\s+[\w'\"]+\s*=\s*[\w'\"]+)|"
    r"(\bUNION\b\s+ALL\s+SELECT\b)|(\bUNION\b\s+SELECT\b)|"
    r"(;\s*(DROP|DELETE|INSERT|UPDATE|ALTER|EXEC|EXECUTE)\b)|"
    r"(--|\#|/\*|\*/)|"
    r"(\bOR\b\s*'?\d*'?\s*=\s*'?\d*)|"
    r"(\bSELECT\b.+\bFROM\b)|"
    r"(\bSLEEP\s*\()|(\bWAITFOR\b\s+DELAY\b)|"
    r"(\bINFORMATION_SCHEMA\b)"
)

_XSS_SEVERE = re.compile(
    r"(?is)"
    r"(<script[\s/>])|(</script>)|"
    r"(javascript\s*:)|"
    r"(\bon\w+\s*=)|"
    r"(<iframe[\s/>])|"
    r"(data\s*:\s*text/html)"
)

# Patrones “sospechosos”: solo WARNING en bitácora (no bloquean salvo combinación fuerte)
_SQLI_SUSPICIOUS = re.compile(r"(?is)('|\"|;|\bOR\b|\bAND\b\s+['\"]?\d)")

_XSS_SUSPICIOUS = re.compile(r"(?is)(<[^>]{0,120}>|&#x?[0-9a-f]+;|%3c)")


@dataclass(frozen=True)
class ScanResult:
    severe_sqli: bool
    severe_xss: bool
    suspicious: bool


def scan_input(value: str) -> ScanResult:
    if not value or not isinstance(value, str):
        return ScanResult(False, False, False)
    s = value.strip()
    if len(s) > 8000:
        s = s[:8000]
    sev_sql = bool(_SQLI_SEVERE.search(s))
    sev_xss = bool(_XSS_SEVERE.search(s))
    susp = bool(_SQLI_SUSPICIOUS.search(s) or _XSS_SUSPICIOUS.search(s))
    return ScanResult(sev_sql, sev_xss, susp)


def is_severe_injection(value: str) -> bool:
    r = scan_input(value)
    return r.severe_sqli or r.severe_xss


def is_suspicious_only(value: str) -> bool:
    r = scan_input(value)
    return r.suspicious and not (r.severe_sqli or r.severe_xss)
