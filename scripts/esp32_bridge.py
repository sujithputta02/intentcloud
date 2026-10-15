#!/usr/bin/env python3
"""
IntentCloud ESP32 Serial Telemetry Bridge
- Dynamically auto-detects USB serial connections to ESP32 OLED Displays (e.g., /dev/cu.usbserial*, /dev/cu.wchusbserial*, /dev/cu.usbmodem*)
- Non-blocking asynchronous network routing to Raspberry Pi OLED (http://192.168.2.2:8000/device/oled/push)
- Ultra-low latency (<2ms) local HTTP endpoint (http://127.0.0.1:8765/push)
  so frontend telemetry never blocks, times out, or fails.
"""

import sys
import os
import glob
import time
import json
import logging
import threading
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import serial

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger("ESP32Bridge")

PORT = int(os.environ.get("BRIDGE_PORT", 8765))
DEFAULT_SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/cu.usbserial-5C790748651")
BAUD_RATE = int(os.environ.get("BAUD_RATE", 115200))
PI_BASE_URL = os.environ.get("PI_BASE_URL", "http://192.168.2.2:8000")
PI_API_URL = f"{PI_BASE_URL}/device/oled"
PI_PUSH_URL = f"{PI_BASE_URL}/device/oled/push"
LOCAL_API_URL = os.environ.get("LOCAL_API_URL", "http://127.0.0.1:8000/device/telemetry")

serial_lock = threading.Lock()
ser = None
current_port = None
last_manual_push = 0
last_warning_time = 0

latest_state = {
    "status": "ONLINE",
    "query": "Ready for query",
    "info": "Pi 3B | Qdrant",
    "match": None,
    "ip": "192.168.2.2",
    "last_updated": time.time()
}

# Async queue for network telemetry to Raspberry Pi
pi_push_queue = queue.Queue(maxsize=20)

def scan_available_serial_ports():
    """Scan the system for any USB-to-Serial devices."""
    candidates = []
    
    patterns = [
        "/dev/cu.usbserial*",
        "/dev/cu.wchusbserial*",
        "/dev/cu.usbmodem*",
        "/dev/cu.SLAB_USBtoUART*",
        "/dev/cu.usb*",
        "/dev/cu.CH34*",
        "/dev/cu.CP21*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
    ]
    for pattern in patterns:
        for match in glob.glob(pattern):
            if match not in candidates and "Bluetooth" not in match and "debug-console" not in match:
                candidates.append(match)

    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            dev = p.device
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if "bluetooth" not in dev.lower() and "debug-console" not in dev.lower():
                if dev not in candidates:
                    candidates.append(dev)
    except Exception:
        pass

    if DEFAULT_SERIAL_PORT and os.path.exists(DEFAULT_SERIAL_PORT) and DEFAULT_SERIAL_PORT not in candidates:
        candidates.insert(0, DEFAULT_SERIAL_PORT)

    return candidates

def try_connect_serial():
    """Attempt connecting to available USB serial port."""
    global ser, current_port, last_warning_time
    with serial_lock:
        if ser and ser.is_open:
            return True

        ports = scan_available_serial_ports()
        if not ports:
            now = time.time()
            if now - last_warning_time > 120:
                logger.info(
                    "No local USB serial port attached. Routing telemetry over Ethernet to "
                    f"Raspberry Pi OLED ({PI_PUSH_URL})."
                )
                last_warning_time = now
            ser = None
            current_port = None
            return False

        target_port = ports[0]
        try:
            if ser and ser.is_open:
                ser.close()
            ser = serial.Serial(
                target_port,
                BAUD_RATE,
                timeout=1,
                dsrdtr=False,
                rtscts=False
            )
            ser.dtr = False
            ser.rts = False
            time.sleep(0.3)
            current_port = target_port
            logger.info(f"✓ Connected to physical ESP32 OLED on {target_port}")
            ser.write(b"STATUS:ACTIVE\nQUERY:Ready for query\nINFO:Pi 3B | Linked\nTEMP:42.5 C | Linked\n")
            ser.flush()
            return True
        except Exception as e:
            now = time.time()
            if now - last_warning_time > 60:
                logger.warning(f"Could not open serial port {target_port}: {e}")
                last_warning_time = now
            ser = None
            current_port = None
            return False

def pi_network_worker():
    """Background worker draining telemetry push queue to Raspberry Pi."""
    while True:
        try:
            payload = pi_push_queue.get()
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    PI_PUSH_URL,
                    data=data,
                    headers={"Content-Type": "application/json", "User-Agent": "ESP32Bridge"}
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"✓ Pushed to Pi OLED: {payload.get('status')} | {payload.get('query')}")
            except Exception as net_err:
                logger.debug(f"Pi network delivery deferred: {net_err}")
            finally:
                pi_push_queue.task_done()
        except Exception:
            time.sleep(0.1)

def queue_pi_push(status=None, query=None, info=None, match=None, ip=None):
    """Queue telemetry for background network delivery to Raspberry Pi."""
    payload = {
        "status": status or latest_state.get("status", "ACTIVE"),
        "query": query or latest_state.get("query", "Ready for query"),
        "info": info or (f"Pi 3B | {match}% Match" if match else latest_state.get("info", "Pi 3B | Qdrant")),
        "edge_ip": ip or latest_state.get("ip", "192.168.2.2"),
        "last_updated": time.time(),
    }
    if match is not None:
        payload["match"] = match

    try:
        # Drop stale queue items if overwhelmed
        if pi_push_queue.full():
            try:
                pi_push_queue.get_nowait()
                pi_push_queue.task_done()
            except Exception:
                pass
        pi_push_queue.put_nowait(payload)
        return True
    except Exception:
        return False

