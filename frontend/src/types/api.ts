// ─────────────────────────────────────────────────────────────
// AI Cybersecurity Assistant — Shared TypeScript API Models
// Auto-generated from openapi.json + API_CONTRACT.md
// ─────────────────────────────────────────────────────────────

// ── Utility Types ──────────────────────────────────────────

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiError {
  detail: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HttpValidationError {
  detail: ValidationError[];
}

export type Severity = "low" | "medium" | "high" | "critical";
export type Status = "open" | "closed" | "investigating" | "resolved";
export type Role = "admin" | "analyst" | "viewer";

// ── Auth Types ─────────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type?: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  mfa_enabled?: boolean;
}

export interface MfaLoginRequest {
  username: string;
  password: string;
  mfa_code: string;
}

export interface MfaSetupResponse {
  secret: string;
  qr_code: string;
}

export interface MfaVerifyRequest {
  code: string;
}

export interface OAuthLoginRequest {
  provider: string;
  code: string;
  redirect_uri?: string;
}

export interface OAuthRedirectResponse {
  authorization_url: string;
}

export interface LdapLoginRequest {
  server: string;
  base_dn: string;
  username: string;
  password: string;
  user_filter?: string;
  bind_dn?: string;
  bind_password?: string;
  attribute_map?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user?: UserResponse;
}

// ── Health Types ───────────────────────────────────────────

export interface HealthResponse {
  status: string;
  version: string;
  database?: string;
}

// ── Log Types ──────────────────────────────────────────────

export interface UploadLogResponse {
  id: number;
  filename: string;
  size_bytes: number;
  source_type: string;
  status: string;
  event_count: number;
}

export interface LogListItem {
  id: number;
  filename: string;
  source_type: string;
  format: string;
  status: string;
  size_bytes: number;
  event_count: number;
  total_events: number;
  suspicious_count: number;
  created_at: string;
}

export interface LogDetail {
  id: number;
  filename: string;
  source_type: string;
  format: string;
  status: string;
  size_bytes: number;
  event_count: number;
  total_events: number;
  filepath?: string;
  created_at: string;
  suspicious_count: number;
  event_types?: string[];
}

export interface LogEntry {
  id?: number;
  log_id?: number;
  line_number: number;
  timestamp?: string;
  source_ip?: string;
  event_type?: string;
  severity?: string;
  raw: string;
  parsed_json?: string;
  created_at?: string;
}

export interface ExtractedEvent {
  timestamp?: string;
  source_ip?: string;
  event_name: string;
  event_label: string;
  line_number: number;
  severity?: string;
  raw?: string;
}

export interface SuspiciousFinding {
  type: string;
  label: string;
  severity?: string;
  source_ip?: string;
  line_number?: number;
  details?: string;
}

export interface TimelineEntry {
  timestamp: string;
  event_type: string;
  source_ip?: string;
  severity?: string;
  details?: string;
}

export interface AttackChain {
  attack_chain: { phase: string; events: unknown[]; summary: string }[];
}

export interface StatsResponse {
  total_events: number;
  suspicious_events: number;
  severity_distribution: Record<string, number>;
  event_type_distribution: Record<string, number>;
  top_ips: Record<string, unknown>[];
  failed_logins: number;
}

export interface LogSuspiciousQuery {
  log_id: number;
  bf_threshold?: number;
  bf_window?: number;
}

// ── Threat Intel Types ─────────────────────────────────────

export interface IOCExtractionResponse {
  ips?: string[];
  domains?: string[];
  urls?: string[];
  emails?: string[];
  hashes?: Record<string, unknown>[];
}

export interface IOCResult {
  indicator: string;
  indicator_type: string;
  threat_score?: number;
  country?: string;
  asn?: string;
  malware_associations?: string[];
  threat_actor_associations?: string[];
  first_seen?: string;
  last_seen?: string;
  detection_ratio?: string;
  sources?: string[];
}

export interface IOCLookupResponse {
  indicator: string;
  indicator_type: string;
  reputation: IOCResult;
}

export interface IOCSearchResult {
  id: number;
  indicator: string;
  indicator_type: string;
  threat_score: number;
  source: string;
  created_at: string;
}

export interface IOCDetailResponse {
  indicator: string;
  indicator_type: string;
  threat_score: number;
  source: string;
  country: string;
  asn: string;
  malware_associations: string[];
  threat_actor_associations: string[];
  detection_ratio: string;
  first_seen: unknown;
  last_seen: unknown;
  created_at: string;
}

