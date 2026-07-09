import json
from typing import Optional

import requests


class SIEMConnector:
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("provider", "")

    def send_event(self, event: dict) -> bool:
        if self.provider == "splunk":
            return self._send_splunk(event)
        elif self.provider == "elastic":
            return self._send_elastic(event)
        elif self.provider in ("sentinel", "azuresentinel"):
            return self._send_azure_sentinel(event)
        elif self.provider == "qradar":
            return self._send_qradar(event)
        return False

    def _send_splunk(self, event: dict) -> bool:
        url = self.config.get("url", "").rstrip("/") + "/services/collector"
        token = self.config.get("token", "")
        try:
            resp = requests.post(url, json={"event": event}, headers={"Authorization": f"Splunk {token}"}, timeout=10)
            return resp.ok
        except Exception:
            return False

    def _send_elastic(self, event: dict) -> bool:
        url = self.config.get("url", "").rstrip("/") + "/_bulk"
        api_key = self.config.get("api_key", "")
        index = self.config.get("index", "cybersec-logs")
        action = json.dumps({"index": {"_index": index}})
        body = f"{action}\n{json.dumps(event)}\n"
        try:
            resp = requests.post(url, data=body, headers={"Content-Type": "application/x-ndjson", "Authorization": f"ApiKey {api_key}"}, timeout=10)
            return resp.ok
        except Exception:
            return False

    def _send_azure_sentinel(self, event: dict) -> bool:
        url = self.config.get("url", "")
        workspace_id = self.config.get("workspace_id", "")
        shared_key = self.config.get("shared_key", "")
        log_type = self.config.get("log_type", "CybersecAssistant")
        body = json.dumps(event)
        try:
            resp = requests.post(url, json={"workspace_id": workspace_id, "shared_key": shared_key, "log_type": log_type, "body": body}, timeout=10)
            return resp.ok
        except Exception:
            return False

    def _send_qradar(self, event: dict) -> bool:
        url = self.config.get("url", "").rstrip("/") + "/api/events"
        token = self.config.get("token", "")
        try:
            resp = requests.post(url, json=event, headers={"SEC": token}, timeout=10)
            return resp.ok
        except Exception:
            return False


class EDRConnector:
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("provider", "")

    def get_alerts(self, since: Optional[str] = None) -> list[dict]:
        if self.provider == "defender":
            return self._get_defender_alerts(since)
        elif self.provider == "crowdstrike":
            return self._get_crowdstrike_alerts(since)
        elif self.provider == "sentinelone":
            return self._get_sentinelone_alerts(since)
        return []

    def _get_defender_alerts(self, since: Optional[str] = None) -> list[dict]:
        url = f"{self.config.get('url', '')}/api/alerts"
        try:
            resp = requests.get(url, headers={"Authorization": f"Bearer {self.config.get('token', '')}"}, timeout=10)
            return resp.json().get("value", []) if resp.ok else []
        except Exception:
            return []

    def _get_crowdstrike_alerts(self, since: Optional[str] = None) -> list[dict]:
        url = f"{self.config.get('url', '')}/detects/queries/detects/v1"
        try:
            resp = requests.post(url, headers={"Authorization": f"Bearer {self.config.get('token', '')}"}, timeout=10)
            return resp.json().get("resources", []) if resp.ok else []
        except Exception:
            return []

    def _get_sentinelone_alerts(self, since: Optional[str] = None) -> list[dict]:
        url = f"{self.config.get('url', '')}/web/api/v2.1/threats"
        try:
            resp = requests.get(url, headers={"Authorization": f"Bearer {self.config.get('token', '')}"}, timeout=10)
            return resp.json().get("data", []) if resp.ok else []
        except Exception:
            return []


class CloudConnector:
    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("provider", "")

    def list_instances(self) -> list[dict]:
        if self.provider == "aws":
            return self._list_aws_instances()
        elif self.provider == "azure":
            return self._list_azure_vms()
        elif self.provider == "gcp":
            return self._list_gcp_instances()
        return []

    def _list_aws_instances(self) -> list[dict]:
        try:
            import boto3
            ec2 = boto3.client("ec2", **self.config.get("credentials", {}))
            resp = ec2.describe_instances()
            instances = []
            for r in resp.get("Reservations", []):
                for i in r.get("Instances", []):
                    instances.append({"id": i["InstanceId"], "state": i["State"]["Name"], "type": i["InstanceType"]})
            return instances
        except Exception:
            return []

    def _list_azure_vms(self) -> list[dict]:
        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.compute import ComputeManagementClient
            creds = self.config.get("credentials", {})
            client = ComputeManagementClient(ClientSecretCredential(creds["tenant_id"], creds["client_id"], creds["client_secret"]), creds.get("subscription_id", ""))
            vms = []
            for vm in client.virtual_machines.list_all():
                vms.append({"id": vm.id, "name": vm.name, "location": vm.location})
            return vms
        except Exception:
            return []

    def _list_gcp_instances(self) -> list[dict]:
        try:
            from google.cloud import compute_v1
            creds = self.config.get("credentials", {})
            client = compute_v1.InstancesClient()
            instances = []
            for zone in self.config.get("zones", ["us-central1-a"]):
                for i in client.list(project=creds.get("project", ""), zone=zone):
                    instances.append({"id": i.id, "name": i.name, "zone": zone})
            return instances
        except Exception:
            return []
