#!/usr/bin/env python3
import sys
import pexpect

HOST = "192.168.2.2"
USER = "pi"
PASSWORD = "password123"

with open("/Users/sujithputta/.ssh/id_ed25519.pub", "r") as f:
    pub_key = f.read().strip()

cmd = f"\"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{pub_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
ssh_cmd = f"ssh -o StrictHostKeyChecking=no {USER}@{HOST} {cmd}"

print(f"Installing SSH key onto {USER}@{HOST}...")
child = pexpect.spawn(ssh_cmd, timeout=15)
idx = child.expect(["password:", "Password:", pexpect.EOF, pexpect.TIMEOUT])
if idx in (0, 1):
    child.sendline(PASSWORD)
    child.expect(pexpect.EOF)

print("✅ Passwordless SSH key installed successfully!")
