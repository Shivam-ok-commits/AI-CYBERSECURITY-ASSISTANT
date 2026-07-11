import json
import re

from src.config import settings
from src.services.ai_explainer import explain_general
from src.services.ai_memory import get_history, save_message
from src.services.ai_prompts import get_prompt
from src.services.ai_rag import search_documents
from src.services.ai_providers import get_provider

SUGGESTED_QUESTIONS = [
    "What suspicious events were found?",
    "Explain any critical alerts.",
    "What is the attack chain?",
    "What should I investigate next?",
    "Are there any IOCs to look up?",
    "What does this event mean?",
    "How should I respond?",
]

FALLBACK_RESPONSES: dict[str, str] = {
    "mitre": "MITRE ATT&CK technique not yet identified. Analyze the event context and match against the MITRE framework (https://attack.mitre.org).",
    "confidence": "Confidence level is based on the number of matching indicators and event severity scores.",
    "attack": "Based on the chronological event analysis, I can identify potential attack stages. The timeline shows events that may correspond to Initial Access, Execution, Persistence, and Exfiltration phases.",
    "ioc": "IOCs have been extracted from the logs. Use the Threat Intelligence endpoints to look up their reputation scores.",
    "default": "I'm your AI Cybersecurity Assistant. I can help analyze logs, explain security events, investigate threats, and provide recommendations. What would you like to investigate?",
}


async def chat_completion(session_id: int, message: str, user_id: int) -> dict:
    save_message(session_id, "user", message, user_id=user_id)

    history = get_history(session_id)
    rag_context = _retrieve_context(message)
    local_reply = _generate_local_reply(message, rag_context)
    suggested = _get_suggested_questions(local_reply)
    evidence = _extract_evidence(message, rag_context)

    provider = get_provider()
    if provider.is_available():
        enhanced = await _try_provider(provider, session_id, history, message, rag_context, local_reply)
        if enhanced:
            local_reply = enhanced

    save_message(session_id, "assistant", local_reply, user_id=user_id)

    return {
        "session_id": session_id,
        "reply": local_reply,
        "evidence": evidence,
        "suggested_questions": suggested,
        "confidence": 0.8 if rag_context else 0.5,
    }


async def investigate_log(log_id: int, event_rows: list[dict]) -> dict:
    extracted = _extract_log_summary(event_rows)
    prompt = get_prompt("investigation").format(log_data=_format_log_data(event_rows[:100]))

    patterns = _find_patterns(event_rows)
    critical = [e for e in event_rows if e.get("severity") in ("critical", "high")]

    chain = _build_attack_chain(extracted)
    priorities = _prioritize_events(critical)

    recommendations = [
        f"Investigate {len(critical)} critical events immediately",
        "Correlate source IPs with threat intelligence",
        "Check for lateral movement indicators",
        "Review authentication logs for unauthorized access",
        "Isolate affected systems if compromise is confirmed",
    ]

    return {
        "summary": f"Analysis complete: {extracted['total']} events, {len(critical)} critical, {len(patterns)} suspicious patterns detected.",
        "suspicious_patterns": patterns[:10],
        "critical_events": [{"line": e.get("line_number"), "raw": (e.get("raw") or "")[:200]} for e in critical[:10]],
        "attack_chain": chain,
        "priorities": priorities,
        "recommendations": recommendations,
        "confidence": 0.7,
    }


async def generate_recommendations(events: list[dict]) -> dict:
    severities = [e.get("severity") for e in events]
    has_critical = "critical" in severities
    has_error = "error" in severities

    return {
        "next_steps": [
            "Isolate affected hosts from the network",
            "Collect memory and disk forensics from compromised systems",
            "Reset credentials for affected accounts",
            "Review firewall logs for C2 communication",
        ],
        "containment": [
            "Block identified malicious IPs at the firewall",
            "Disable compromised user accounts",
            "Quarantine affected endpoints",
        ] if has_critical else [
            "Monitor identified suspicious IPs",
            "Restrict affected service accounts",
        ],
        "recovery": [
            "Restore systems from known-good backups",
            "Patch exploited vulnerabilities",
            "Rotate all credentials and secrets",
        ],
        "patching": [
            "Apply latest security updates to all systems",
            "Prioritize patches for exploited CVEs",
            "Enable automatic updates where possible",
        ],
        "detection_improvements": [
            "Enable enhanced audit logging on critical systems",
            "Deploy additional monitoring for suspicious process chains",
            "Implement alerting for brute-force attempts",
            "Configure threat intelligence feed integration",
        ],
    }


async def analyze_timeline(event_rows: list[dict]) -> dict:
    timeline = []
    for e in event_rows:
        timeline.append({
            "timestamp": e.get("timestamp", "unknown"),
            "event": (e.get("raw") or "")[:150],
            "severity": e.get("severity", "info"),
            "explanation": explain_general(e.get("raw", "")),
        })

    stages = _build_attack_chain(_extract_log_summary(event_rows))
    critical_events = [e for e in event_rows if e.get("severity") in ("critical", "high")]

    root_cause = ""
    if critical_events:
        first = critical_events[0]
        root_cause = (first.get("raw") or "")[:200]

    return {
        "timeline": timeline[:50],
        "attack_stages": stages,
        "root_cause": root_cause or "No clear root cause identified. Review the earliest events in the timeline.",
        "confidence": 0.7 if stages else 0.3,
    }


