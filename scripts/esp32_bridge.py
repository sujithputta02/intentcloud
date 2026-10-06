#!/usr/bin/env python3
"""
IntentCloud ESP32 Serial Telemetry Bridge
Keeps a persistent USB Serial connection to the ESP32 OLED Display (/dev/cu.usbserial-5C790748651)
Provides an ultra-low latency local HTTP endpoint (http://127.0.0.1:8765/push)
so the Next.js frontend search pipeline can instantly stream live telemetry stages directly
to the physical OLED screen in real-time.
"""

import sys
import os
import time
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import serial

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("ESP32Bridge")

PORT = 8765
SERIAL_PORT = "/dev/cu.usbserial-5C790748651"
BAUD_RATE = 115200
PI_API_URL = "http://192.168.2.2:8000/device/oled"

serial_lock = threading.Lock()
ser = None
last_manual_push = 0

def init_serial():
    global ser
    try:
        if ser and ser.is_open:
            ser.close()
        ser = serial.Serial(
            SERIAL_PORT,
            BAUD_RATE,
            timeout=1,
            dsrdtr=False,
            rtscts=False
        )
        ser.dtr = False
        ser.rts = False
        time.sleep(0.5)
        logger.info(f"Connected to ESP32 on {SERIAL_PORT}")
        # Send initial status
        ser.write(b"STATUS:ACTIVE\nQUERY:Ready for query\nINFO:Pi 3B | Linked\n")
        ser.flush()
        return True
    except Exception as e:
        logger.warning(f"Could not open serial port {SERIAL_PORT}: {e}")
        ser = None
        return False

def send_telemetry(status=None, query=None, info=None, match=None, ip=None):
    global ser, last_manual_push
    last_manual_push = time.time()
    with serial_lock:
        if ser is None or not ser.is_open:
            if not init_serial():
                return False
        try:
            payload = []
            if ip:
                payload.append(f"IP:{ip}\n")
            if status:
                payload.append(f"STATUS:{status}\n")
            if query:
                clean_q = query.replace('\n', ' ').strip()
                payload.append(f"QUERY:{clean_q}\n")
            if info:
                payload.append(f"INFO:{info}\n")
            elif match:
                payload.append(f"MATCH:{match}\n")
            
            for line in payload:
                ser.write(line.encode('utf-8'))
            ser.flush()
            logger.info(f"Pushed to OLED: {payload}")
            return True
        except Exception as e:
            logger.error(f"Error writing to serial: {e}")
            try:
                ser.close()
            except:
                pass
            ser = None
            return False

class BridgeHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        is_connected = ser is not None and ser.is_open
        response = {
            "status": "online",
            "serial_connected": is_connected,
            "port": SERIAL_PORT,
            "baud": BAUD_RATE
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception:
            data = {}

        status = data.get("status")
        query = data.get("query")
        info = data.get("info")
        match = data.get("match")
        ip = data.get("ip")

        success = send_telemetry(status=status, query=query, info=info, match=match, ip=ip)

        self.send_response(200 if success else 500)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            "success": success,
            "delivered": success,
            "timestamp": time.time()
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging
        return

def pi_sync_worker():
    """Background worker to sync latest OLED state from Raspberry Pi if idle"""
    last_known_state = None
    while True:
        try:
            time.sleep(3.0)
            # If user recently executed an active search query in last 10s, don't overwrite
            if time.time() - last_manual_push < 10.0:
                continue

            req = urllib.request.Request(PI_API_URL, headers={'User-Agent': 'ESP32Bridge'})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    if data != last_known_state:
                        last_known_state = data
                        status = data.get("status", "ACTIVE")
                        query = data.get("last_query", "Ready for query")
                        hw_info = data.get("hw_info", "Pi 3B | Cooling")
                        ip = data.get("ip", "192.168.2.2")
                        send_telemetry(status=status, query=query, info=hw_info, ip=ip)
        except Exception:
            pass

def main():
    logger.info("Initializing IntentCloud Serial Telemetry Bridge...")
    init_serial()

    # Start Pi state sync thread
    sync_thread = threading.Thread(target=pi_sync_worker, daemon=True)
    sync_thread.start()

    server = HTTPServer(('127.0.0.1', PORT), BridgeHandler)
    logger.info(f"✓ Bridge server running at http://127.0.0.1:{PORT}")
    logger.info(f"✓ Streaming live telemetry directly to physical OLED at {SERIAL_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping bridge server...")
        if ser and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
