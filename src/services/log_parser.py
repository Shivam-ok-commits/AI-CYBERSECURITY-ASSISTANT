import ipaddress
import json
import re
import xml.etree.ElementTree as ET

SYSLOG_RE = re.compile(
    r"^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+)(?:\[(\d+)\])?:\s+(.*)$"
)
SYSLOG_ISO_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\d.]+Z?)\s+(\S+)\s+(\S+)\s+(.*)$"
)
APACHE_COMMON_RE = re.compile(
    r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([A-Z]+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\d+)'
)
APACHE_COMBINED_RE = re.compile(
    r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([A-Z]+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\d+)\s+"([^"]*)"\s+"([^"]*)"'
)
NGINX_ERROR_RE = re.compile(
    r"^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\d+#\d+):\s+\*(\d+)\s+(.*)$"
)
JSON_LINE_RE = re.compile(r"^\s*[{\[]")
XML_EVENT_RE = re.compile(r"<Event[^>]*>", re.IGNORECASE)

ALLOWED_EXTENSIONS = {".log", ".txt", ".evtx", ".syslog", ".csv", ".json", ".xml"}
MAX_FILE_SIZE = 100 * 1024 * 1024

FILENAME_FORMAT_MAP: dict[str, str] = {
    "access.log": "apache",
    "error.log": "apache",
    "nginx-access.log": "nginx",
    "nginx-error.log": "nginx",
    "syslog": "syslog",
    "messages": "syslog",
    "auth.log": "syslog",
    "secure": "syslog",
    "application.evtx": "windows",
    "system.evtx": "windows",
    "security.evtx": "windows",
}


def validate_file(filename: str, size: int) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large ({size} bytes). Max: {MAX_FILE_SIZE} bytes")


def detect_source_type(text: str, filename: str = "") -> str:
    fname_lower = filename.lower().strip()
    if fname_lower in FILENAME_FORMAT_MAP:
        return FILENAME_FORMAT_MAP[fname_lower]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == ".evtx":
        return "windows"

    first_line = text.lstrip()[:500]
    if XML_EVENT_RE.match(first_line):
        return "windows"
    if JSON_LINE_RE.match(first_line):
        return "json"
    if APACHE_COMBINED_RE.match(first_line) or APACHE_COMMON_RE.match(first_line):
        return "apache"
    if NGINX_ERROR_RE.match(first_line):
        return "nginx"
    if SYSLOG_RE.match(first_line) or SYSLOG_ISO_RE.match(first_line):
        return "syslog"
    return "generic"


def parse_line(line: str, index: int, source_type: str = "") -> dict | None:
    stripped = line.strip()
    if not stripped:
        return None

    parsed: dict = {
        "line_number": index + 1,
        "timestamp": None,
        "source_ip": None,
        "event_type": None,
        "severity": None,
        "raw": stripped,
    }

    if source_type == "syslog":
        _parse_syslog_line(stripped, parsed)
    elif source_type == "apache":
        _parse_apache_line(stripped, parsed)
    elif source_type == "nginx":
        _parse_nginx_line(stripped, parsed)
    else:
        _parse_auto(stripped, parsed)

    return parsed


def parse_log(content: str, source_type: str = "") -> list[dict]:
    if source_type == "windows":
        return _parse_windows_xml(content)
    lines = content.splitlines()
    return [p for p in (parse_line(l, i, source_type) for i, l in enumerate(lines)) if p]


def _parse_syslog_line(stripped: str, parsed: dict) -> None:
    if m := SYSLOG_RE.match(stripped):
        parsed["timestamp"] = m.group(1)
        parsed["source_ip"] = m.group(2)
        parsed["event_type"] = m.group(3)
        parsed["severity"] = _severity_from_text(f"{m.group(3)} {m.group(5)}")
    elif m := SYSLOG_ISO_RE.match(stripped):
        parsed["timestamp"] = m.group(1)
        parsed["source_ip"] = m.group(2)
        parsed["event_type"] = m.group(3)
        parsed["severity"] = _severity_from_text(f"{m.group(3)} {m.group(4)}")
    else:
        parsed["event_type"] = "syslog"
        parsed["severity"] = _severity_from_text(stripped)
        parsed["source_ip"] = _extract_ip(stripped)


def _parse_apache_line(stripped: str, parsed: dict) -> None:
    combined_m = APACHE_COMBINED_RE.match(stripped)
    common_m = APACHE_COMMON_RE.match(stripped)
    m = combined_m or common_m
    if m:
        parsed["source_ip"] = m.group(1)
        parsed["timestamp"] = m.group(2)
        parsed["event_type"] = m.group(3)
        try:
            code = int(m.group(5))
            parsed["severity"] = "error" if code >= 400 else "info"
            parsed["event_type"] = f"HTTP_{m.group(3)}_{code}"
        except ValueError:
            pass
    else:
        parsed["event_type"] = "web"
        parsed["severity"] = "info"
        parsed["source_ip"] = _extract_ip(stripped)


def _parse_nginx_line(stripped: str, parsed: dict) -> None:
    if m := NGINX_ERROR_RE.match(stripped):
        parsed["timestamp"] = m.group(1)
        parsed["severity"] = m.group(2).lower()
        parsed["event_type"] = "nginx_error"
    elif m := APACHE_COMBINED_RE.match(stripped):
        parsed["source_ip"] = m.group(1)
        parsed["timestamp"] = m.group(2)
        parsed["event_type"] = m.group(3)
        try:
            code = int(m.group(5))
            parsed["severity"] = "error" if code >= 400 else "info"
        except ValueError:
            pass
    else:
        parsed["event_type"] = "nginx"
        parsed["severity"] = "info"
        parsed["source_ip"] = _extract_ip(stripped)


def _parse_auto(stripped: str, parsed: dict) -> None:
    if m := SYSLOG_RE.match(stripped):
        parsed["timestamp"] = m.group(1)
        parsed["source_ip"] = m.group(2)
        parsed["event_type"] = m.group(3)
        parsed["severity"] = _severity_from_text(f"{m.group(3)} {m.group(5)}")
    elif m := APACHE_COMBINED_RE.match(stripped):
        parsed["source_ip"] = m.group(1)
        parsed["timestamp"] = m.group(2)
        parsed["event_type"] = m.group(3)
        try:
            code = int(m.group(5))
            parsed["severity"] = "error" if code >= 400 else "info"
        except ValueError:
            pass
    elif m := APACHE_COMMON_RE.match(stripped):
        parsed["source_ip"] = m.group(1)
        parsed["timestamp"] = m.group(2)
        parsed["event_type"] = m.group(3)
        try:
            code = int(m.group(5))
            parsed["severity"] = "error" if code >= 400 else "info"
        except ValueError:
            pass
    else:
        parsed["event_type"] = "log"
        parsed["severity"] = "info"
        parsed["source_ip"] = _extract_ip(stripped)


def _event_ns(event: ET.Element) -> str:
    return event.tag.split("}")[0] + "}" if "}" in event.tag else ""


def _parse_single_event(event: ET.Element, index: int) -> dict:
    ns = _event_ns(event)
    system = event.find(f"{ns}System") if ns else event.find("System")
    if system is None:
        system = event.find("System")
    ev = {
        "line_number": index + 1,
        "timestamp": None,
        "source_ip": None,
        "event_type": None,
        "severity": None,
        "raw": ET.tostring(event, encoding="unicode"),
    }
    if system is not None:
        for child in system:
            local = child.tag.split("}")[-1]
            text = child.text or child.get("SystemTime") or ""
            if local == "TimeCreated":
                ev["timestamp"] = child.get("SystemTime")
            elif local == "Computer":
                ev["source_ip"] = text
            elif local == "EventID":
                ev["event_type"] = text
            elif local == "Level":
                ev["severity"] = _win_level(text)
    return ev


def _parse_windows_xml(content: str) -> list[dict]:
    events: list[dict] = []
    try:
        root = ET.fromstring(content)
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if "Event" in tag:
            events.append(_parse_single_event(root, 0))
        for i, child in enumerate(root.findall(".//{http://schemas.microsoft.com/win/2004/08/events/event}Event") or root.findall(".//Event")):
            events.append(_parse_single_event(child, len(events) + i))
    except ET.ParseError:
        line_events = re.findall(r"<Event[^>]*>.*?</Event>", content, re.DOTALL)
        for i, xml_block in enumerate(line_events):
            try:
                event = ET.fromstring(xml_block)
                events.append(_parse_single_event(event, i))
            except ET.ParseError:
                pass
    return events


def _xml_text(element, path: str, attr: str | None = None) -> str | None:
    if element is None:
        return None
    child = element.find(path)
    if child is None:
        return None
    if attr:
        return child.get(attr) or child.text or None
    return child.text or None


def _win_level(level: str | None) -> str:
    mapping = {"1": "critical", "2": "error", "3": "warning", "4": "info", "5": "verbose"}
    return mapping.get(level or "", "info")


def _severity_from_text(text: str) -> str:
    low = text.lower()
    if any(kw in low for kw in ("error", "critical", "alert", "emerg", "panic")):
        return "error"
    if any(kw in low for kw in ("warn", "notice")):
        return "warning"
    return "info"


def _extract_ip(text: str) -> str | None:
    try:
        for token in text.split():
            ipaddress.ip_address(token.strip("[]()\"'"))
            return token.strip("[]()\"'")
    except ValueError:
        pass
    return None
