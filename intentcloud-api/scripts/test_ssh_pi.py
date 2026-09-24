#!/usr/bin/env python3
import sys
import pexpect

HOST = "192.168.2.2"
USER = "pi"
PASSWORD = "password123"

def run_remote(cmd: str, timeout: int = 30) -> str:
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {USER}@{HOST} {cmd}"
    child = pexpect.spawn(ssh_cmd, timeout=timeout)
    idx = child.expect(["password:", "Password:", pexpect.EOF, pexpect.TIMEOUT])
    if idx in (0, 1):
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF)
    output = child.before.decode("utf-8", errors="ignore") if child.before else ""
    return output

if __name__ == "__main__":
    print(f"Connecting to Raspberry Pi at {USER}@{HOST}...")
    try:
        sys_info = run_remote("'uname -a && free -h'")
        print(sys_info)
        print("\n✅ Raspberry Pi SSH Connection SUCCESSFUL!")
    except Exception as e:
        print(f"❌ Error connecting: {e}")
