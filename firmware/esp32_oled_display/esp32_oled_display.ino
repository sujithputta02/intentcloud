/*
 * IntentCloud — Cognitive Cloud Memory System
 * Edge Node Hardware Display (ESP32 + SSD1306 0.96" OLED)
 * 
 * Pinout:
 *   OLED VCC -> ESP32 3V3 (or VIN)
 *   OLED GND -> ESP32 GND
 *   OLED SCL -> ESP32 GPIO 22 (D22)
 *   OLED SDA -> ESP32 GPIO 21 (D21)
 * 
 * Serial Input:
 *   Listens on Serial (115200 baud) for updates from Raspberry Pi:
 *   Format: "IP:<ip>", "TEMP:<temp>", "QUERY:<text>", "STATUS:<text>"
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1

// Standard 0.96" I2C address is usually 0x3C (rarely 0x3D)
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// State variables
String nodeIP = "192.168.2.2";
String systemStatus = "ONLINE";
String lastQuery = "System Ready";
String cpuTemp = "42.5 C";
int pulseCount = 0;
unsigned long lastUpdate = 0;

void drawDashboard() {
  display.clearDisplay();

  // Header Banner
  display.fillRect(0, 0, 128, 12, SSD1306_WHITE);
  display.setTextSize(1);
  display.setTextColor(SSD1306_BLACK);
  display.setCursor(4, 2);
  display.print("INTENTCLOUD EDGE");

  // Pulse Activity Indicator (alternating box)
  if (pulseCount % 2 == 0) {
    display.fillRect(116, 2, 8, 8, SSD1306_BLACK);
  } else {
    display.drawRect(116, 2, 8, 8, SSD1306_BLACK);
  }

  // Body Text
  display.setTextColor(SSD1306_WHITE);

  // Status & Pipeline
  display.setCursor(0, 16);
  display.print("Status: ");
  display.print(systemStatus);

  // IP Address
  display.setCursor(0, 26);
  display.print("Edge IP: ");
  display.print(nodeIP);

  // CPU / Hardware Health
  display.setCursor(0, 36);
  display.print("Temp: ");
  display.print(cpuTemp);
  display.print(" | Pi 3B");

  // Divider Line
  display.drawLine(0, 47, 128, 47, SSD1306_WHITE);

  // Real-time Query Activity
  display.setCursor(0, 52);
  display.print("Q: ");
  if (lastQuery.length() > 18) {
    display.print(lastQuery.substring(0, 18));
  } else {
    display.print(lastQuery);
  }

  display.display();
}

void parseSerialCommand(String cmd) {
  cmd.trim();
  if (cmd.startsWith("IP:")) {
    nodeIP = cmd.substring(3);
  } else if (cmd.startsWith("STATUS:")) {
    systemStatus = cmd.substring(7);
  } else if (cmd.startsWith("TEMP:")) {
    cpuTemp = cmd.substring(5);
  } else if (cmd.startsWith("QUERY:")) {
    lastQuery = cmd.substring(6);
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n[IntentCloud] Initializing ESP32 Edge Display Node...");

  // Initialize I2C on default ESP32 pins: SDA=21, SCL=22
  Wire.begin(21, 22);

  // Initialize display with internal charge pump enabled
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("[IntentCloud] 0x3C failed, trying address 0x3D...");
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
      Serial.println("[IntentCloud] ERROR: SSD1306 OLED display not detected!");
      while (true) {
        delay(1000);
      }
    }
  }

  Serial.println("[IntentCloud] SSD1306 OLED initialized successfully!");

  // Splash Screen
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(16, 12);
  display.println("INTENTCLOUD");
  display.setCursor(8, 26);
  display.println("Cognitive Memory");
  display.setCursor(20, 40);
  display.println("Edge System");
  display.setCursor(24, 54);
  display.println("Starting...");
  display.display();
  delay(1800);

  drawDashboard();
}

void loop() {
  // Read any incoming serial telemetry from Raspberry Pi
  while (Serial.available()) {
    String incoming = Serial.readStringUntil('\n');
    parseSerialCommand(incoming);
  }

  // Refresh animation pulse every 1 second
  if (millis() - lastUpdate > 1000) {
    lastUpdate = millis();
    pulseCount++;
    drawDashboard();
  }
}
