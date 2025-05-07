#!/bin/bash

echo "[+] Simulating attacks against Blackhole Nexus..."

# 1. Trigger Cowrie logs via SSH
echo "[🐝] Attempting SSH to Cowrie honeypot..."
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1 "exit" || true

# 2. Trigger syscall hooks
echo "[🔧] Triggering syscall activity..."
whoami
ls /etc
cat /etc/passwd > /dev/null
mkdir /tmp/fake_attack_dir
rm -rf /tmp/fake_attack_dir

# 3. Trigger Threat Intelligence Lookup
echo "[🌐] Making suspicious outbound connection to trigger Threat Intel..."
curl -s --max-time 5 http://185.199.110.153 > /dev/null || true

echo "[✔] Simulation complete. Check your log files."
