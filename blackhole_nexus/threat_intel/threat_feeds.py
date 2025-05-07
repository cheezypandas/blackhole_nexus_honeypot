import requests
import json
from datetime import datetime

ABUSEIPDB_API_KEY = "YOUR_API_KEY"
VT_API_KEY = "YOUR_VIRUSTOTAL_KEY"

class ThreatIntel:
    def __init__(self):
        self.log_file = "/var/log/threat_intel.json"
        
    def check_ip(self, ip):
        """Check IP against AbuseIPDB and VirusTotal"""
        results = {}
        
        # AbuseIPDB Check
        try:
            url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}"
            headers = {"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"}
            response = requests.get(url, headers=headers)
            abuse_data = response.json().get("data", {})
            results["abuseipdb"] = {
                "score": abuse_data.get("abuseConfidenceScore", 0),
                "isp": abuse_data.get("isp", "Unknown")
            }
        except Exception as e:
            results["abuseipdb_error"] = str(e)
        
        # VirusTotal Check
        try:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
            headers = {"x-apikey": VT_API_KEY}
            response = requests.get(url, headers=headers)
            vt_data = response.json().get("data", {}).get("attributes", {})
            results["virustotal"] = {
                "malicious": vt_data.get("last_analysis_stats", {}).get("malicious", 0)
            }
        except Exception as e:
            results["virustotal_error"] = str(e)
        
        self._log_result(ip, results)
        return results
    
    def _log_result(self, ip, data):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "ip": ip,
            "results": data
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

if __name__ == "__main__":
    ti = ThreatIntel()
    print(ti.check_ip("8.8.8.8"))  # Test with Google DNS