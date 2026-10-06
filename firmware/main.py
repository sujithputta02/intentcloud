import time
import sys
import select
from machine import Pin, I2C
import ssd1306

# Give power rails time to stabilize
time.sleep_ms(600)

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
devs = i2c.scan()
addr = 0x3C if 0x3C in devs else (devs[0] if devs else 0x3C)
print("SSD1306 OLED initialized on I2C address:", hex(addr))

oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=addr)

# Initial Splash
oled.fill(0)
oled.fill_rect(0, 0, 128, 12, 1)
oled.text("INTENTCLOUD", 20, 2, 0)
oled.text("Cognitive Edge", 8, 20, 1)
oled.text("Hardware Online", 4, 34, 1)
oled.text("Ready for Query", 4, 48, 1)
oled.show()
time.sleep(1.5)

# State variables
edge_ip = "192.168.2.2"
status = "ONLINE"
hw_info = "Pi 3B | Qdrant"
last_query = "Ready for query"
pulse = 0

def draw_dashboard():
    global pulse
    oled.fill(0)
    
    # Inverted Header Banner
    oled.fill_rect(0, 0, 128, 11, 1)
    oled.text("INTENTCLOUD", 4, 2, 0)
    
    # Pulse dot indicator in header
    if pulse % 2 == 0:
        oled.fill_rect(116, 2, 7, 7, 0)
    else:
        oled.rect(116, 2, 7, 7, 0)
    
    # Telemetry rows
    oled.text("Status: " + status[:10], 0, 15, 1)
    oled.text("IP: " + edge_ip[:14], 0, 26, 1)
    oled.text(hw_info[:16], 0, 37, 1)
    
    # Divider line
    oled.hline(0, 48, 128, 1)
    
    # Query / activity tracker
    display_q = last_query
    if len(display_q) > 13:
        display_q = display_q[:13]
    oled.text("Q: " + display_q, 0, 53, 1)
    
    oled.show()

# Setup non-blocking Serial input
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

while True:
    if poll.poll(0):
        try:
            line = sys.stdin.readline().strip()
            if line:
                if line.startswith("IP:"):
                    edge_ip = line[3:].strip()
                elif line.startswith("STATUS:"):
                    status = line[7:].strip()
                elif line.startswith("QUERY:"):
                    last_query = line[6:].strip()
                elif line.startswith("INFO:"):
                    hw_info = line[5:].strip()
                elif line.startswith("TEMP:"):
                    hw_info = "Pi 3B | " + line[5:].strip()
                elif line.startswith("MATCH:"):
                    hw_info = "Pi 3B | " + line[6:].strip() + " Match"
        except Exception:
            pass

    pulse += 1
    draw_dashboard()
    time.sleep(0.5)
