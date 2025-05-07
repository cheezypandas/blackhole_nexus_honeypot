from impacket import smbserver
import logging
import json
from datetime import datetime

class CustomSMB(smbserver.SimpleSMBServer):
    def __init__(self):
        super().__init__()
        self.setLogFile("/var/log/smb_honeypot.log")
        
    def logEvent(self, event):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "source_ip": self._ClientInfo.getRemoteAddress(),
            "event": event
        }
        with open("/var/log/smb_audit.json", "a") as f:
            f.write(json.dumps(entry) + "\n")

server = CustomSMB()
server.addShare("HR_DOCS", "/tmp/fake_share", "Fake HR Documents")
server.setSMB2Support(True)
server.addCredential("admin", 0, "aad3b435b51404eeaad3b435b51404ee")  # Empty NTLM hash
print("[+] SMB honeypot running on 0.0.0.0:445")
server.start()