export interface IOCStats {
  total_iocs: number;
  malicious_iocs: number;
  by_type: Record<string, unknown>[];
}

export interface CVEResult {
  cve_id: string;
  description?: string;
  severity?: string;
  score?: number;
  published?: unknown;
}

export interface KEVResult {
  cve_id: string;
  vendor?: string;
  product?: string;
  description?: string;
  date_added?: string;
  required_action?: string;
}

export interface CorrelationResult {
  total_iocs: number;
  repeated_iocs: Record<string, unknown>[];
  campaigns: Record<string, unknown>[];
}

export interface ThreatFeedResponse {
  latest_cves?: Record<string, unknown>[];
  latest_malware?: Record<string, unknown>[];
  latest_ransomware?: Record<string, unknown>[];
  latest_threat_actors?: Record<string, unknown>[];
}

export interface DailySummaryResponse {
  date: string;
  known_exploited_vulnerabilities: Record<string, unknown>[];
  total_kev: number;
}

export interface ThreatFeedItem {
  indicator: string;
  type: string;
  risk: string;
  source: string;
  updated: string;
}

// ── AI Types ───────────────────────────────────────────────

export interface AIProviderInfo {
  name: string;
  available: boolean;
  requires_api_key: boolean;
}

export interface ChatSessionCreate {
  title?: string;
  context_type?: string;
  context_id?: unknown;
}

export interface ChatSessionResponse {
  id: number;
  title: string;
  context_type: string;
  context_id?: unknown;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  session_id: number;
  message: string;
  stream?: boolean;
}

export interface ChatResponse {
  session_id: number;
  reply: string;
  evidence?: Record<string, unknown>[];
  suggested_questions?: string[];
  confidence?: number;
}

export interface ExplainRequest {
  text: string;
  context_type?: string;
}

export interface ExplainResponse {
  explanation: string;
  confidence: number;
  sources?: string[];
}

export interface InvestigationRequest {
  log_id?: unknown;
  evidence?: string;
}

export interface InvestigationResponse {
  summary: string;
  suspicious_patterns?: Record<string, unknown>[];
  critical_events?: Record<string, unknown>[];
  attack_chain?: string[];
  priorities?: Record<string, unknown>[];
  recommendations?: string[];
  confidence?: number;
}

export interface RecommendationResponse {
  next_steps?: string[];
  containment?: string[];
  recovery?: string[];
  patching?: string[];
  detection_improvements?: string[];
}

export interface TimelineAnalysisResponse {
  timeline?: Record<string, unknown>[];
  attack_stages?: string[];
  root_cause?: string;
  confidence?: number;
}

export interface PromptTemplate {
  name: string;
  category: string;
  content: string;
  id?: unknown;
  version?: string;
  is_active?: boolean;
}

// ── Case Management Types ──────────────────────────────────

export interface CaseCreate {
  title: string;
  description?: string;
  case_type?: string;
  severity?: string;
  assigned_analyst?: string;
}

export interface CaseUpdate {
  title?: unknown;
  description?: unknown;
  status?: unknown;
  severity?: unknown;
  case_type?: unknown;
  assigned_analyst?: unknown;
  findings?: unknown;
  root_cause?: unknown;
  impact_assessment?: unknown;
  containment_steps?: unknown;
  recovery_steps?: unknown;
  lessons_learned?: unknown;
  is_archived?: unknown;
}

export interface CaseResponse {
  id: number;
  case_id: string;
  title: string;
  description: string;
  status: string;
  severity: string;
  case_type: string;
  user_id: number;
  assigned_analyst: string;
  findings: string;
  root_cause: string;
  impact_assessment: string;
  containment_steps: string;
  recovery_steps: string;
  lessons_learned: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  closed_at?: unknown;
}