def _generate_local_reply(message: str, context: list[dict]) -> str:
    lower = message.lower()

    if context:
        ctx = "\n".join(c["chunk_text"][:200] for c in context[:3])
        return f"Based on available context:\n\n{ctx}\n\nRegarding your question about '{message}': "
    if "hello" in lower or "hi " in lower or "hey" in lower:
        return "Hello! I'm your AI Cybersecurity Assistant. How can I help you today?"
    if "help" in lower:
        return "I can help you with:\n1. Analyzing uploaded log files\n2. Explaining security events and Event IDs\n3. Investigating suspicious activity\n4. Providing remediation recommendations\n5. Explaining IOCs, CVEs, and malware behavior\n\nWhat would you like to explore?"

    explained = explain_general(message)
    if explained:
        return explained

    return _get_fallback(message)


def _get_fallback(message: str) -> str:
    lower = message.lower()
    for key, resp in FALLBACK_RESPONSES.items():
        if key in lower:
            return resp
    return FALLBACK_RESPONSES["default"]


def _retrieve_context(message: str) -> list[dict]:
    return search_documents(message, limit=3)


def _extract_evidence(message: str, context: list[dict]) -> list[dict]:
    evidence = []
    if context:
        for c in context[:3]:
            evidence.append({
                "type": c.get("source_type", "document"),
                "source": c.get("source_id", ""),
                "summary": c["chunk_text"][:150],
            })
    return evidence


def _get_suggested_questions(reply: str) -> list[str]:
    if "attack" in reply.lower() or "critical" in reply.lower():
        return ["What is the root cause?", "How do I contain this?", "What IOCs should I block?"]
    if "ioc" in reply.lower() or "indicator" in reply.lower():
        return ["Look up this IP", "What malware is associated?", "Are there related CVEs?"]
    return SUGGESTED_QUESTIONS[:4]


async def _try_provider(provider, session_id: int, history: list[dict], message: str, context: list[dict], fallback: str) -> str | None:
    try:
        messages = [{"role": "system", "content": get_prompt("system")}]
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})
        if context:
            ctx_text = "\n".join(c["chunk_text"][:300] for c in context[:2])
            messages.append({"role": "system", "content": f"Relevant context:\n{ctx_text}"})
        messages.append({"role": "user", "content": message})
        return await provider.chat(messages)
    except Exception:
        return None


def _extract_log_summary(events: list[dict]) -> dict:
    types = {}
    severities = {}
    ips = set()
    for e in events:
        et = e.get("event_type", "unknown")
        types[et] = types.get(et, 0) + 1
        sev = e.get("severity", "info")
        severities[sev] = severities.get(sev, 0) + 1
        if e.get("source_ip"):
            ips.add(e["source_ip"])
    return {
        "total": len(events),
        "event_types": types,
        "severities": severities,
        "unique_ips": len(ips),
    }


def _format_log_data(events: list[dict]) -> str:
    return "\n".join(
        f"[{e.get('line_number')}] {e.get('timestamp', '')} {e.get('source_ip', '')} {e.get('event_type', '')} {e.get('severity', '')}: {e.get('raw', '')}"
        for e in events
    )


def _find_patterns(events: list[dict]) -> list[dict]:
    patterns = []
    failed_attempts = {}
    for e in events:
        raw = (e.get("raw") or "").lower()
        if "failed password" in raw:
            ip = e.get("source_ip", "unknown")
            failed_attempts[ip] = failed_attempts.get(ip, 0) + 1

    for ip, count in failed_attempts.items():
        if count >= 3:
            patterns.append({
                "type": "multiple_failed_logins",
                "description": f"{count} failed logins from {ip}",
                "severity": "high" if count >= 10 else "medium",
                "count": count,
                "ip": ip,
            })
    return patterns


def _build_attack_chain(summary: dict) -> list[str]:
    chain = []
    types = summary.get("event_types", {})
    if any("failed" in k.lower() or "4625" in k for k in types):
        chain.append("Reconnaissance / Brute-Force")
    if any("accepted" in k.lower() or "4624" in k for k in types):
        chain.append("Initial Access")
    if any("4688" in k or "process" in k.lower() for k in types):
        chain.append("Execution")
    if any("7045" in k or "service" in k.lower() for k in types):
        chain.append("Persistence")
    if any("5156" in k or "connection" in k.lower() for k in types):
        chain.append("Command & Control")
    if not chain:
        chain.append("No attack chain identified - events appear benign")
    return chain


def _prioritize_events(events: list[dict]) -> list[dict]:
    return [
        {"priority": "Critical", "count": sum(1 for e in events if e.get("severity") == "critical"), "action": "Immediate investigation required"},
        {"priority": "High", "count": sum(1 for e in events if e.get("severity") == "high"), "action": "Investigate within 1 hour"},
        {"priority": "Medium", "count": sum(1 for e in events if e.get("severity") == "warning"), "action": "Investigate within 24 hours"},
    ]