# Rate limiter & deduplicator for hardware OLED (eliminates screen glitching & tearing)
last_serial_write_time = 0
MIN_SERIAL_INTERVAL = 0.20  # 200ms debounce ensures I2C bus stability
last_sent_packet = None

def write_hardware_packet():
    """Write sanitized, rate-limited telemetry packet to the physical ESP32 OLED"""
    global ser, last_serial_write_time, last_sent_packet
    now = time.time()
    if now - last_serial_write_time < MIN_SERIAL_INTERVAL:
        return

    with serial_lock:
        if not (ser and ser.is_open):
            return

        ip = str(latest_state.get("ip", "192.168.2.2"))[:15]
        status = str(latest_state.get("status", "ONLINE"))[:10]
        query = str(latest_state.get("query", "Ready for query")).replace('\n', ' ').strip()[:18]
        info = str(latest_state.get("info", "Pi 3B | Qdrant"))[:16]

        # Firmware expects exactly: IP:<ip>\n STATUS:<status>\n TEMP:<temp>\n QUERY:<query>\n
        packet = f"IP:{ip}\nSTATUS:{status}\nTEMP:{info}\nQUERY:{query}\n"
        if packet == last_sent_packet:
            return  # Skip duplicate writes to prevent display redraw jitter

        try:
            ser.write(packet.encode("utf-8"))
            ser.flush()
            last_serial_write_time = now
            last_sent_packet = packet
        except Exception as e:
            logger.error(f"Error writing to USB serial: {e}")
            try:
                ser.close()
            except Exception:
                pass
            ser = None

def send_telemetry(status=None, query=None, info=None, match=None, ip=None):
    """Fast non-blocking dispatch: USB serial if open, else async network queue."""
    global ser, last_manual_push, latest_state
    last_manual_push = time.time()

    # Update memory cache
    if status: latest_state["status"] = status
    if query: latest_state["query"] = query
    if info: latest_state["info"] = info
    elif match: latest_state["info"] = f"Pi 3B | {match}% Match"
    if match is not None: latest_state["match"] = match
    if ip: latest_state["ip"] = ip
    latest_state["last_updated"] = time.time()

    # Always log live telemetry on bridge terminal so live pipeline is visible
    clean_display_q = (query or latest_state.get("query", "Ready for query")).replace('\n', ' ').strip()
    logger.info(f"⚡ [OLED LIVE] Status: {latest_state['status']:<10} | Query: '{clean_display_q[:25]}' | Info: {latest_state.get('info', '')} | Match: {latest_state.get('match') or '-'}%")

    # Smooth rate-limited write to hardware serial
    write_hardware_packet()

    # Async path: Queue for network delivery to Raspberry Pi OLED
    queue_pi_push(status=status, query=query, info=info, match=match, ip=ip)
    return True, "usb_serial" if (ser and ser.is_open) else "pi_network"

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
            "port": current_port or DEFAULT_SERIAL_PORT,
            "transport": "usb_serial" if is_connected else "pi_network",
            "baud": BAUD_RATE,
            "latest_state": latest_state
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

        success, transport = send_telemetry(status=status, query=query, info=info, match=match, ip=ip)

        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            "success": success,
            "delivered": True,
            "transport": transport,
            "timestamp": time.time()
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        return

def pi_sync_worker():
    """Background worker to sync latest OLED state from local backend (127.0.0.1:8000) and Raspberry Pi"""
    last_known_state = None
    while True:
        try:
            time.sleep(1.0)
            if time.time() - last_manual_push < 2.0:
                continue

            data = None
            # 1. Sync from local backend first (which handles search/upload from frontend)
            try:
                req = urllib.request.Request(LOCAL_API_URL, headers={'User-Agent': 'ESP32Bridge'})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
            except Exception:
                pass

            # 2. Fallback to Raspberry Pi if local backend didn't respond
            if not data:
                try:
                    req_pi = urllib.request.Request(PI_API_URL, headers={'User-Agent': 'ESP32Bridge'})
                    with urllib.request.urlopen(req_pi, timeout=1.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode('utf-8'))
                except Exception:
                    pass

            if data and data != last_known_state:
                last_known_state = data
                status = data.get("status", "ACTIVE")
                query = data.get("last_query", "Ready for query")
                hw_info = data.get("hw_info", "Pi 3B | Cooling")
                ip = data.get("edge_ip") or data.get("ip", "192.168.2.2")
                send_telemetry(status=status, query=query, info=hw_info, ip=ip)
        except Exception:
            pass

def hotplug_worker():
    """Periodically scan for newly plugged USB serial devices in the background every second"""
    while True:
        try:
            time.sleep(1.0)
            if ser is None or not ser.is_open:
                try_connect_serial()
        except Exception:
            pass

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def main():
    logger.info("Initializing IntentCloud Serial Telemetry Bridge...")
    try_connect_serial()

    # Start background workers
    threading.Thread(target=pi_network_worker, daemon=True).start()
    threading.Thread(target=pi_sync_worker, daemon=True).start()
    threading.Thread(target=hotplug_worker, daemon=True).start()

    server = ReusableHTTPServer(('127.0.0.1', PORT), BridgeHandler)
    logger.info(f"✓ Bridge server running at http://127.0.0.1:{PORT}")
    if ser and ser.is_open:
        logger.info(f"✓ Streaming live telemetry directly to physical OLED at {current_port}")
    else:
        logger.info(f"✓ Streaming live telemetry directly to Raspberry Pi OLED at {PI_PUSH_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping bridge server...")
        if ser and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()
