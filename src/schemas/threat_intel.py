from pydantic import BaseModel


class IOCResult(BaseModel):
    indicator: str
    indicator_type: str
    threat_score: float = 0
    country: str = ""
    asn: str = ""
    malware_associations: list[str] = []
    threat_actor_associations: list[str] = []
    first_seen: str | None = None
    last_seen: str | None = None
    detection_ratio: str = "0/0"
    sources: list[str] = []


class IOCExtractionResponse(BaseModel):
    ips: list[str] = []
    domains: list[str] = []
    urls: list[str] = []
    emails: list[str] = []
    hashes: list[dict] = []


class IOCLookupResponse(BaseModel):
    indicator: str
    indicator_type: str
    reputation: IOCResult


class IOCSearchResult(BaseModel):
    id: int
    indicator: str
    indicator_type: str
    threat_score: float
    source: str
    created_at: str


class IOCDetailResponse(BaseModel):
    indicator: str
    indicator_type: str
    threat_score: float
    source: str
    country: str
    asn: str
    malware_associations: list[str]
    threat_actor_associations: list[str]
    detection_ratio: str
    first_seen: str | None
    last_seen: str | None
    created_at: str


class IOCStats(BaseModel):
    total_iocs: int
    malicious_iocs: int
    by_type: list[dict]


class CorrelationResult(BaseModel):
    total_iocs: int
    repeated_iocs: list[dict]
    campaigns: list[dict]


class CVEResult(BaseModel):
    cve_id: str
    description: str = ""
    severity: str = ""
    score: float = 0
    published: str | None = None


class KEVResult(BaseModel):
    cve_id: str
    vendor: str = ""
    product: str = ""
    description: str = ""
    date_added: str = ""
    required_action: str = ""


class ThreatFeedResponse(BaseModel):
    latest_cves: list[dict] = []
    latest_malware: list[dict] = []
    latest_ransomware: list[dict] = []
    latest_threat_actors: list[dict] = []


class DailySummaryResponse(BaseModel):
    date: str
    known_exploited_vulnerabilities: list[dict]
    total_kev: int