export interface CaseListResponse {
  id: number;
  case_id: string;
  title: string;
  status: string;
  severity: string;
  case_type: string;
  assigned_analyst: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface CaseNoteCreate {
  content: string;
}

export interface CommentCreate {
  content: string;
  is_internal?: boolean;
}

export interface CommentResponse {
  id: number;
  case_id: number;
  user_id: number;
  username?: string;
  content: string;
  is_internal: boolean;
  created_at: string;
}

export interface EvidenceCreate {
  evidence_type: string;
  file_name?: string;
  file_path?: string;
  description?: string;
  source?: string;
}

export interface EvidenceResponse {
  id: number;
  case_id: number;
  evidence_type: string;
  file_name: string;
  file_path: string;
  description: string;
  source: string;
  created_at: string;
}

export interface ReportGenerateRequest {
  title?: string;
  executive_summary?: string;
  technical_summary?: string;
  attack_timeline?: Record<string, unknown>[];
  ioc_list?: Record<string, unknown>[];
  mitre_mapping?: Record<string, unknown>[];
  root_cause?: string;
  impact_assessment?: string;
  containment_steps?: string[];
  recovery_steps?: string[];
  lessons_learned?: string;
}

export interface ReportResponse {
  id: number;
  case_id: number;
  title: string;
  format: string;
  content: string;
  executive_summary: string;
  technical_summary: string;
  attack_timeline: string;
  ioc_list: string;
  mitre_mapping: string;
  created_at: string;
  updated_at: string;
}

export interface TemplateCreate {
  name: string;
  content: string;
  category?: string;
  is_default?: boolean;
}

export interface TemplateResponse {
  id: number;
  name: string;
  category: string;
  content: string;
  is_default: boolean;
  created_at: string;
}

export interface ActivityResponse {
  id: number;
  case_id: number;
  user_id: number;
  username?: string;
  action: string;
  details: string;
  created_at: string;
}

export interface AuditLogResponse {
  id: number;
  user_id: number;
  username?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string;
  ip_address: string;
  created_at: string;
}

// ── Dashboard Types ────────────────────────────────────────

export interface ExecutiveSummary {
  total_alerts: number;
  critical_alerts: number;
  open_cases: number;
  active_investigations: number;
  total_iocs: number;
  total_assets: number;
  high_risk_assets: number;
  risk_score: number;
  security_health: string;
}

export interface AlertStats {
  total: number;
  by_severity: Record<string, unknown>;
  by_status: Record<string, unknown>;
  by_type: Record<string, unknown>;
  recent: Record<string, unknown>[];
}

export interface InvestigationStats {
  total: number;
  open: number;
  closed: number;
  in_progress: number;
  by_severity: Record<string, unknown>;
  avg_resolution_time: string;
}

export interface ThreatIntelStats {
  total_iocs: number;
  by_type: Record<string, unknown>;
  top_threats: Record<string, unknown>[];
  recent_cves: string[];
  recent_malware: string[];
}

export interface LogStats {
  total_events: number;
  by_severity: Record<string, unknown>;
  by_event_type: Record<string, unknown>;
  top_source_ips: Record<string, unknown>[];
  recent_activity: Record<string, unknown>[];
}

export interface AlertCreate {
  title: string;
  description?: string;
  severity?: string;
  status?: string;
  alert_type?: string;
  source?: string;
  source_id?: string;
  assigned_to?: string;
  ioc_value?: string;
  event_count?: number;
  raw_data?: string;
}

export interface AlertResponse {
  id: number;
  title: string;
  description: string;
  severity: string;
  status: string;
  alert_type: string;
  source: string;
  source_id: string;
  user_id: number;
  assigned_to: string;
  ioc_value: string;
  event_count: number;
  raw_data: string;
  resolved_at?: unknown;
  created_at: string;
  updated_at: string;
}

export interface AlertUpdate {
  title?: unknown;
  description?: unknown;
  severity?: unknown;
  status?: unknown;
  alert_type?: unknown;
  assigned_to?: unknown;
  event_count?: unknown;
}

export interface DashboardSummary {
  executive: ExecutiveSummary;
  alerts: AlertStats;
  investigations: InvestigationStats;
  threat_intel: ThreatIntelStats;
  assets: AssetResponse[];
  log_stats: LogStats;
  notifications: NotificationResponse[];
}

export interface AssetCreate {
  hostname?: string;
  ip_address?: string;
  asset_type?: string;
  os?: string;
  department?: string;
  location?: string;
  owner?: string;
  risk_score?: number;
  criticality?: string;
  is_active?: boolean;
  tags?: string;
  last_seen?: string;
}

export interface AssetResponse {
  id: number;
  hostname: string;
  ip_address: string;
  asset_type: string;
  os: string;
  department: string;
  location: string;
  owner: string;
  risk_score: number;
  criticality: string;
  is_active: boolean;
  tags: string;
  last_seen?: unknown;
  created_at: string;
  updated_at: string;
}

export interface AssetUpdate {
  hostname?: unknown;
  ip_address?: unknown;
  asset_type?: unknown;
  os?: unknown;
  department?: unknown;
  location?: unknown;
  owner?: unknown;
  risk_score?: unknown;
  criticality?: unknown;
  is_active?: unknown;
  tags?: unknown;
  last_seen?: unknown;
}

export interface NotificationCreate {
  title: string;
  message?: string;
  notification_type?: string;
  severity?: string;
  link?: string;
}

export interface NotificationResponse {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: string;
  severity: string;
  is_read: boolean;
  link: string;
  created_at: string;
}

export interface UserSettingsResponse {
  id: number;
  user_id: number;
  preferences: string;
  notification_config: string;
  dashboard_layout: string;
  updated_at: string;
}

export interface UserSettingsUpdate {
  preferences?: unknown;
  notification_config?: unknown;
  dashboard_layout?: unknown;
}

// ── Detection Types ────────────────────────────────────────

export interface DetectionRuleCreate {
  name: string;
  description?: string;
  rule_type?: string;
  rule_format?: string;
  category?: string;
  content?: string;
  severity?: string;
  mitre_attack_id?: string;
}

export interface DetectionRuleResponse {
  id: number;
  name: string;
  description: string;
  rule_type: string;
  rule_format: string;
  category: string;
  content: string;
  severity: string;
  mitre_attack_id: string;
  enabled: boolean;
  hit_count: number;
  false_positive_count: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface DetectionRuleUpdate {
  name?: unknown;
  description?: unknown;
  category?: unknown;
  content?: unknown;
  severity?: unknown;
  mitre_attack_id?: unknown;
  enabled?: unknown;
}

export interface RuleTestResult {
  rule_id: number;
  matched: boolean;
  matches?: Record<string, unknown>[];
  execution_time_ms?: number;
  error?: string;
}

export interface SigmaRuleCreate {
  title: string;
  description?: string;
  author?: string;
  rule_id?: string;
  logsource_category?: string;
  logsource_product?: string;
  logsource_service?: string;
  detection?: string;
  fields?: string;
  falsepositives?: string;
  level?: string;
  tags?: string;
  status?: string;
  content?: string;
}

export interface SigmaRuleResponse {
  id: number;
  title: string;
  description: string;
  author: string;
  rule_id: string;
  logsource_category: string;
  logsource_product: string;
  logsource_service: string;
  detection: string;
  fields: string;
  falsepositives: string;
  level: string;
  tags: string;
  status: string;
  content: string;
  enabled: boolean;
  hit_count: number;
  created_at: string;
  updated_at: string;
}

export interface YARARuleCreate {
  name: string;
  content: string;
  description?: string;
  author?: string;
  rule_id?: string;
  tags?: string;
  malware_family?: string;
  reference?: string;
}

export interface YARARuleResponse {
  id: number;
  name: string;
  description: string;
  author: string;
  rule_id: string;
  content: string;
  tags: string;
  malware_family: string;
  reference: string;
  enabled: boolean;
  hit_count: number;
  compiled: boolean;
  created_at: string;
  updated_at: string;
}

export interface SavedHuntCreate {
  name: string;
  description?: string;
  hunt_type?: string;
  query?: string;
  filters?: string;
}

export interface SavedHuntResponse {
  id: number;
  name: string;
  description: string;
  hunt_type: string;
  query: string;
  filters: string;
  user_id: number;
  is_scheduled: boolean;
  last_run?: unknown;
  created_at: string;
  updated_at: string;
}

export interface HuntResultResponse {
  id: number;
  hunt_id?: unknown;
  hunt_type: string;
  match_type: string;
  match_value: string;
  source: string;
  severity: string;
  context: string;
  user_id: number;
  created_at: string;
}

export interface ScheduledJobCreate {
  name: string;
  job_type: string;
  config?: string;
  schedule_interval?: string;
}

export interface ScheduledJobResponse {
  id: number;
  name: string;
  job_type: string;
  config: string;
  schedule_interval: string;
  is_active: boolean;
  last_run?: unknown;
  next_run?: unknown;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface AlertAutomationCreate {
  name: string;
  trigger_type: string;
  description?: string;
  conditions?: string;
  actions?: string;
  priority?: number;
}

export interface AlertAutomationResponse {
  id: number;
  name: string;
  description: string;
  trigger_type: string;
  conditions: string;
  actions: string;
  is_active: boolean;
  priority: number;
  hit_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowPlaybookCreate {
  name: string;
  description?: string;
  category?: string;
  steps?: string;
}

export interface WorkflowPlaybookResponse {
  id: number;
  name: string;
  description: string;
  category: string;
  steps: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface HuntingReportCreate {
  title: string;
  hunt_type?: string;
  summary?: string;
  findings?: string;
  ioc_list?: string;
  rule_matches?: string;
  statistics?: string;
}

export interface HuntingReportResponse {
  id: number;
  title: string;
  hunt_type: string;
  summary: string;
  findings: string;
  ioc_list: string;
  rule_matches: string;
  statistics: string;
  user_id: number;
  created_at: string;
}

export interface AnalyticsResponse {
  total_rules: number;
  enabled_rules: number;
  total_hits: number;
  false_positives: number;
  false_positive_rate: number;
  by_category: Record<string, unknown>;
  by_severity: Record<string, unknown>;
  by_mitre: Record<string, unknown>;
  top_rules: Record<string, unknown>[];
  hunting_metrics: Record<string, unknown>;
}

// ── Enterprise Types ───────────────────────────────────────

export interface NotificationConfigCreate {
  channel: string;
  event: string;
  config?: Record<string, unknown>;
}

export interface NotificationConfigResponse {
  id: number;
  channel: string;
  event: string;
  config: string;
  enabled: boolean;
}

export interface SendNotificationRequest {
  channel: string;
  event: string;
  data?: Record<string, unknown>;
  to?: string;
  webhook_url?: string;
}

export interface OrgCreate {
  name: string;
  slug?: string;
}

export interface OrgResponse {
  id: number;
  name: string;
  slug: string;
  owner_id: number;
  settings: string;
  max_users: number;
  max_storage_mb: number;
  created_at: string;
}

export interface OrgMemberAdd {
  user_id: number;
  role?: string;
}

export interface PlanChange {
  plan: string;
}

export interface SubscriptionResponse {
  id: number;
  org_id: number;
  plan: string;
  status: string;
  user_limit: number;
  storage_limit_mb: number;
  api_limit: number;
}

export interface IntegrationCreate {
  provider: string;
  config?: Record<string, unknown>;
}

export interface IntegrationResponse {
  id: number;
  provider: string;
  config: string;
  enabled: boolean;
  last_sync?: string;
}

export interface IntegrationEventSend {
  event: Record<string, unknown>;
}

export interface BackupResponse {
  id: number;
  type: string;
  path: string;
  size_bytes: number;
  status: string;
  created_at: string;
}

// ── Plugin Types ───────────────────────────────────────────

export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  plugin_type: string;
  description: string;
  author: string;
  enabled: boolean;
  config: Record<string, string>;
  settings_schema: Record<string, unknown>;
}

// ── Upload Types ───────────────────────────────────────────

export interface FileUploadPayload {
  file: File | Blob;
  filename: string;
}

// ── API Endpoint Response Composites ───────────────────────
// These are endpoint-specific response shapes not captured by
// a single schema, or endpoint responses that have empty
// schemas in OpenAPI.

export interface ExecutiveSummaryResponse {
  total_alerts: number;
  critical_alerts: number;
  open_cases: number;
  active_threats: number;
  total_iocs: number;
  recent_activity: { action: string; timestamp: string }[];
}

export interface ChartData {
  labels: string[];
  datasets: { label: string; data: number[] }[];
}

export interface ApiMetricEntry {
  id: number;
  endpoint: string;
  method: string;
  status_code: number;
  duration_ms: number;
  timestamp: string;
}

export interface ApiMetricStats {
  total_requests: number;
  avg_duration_ms: number;
  top_endpoints: { endpoint: string; hits: number; avg_dur: number }[];
}

export interface CorrelateIocsRequest {
  iocs: string[];
}

export interface CorrelateIocsResponse {
  groups: { name: string; type: string; iocs: string[]; reputation: string }[];
  total: number;
}

export interface RAGSearchResponse {
  results: Record<string, unknown>[];
  total: number;
}

export interface RAGIndexResponse {
  indexed: boolean;
  chunks: number;
}

// ── Enums / Constants ──────────────────────────────────────

export const SEVERITY_LEVELS = ["low", "medium", "high", "critical"] as const;
export type SeverityLevel = (typeof SEVERITY_LEVELS)[number];

export const CASE_STATUSES = ["open", "closed", "investigating"] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];

export const IOC_TYPES = ["ip", "domain", "url", "md5", "sha1", "sha256", "email"] as const;
export type IOCType = (typeof IOC_TYPES)[number];

export const ALERT_STATUSES = ["open", "investigating", "resolved"] as const;
export type AlertStatus = (typeof ALERT_STATUSES)[number];

export const SOURCE_TYPES = [
  "linux_auth", "windows_event", "syslog", "apache_access",
  "apache_error", "nginx_access", "firewall", "custom",
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

// Generated 78 interfaces + 12 composite types = 90 total
