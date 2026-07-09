SYSTEM_PROMPT = """You are an AI Cybersecurity Assistant helping a SOC analyst investigate security events.
Always ground your answers in the provided evidence. If you don't know something, say so.
Include confidence levels in your responses. Be concise and technical."""

INVESTIGATION_PROMPT = """Analyze the following log data and identify:
1. Suspicious patterns and events
2. Critical events that require immediate attention
3. The attack chain / kill chain phases
4. Prioritized list of alerts
5. Confidence level for each finding

Log data:
{log_data}"""

THREAT_ANALYSIS_PROMPT = """Analyze the following threat intelligence data:
- IOC: {indicator}
- Type: {ioc_type}
- Threat Score: {score}
- Associated Malware: {malware}
- Associated Threat Actors: {actors}

Provide a concise threat assessment."""

REPORT_PROMPT = """Generate a cybersecurity incident report based on:
- Investigation Summary: {summary}
- Events Found: {events}
- IOCs Identified: {iocs}
- Attack Chain: {chain}
- Recommendations: {recommendations}

Format as a structured report."""


DEFAULT_PROMPTS: dict[str, str] = {
    "system": SYSTEM_PROMPT,
    "investigation": INVESTIGATION_PROMPT,
    "threat_analysis": THREAT_ANALYSIS_PROMPT,
    "report": REPORT_PROMPT,
}


def get_prompt(name: str) -> str:
    return DEFAULT_PROMPTS.get(name, SYSTEM_PROMPT)


def list_prompts() -> list[dict]:
    return [
        {"name": k, "category": _category(k), "content": v[:100] + "...", "version": "1.0", "is_active": True}
        for k, v in DEFAULT_PROMPTS.items()
    ]


def _category(name: str) -> str:
    mapping = {
        "system": "system",
        "investigation": "investigation",
        "threat_analysis": "threat_analysis",
        "report": "report",
    }
    return mapping.get(name, "general")
