import hashlib
import ipaddress
import re
from urllib.parse import urlparse

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_RE = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")
URL_RE = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[^\s\"'<>]*)?")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HASH_RE = re.compile(r"\b([a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b")

_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

KNOWN_TLDS = {
    "com", "org", "net", "edu", "gov", "mil", "int", "info", "biz", "io",
    "co", "uk", "de", "jp", "fr", "au", "ru", "cn", "br", "in", "us",
    "app", "dev", "ai", "cloud", "click", "online", "site", "tech", "store",
}


def _is_private_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _PRIVATE_NETS)
    except ValueError:
        return False


def _looks_like_domain(token: str) -> bool:
    parts = token.lower().split(".")
    if len(parts) < 2:
        return False
    tld = parts[-1]
    if tld not in KNOWN_TLDS and len(tld) > 6:
        return False
    return bool(DOMAIN_RE.fullmatch(token))


def extract_iocs(text: str) -> dict[str, list[str]]:
    iocs: dict[str, list[str]] = {
        "ips": [],
        "domains": [],
        "urls": [],
        "emails": [],
        "hashes": [],
    }

    seen: dict[str, set[str]] = {k: set() for k in iocs}

    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?)")
        if url not in seen["urls"]:
            seen["urls"].add(url)
            iocs["urls"].append(url)

    for m in EMAIL_RE.finditer(text):
        email = m.group(0)
        if email not in seen["emails"]:
            seen["emails"].add(email)
            iocs["emails"].append(email)

    for m in IP_RE.finditer(text):
        ip = m.group(0)
        if ip in seen["ips"]:
            continue
        seen["ips"].add(ip)
        if _is_private_ip(ip):
            continue
        iocs["ips"].append(ip)

    for m in HASH_RE.finditer(text):
        h = m.group(0).lower()
        hlen = len(h)
        if hlen not in (32, 40, 64):
            continue
        if h in seen["hashes"]:
            continue
        seen["hashes"].add(h)
        if hlen == 32:
            iocs["hashes"].append({"value": h, "type": "md5"})
        elif hlen == 40:
            iocs["hashes"].append({"value": h, "type": "sha1"})
        elif hlen == 64:
            iocs["hashes"].append({"value": h, "type": "sha256"})

    for token in re.findall(r"\S+", text):
        token = token.strip(".,;:!?\"'()[]{}").lower()
        if _looks_like_domain(token) and token not in seen["domains"]:
            parsed = urlparse(token)
            domain = parsed.netloc or token
            if domain and not any(domain.startswith(p) for p in ("http://", "https://")):
                if domain not in seen["domains"]:
                    seen["domains"].add(domain)
                    iocs["domains"].append(domain)

    iocs["hashes"] = list({h["value"]: h for h in iocs["hashes"]}.values())

    return iocs


def extract_from_events(rows: list[dict]) -> list[dict]:
    all_iocs: list[dict] = []
    for row in rows:
        raw = row.get("raw") or ""
        iocs = extract_iocs(raw)
        for ioc_type, values in iocs.items():
            if ioc_type == "hashes":
                for v in values:
                    all_iocs.append({
                        "indicator": v["value"],
                        "indicator_type": v["type"],
                        "log_id": row.get("log_id"),
                        "event_line": row.get("line_number", 0),
                        "context": raw[:200],
                    })
            else:
                for v in values:
                    all_iocs.append({
                        "indicator": v,
                        "indicator_type": ioc_type[:-1] if ioc_type.endswith("s") else ioc_type,
                        "log_id": row.get("log_id"),
                        "event_line": row.get("line_number", 0),
                        "context": raw[:200],
                    })
    return all_iocs
