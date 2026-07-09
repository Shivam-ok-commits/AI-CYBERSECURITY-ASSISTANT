import sqlite3
from contextlib import contextmanager

from src.config import settings


def get_connection():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'analyst',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                source_type TEXT NOT NULL DEFAULT 'unknown',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open',
                severity TEXT NOT NULL DEFAULT 'medium',
                findings TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                investigation_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                format TEXT NOT NULL DEFAULT 'markdown',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE SET NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threat_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT UNIQUE NOT NULL,
                indicator_type TEXT NOT NULL,
                threat_score REAL NOT NULL DEFAULT 0.0,
                source TEXT NOT NULL DEFAULT '',
                raw_data TEXT NOT NULL DEFAULT '',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS parsed_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                timestamp TEXT,
                source_ip TEXT,
                event_type TEXT,
                severity TEXT,
                raw TEXT NOT NULL,
                parsed_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (log_id) REFERENCES uploaded_logs(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ioc_reputation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT UNIQUE NOT NULL,
                indicator_type TEXT NOT NULL,
                threat_score REAL NOT NULL DEFAULT 0.0,
                source TEXT NOT NULL DEFAULT '',
                country TEXT NOT NULL DEFAULT '',
                asn TEXT NOT NULL DEFAULT '',
                malware_associations TEXT NOT NULL DEFAULT '[]',
                threat_actor_associations TEXT NOT NULL DEFAULT '[]',
                first_seen TEXT,
                last_seen TEXT,
                detection_ratio TEXT NOT NULL DEFAULT '0/0',
                raw_data TEXT NOT NULL DEFAULT '{}',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ioc_correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator TEXT NOT NULL,
                indicator_type TEXT NOT NULL,
                log_id INTEGER NOT NULL,
                event_line INTEGER NOT NULL DEFAULT 0,
                context TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (log_id) REFERENCES uploaded_logs(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ioc_corr_indicator ON ioc_correlations(indicator)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ioc_reputation_indicator ON ioc_reputation(indicator)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New Chat',
                context_type TEXT NOT NULL DEFAULT 'general',
                context_id INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                message_id INTEGER,
                evidence_type TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                evidence_summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_text TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL DEFAULT '',
                metadata TEXT NOT NULL DEFAULT '{}',
                embedding TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','closed')),
                severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
                case_type TEXT NOT NULL DEFAULT 'incident' CHECK(case_type IN ('malware','phishing','brute_force','web_attack','insider_threat','custom','incident')),
                user_id INTEGER NOT NULL,
                assigned_analyst TEXT NOT NULL DEFAULT '',
                findings TEXT NOT NULL DEFAULT '',
                root_cause TEXT NOT NULL DEFAULT '',
                impact_assessment TEXT NOT NULL DEFAULT '',
                containment_steps TEXT NOT NULL DEFAULT '[]',
                recovery_steps TEXT NOT NULL DEFAULT '[]',
                lessons_learned TEXT NOT NULL DEFAULT '',
                is_archived INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                closed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_case_id ON cases(case_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_severity ON cases(severity)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cases_archived ON cases(is_archived)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                evidence_type TEXT NOT NULL CHECK(evidence_type IN ('file','screenshot','ioc','malware_report','log','other')),
                file_name TEXT NOT NULL DEFAULT '',
                file_path TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_evidence_case ON case_evidence(case_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'markdown' CHECK(format IN ('markdown','html','json','pdf')),
                content TEXT NOT NULL DEFAULT '',
                executive_summary TEXT NOT NULL DEFAULT '',
                technical_summary TEXT NOT NULL DEFAULT '',
                attack_timeline TEXT NOT NULL DEFAULT '[]',
                ioc_list TEXT NOT NULL DEFAULT '[]',
                mitre_mapping TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_reports_case ON case_reports(case_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_internal INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_comments_case ON case_comments(case_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS case_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_activity_case ON case_activity(case_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT '',
                ip_address TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL DEFAULT 'custom',
                content TEXT NOT NULL,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('malware_incident', 'malware', '## Malware Incident Report\n\n### Executive Summary\n{{executive_summary}}\n\n### Technical Summary\n{{technical_summary}}\n\n### Indicators of Compromise\n{{ioc_list}}\n\n### MITRE ATT&CK Mapping\n{{mitre_mapping}}\n\n### Containment\n{{containment_steps}}\n\n### Recovery\n{{recovery_steps}}\n\n### Lessons Learned\n{{lessons_learned}}', 1)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('phishing_incident', 'phishing', '## Phishing Incident Report\n\n### Executive Summary\n{{executive_summary}}\n\n### Indicators\n{{ioc_list}}\n\n### Affected Users\n{{affected_users}}\n\n### Remediation\n{{containment_steps}}\n\n### Lessons Learned\n{{lessons_learned}}', 1)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('brute_force_attack', 'brute_force', '## Brute Force Attack Report\n\n### Executive Summary\n{{executive_summary}}\n\n### Attack Details\n{{technical_summary}}\n\n### Source IPs\n{{source_ips}}\n\n### Affected Accounts\n{{affected_accounts}}\n\n### Recommendations\n{{containment_steps}}\n\n### Recovery\n{{recovery_steps}}', 1)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('web_attack', 'web_attack', '## Web Attack Report\n\n### Executive Summary\n{{executive_summary}}\n\n### Attack Vector\n{{technical_summary}}\n\n### Affected Endpoints\n{{affected_endpoints}}\n\n### IOCs\n{{ioc_list}}\n\n### Mitigation\n{{containment_steps}}', 1)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('insider_threat', 'insider_threat', '## Insider Threat Report\n\n### Executive Summary\n{{executive_summary}}\n\n### User Activity\n{{technical_summary}}\n\n### Evidence\n{{evidence_list}}\n\n### Impact Assessment\n{{impact_assessment}}\n\n### Recommendations\n{{containment_steps}}', 1)
        """)
        conn.execute("""
            INSERT OR IGNORE INTO report_templates (name, category, content, is_default)
            VALUES ('custom', 'custom', '## Incident Report\n\n### Executive Summary\n{{executive_summary}}\n\n### Details\n{{technical_summary}}\n\n### Timeline\n{{attack_timeline}}\n\n### IOCs\n{{ioc_list}}\n\n### MITRE ATT&CK\n{{mitre_mapping}}\n\n### Root Cause\n{{root_cause}}\n\n### Impact\n{{impact_assessment}}\n\n### Containment\n{{containment_steps}}\n\n### Recovery\n{{recovery_steps}}\n\n### Lessons Learned\n{{lessons_learned}}', 1)
        """)
        # ── Phase 7 tables ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','acknowledged','investigating','resolved','dismissed')),
                alert_type TEXT NOT NULL DEFAULT 'other' CHECK(alert_type IN ('malware','ioc','brute_force','phishing','anomaly','policy','vulnerability','threat_intel','other')),
                source TEXT NOT NULL DEFAULT '',
                source_id TEXT NOT NULL DEFAULT '',
                user_id INTEGER NOT NULL DEFAULT 0,
                assigned_to TEXT NOT NULL DEFAULT '',
                ioc_value TEXT NOT NULL DEFAULT '',
                event_count INTEGER NOT NULL DEFAULT 0,
                raw_data TEXT NOT NULL DEFAULT '{}',
                resolved_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT NOT NULL DEFAULT '',
                ip_address TEXT NOT NULL DEFAULT '',
                asset_type TEXT NOT NULL DEFAULT 'host' CHECK(asset_type IN ('host','server','endpoint','network_device','cloud','application','database','other')),
                os TEXT NOT NULL DEFAULT '',
                department TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '',
                risk_score REAL NOT NULL DEFAULT 0.0,
                criticality TEXT NOT NULL DEFAULT 'medium' CHECK(criticality IN ('low','medium','high','critical')),
                is_active INTEGER NOT NULL DEFAULT 1,
                tags TEXT NOT NULL DEFAULT '[]',
                last_seen TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_ip ON assets(ip_address)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_risk ON assets(risk_score)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_assets_criticality ON assets(criticality)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                notification_type TEXT NOT NULL DEFAULT 'info' CHECK(notification_type IN ('alert','ioc','malware','investigation','threat_feed','system','info')),
                severity TEXT NOT NULL DEFAULT 'info' CHECK(severity IN ('info','low','medium','high','critical')),
                is_read INTEGER NOT NULL DEFAULT 0,
                link TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id, is_read)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                preferences TEXT NOT NULL DEFAULT '{}',
                notification_config TEXT NOT NULL DEFAULT '{}',
                dashboard_layout TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        # ── Phase 8 tables ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detection_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                rule_type TEXT NOT NULL DEFAULT 'custom' CHECK(rule_type IN ('sigma','yara','custom')),
                rule_format TEXT NOT NULL DEFAULT 'custom' CHECK(rule_format IN ('sigma','yara','custom','query','regex')),
                category TEXT NOT NULL DEFAULT 'general' CHECK(category IN ('malware','phishing','brute_force','web_attack','insider_threat','lateral_movement','persistence','execution','credential_access','exfiltration','general','custom')),
                content TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
                mitre_attack_id TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                hit_count INTEGER NOT NULL DEFAULT 0,
                false_positive_count INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_detection_rules_type ON detection_rules(rule_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_detection_rules_category ON detection_rules(category)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_detection_rules_enabled ON detection_rules(enabled)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sigma_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                author TEXT NOT NULL DEFAULT '',
                rule_id TEXT UNIQUE NOT NULL DEFAULT '',
                logsource_category TEXT NOT NULL DEFAULT '',
                logsource_product TEXT NOT NULL DEFAULT '',
                logsource_service TEXT NOT NULL DEFAULT '',
                detection TEXT NOT NULL DEFAULT '{}',
                fields TEXT NOT NULL DEFAULT '[]',
                falsepositives TEXT NOT NULL DEFAULT '[]',
                level TEXT NOT NULL DEFAULT 'medium',
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'experimental' CHECK(status IN ('experimental','stable','deprecated','unsupported')),
                content TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                hit_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sigma_level ON sigma_rules(level)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS yara_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                author TEXT NOT NULL DEFAULT '',
                rule_id TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                malware_family TEXT NOT NULL DEFAULT '',
                reference TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                hit_count INTEGER NOT NULL DEFAULT 0,
                compiled INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_yara_name ON yara_rules(name)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_hunts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                hunt_type TEXT NOT NULL DEFAULT 'log' CHECK(hunt_type IN ('log','ioc','process','network','user','custom')),
                query TEXT NOT NULL DEFAULT '',
                filters TEXT NOT NULL DEFAULT '{}',
                user_id INTEGER NOT NULL,
                is_scheduled INTEGER NOT NULL DEFAULT 0,
                last_run TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_saved_hunts_type ON saved_hunts(hunt_type)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                job_type TEXT NOT NULL CHECK(job_type IN ('log_analysis','ioc_check','threat_feed_update','malware_analysis','hunt','report')),
                config TEXT NOT NULL DEFAULT '{}',
                schedule_interval TEXT NOT NULL DEFAULT 'daily' CHECK(schedule_interval IN ('once','hourly','daily','weekly','monthly')),
                is_active INTEGER NOT NULL DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_type ON scheduled_jobs(job_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_active ON scheduled_jobs(is_active)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_automation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                trigger_type TEXT NOT NULL CHECK(trigger_type IN ('alert_created','alert_severity','alert_type','ioc_detected','rule_match','schedule')),
                conditions TEXT NOT NULL DEFAULT '{}',
                actions TEXT NOT NULL DEFAULT '[]',
                is_active INTEGER NOT NULL DEFAULT 1,
                priority INTEGER NOT NULL DEFAULT 0,
                hit_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_playbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'general' CHECK(category IN ('malware','phishing','brute_force','web_attack','insider_threat','general')),
                steps TEXT NOT NULL DEFAULT '[]',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hunt_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hunt_id INTEGER,
                hunt_type TEXT NOT NULL DEFAULT 'log',
                match_type TEXT NOT NULL DEFAULT '',
                match_value TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL DEFAULT 'medium',
                context TEXT NOT NULL DEFAULT '{}',
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (hunt_id) REFERENCES saved_hunts(id) ON DELETE SET NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hunt_results_type ON hunt_results(hunt_type)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rule_hits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL CHECK(rule_type IN ('detection','sigma','yara')),
                rule_id INTEGER NOT NULL,
                event_source TEXT NOT NULL DEFAULT '',
                match_detail TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL DEFAULT 'medium',
                is_false_positive INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_rule_hits_type ON rule_hits(rule_type, rule_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hunting_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                hunt_type TEXT NOT NULL DEFAULT 'log',
                summary TEXT NOT NULL DEFAULT '',
                findings TEXT NOT NULL DEFAULT '[]',
                ioc_list TEXT NOT NULL DEFAULT '[]',
                rule_matches TEXT NOT NULL DEFAULT '[]',
                statistics TEXT NOT NULL DEFAULT '{}',
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        for col_sql in [
            "ALTER TABLE users ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE users ADD COLUMN mfa_secret TEXT NOT NULL DEFAULT ''",
        ]:
            try:
                conn.execute(col_sql)
            except Exception:
                pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                provider_email TEXT NOT NULL DEFAULT '',
                access_token TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(provider, provider_user_id)
            )
        """)
        # ── 9.x tables ──
        conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL DEFAULT 0,
                max_users INTEGER NOT NULL DEFAULT 10,
                max_storage_mb INTEGER NOT NULL DEFAULT 1024,
                settings TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS org_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(org_id, user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                plan TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                api_limit INTEGER NOT NULL DEFAULT 1000,
                user_limit INTEGER NOT NULL DEFAULT 5,
                storage_limit_mb INTEGER NOT NULL DEFAULT 512,
                stripe_customer_id TEXT NOT NULL DEFAULT '',
                stripe_subscription_id TEXT NOT NULL DEFAULT '',
                current_period_start TEXT,
                current_period_end TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                channel TEXT NOT NULL DEFAULT 'email',
                event TEXT NOT NULL DEFAULT '',
                config TEXT NOT NULL DEFAULT '{}',
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL DEFAULT 0,
                provider TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}',
                enabled INTEGER NOT NULL DEFAULT 1,
                last_sync TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'GET',
                status_code INTEGER NOT NULL DEFAULT 200,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                user_id INTEGER,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                type TEXT NOT NULL DEFAULT 'manual',
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
