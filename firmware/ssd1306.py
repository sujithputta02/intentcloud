import time
import framebuf

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        try:
            self.i2c.writeto(self.addr, bytearray([0x80, cmd]))
        except Exception:
            pass

    def init_display(self):
        # Full Adafruit-tested SSD1306 power-on sequence
        cmds = (
            0xAE,        # Display OFF
            0xD5, 0x80,  # Clock divide ratio
            0xA8, self.height - 1, # Multiplex ratio (63 for 64h)
            0xD3, 0x00,  # Display offset 0
            0x40,        # Start line 0
            0x8D, 0x14,  # Enable internal charge pump (essential!)
            0x20, 0x00,  # Horizontal memory mode
            0xA1,        # Segment remap
            0xC8,        # COM scan direction
            0xDA, 0x02 if self.height == 32 else 0x12, # COM pins config
            0x81, 0xFF,  # Contrast maximum
            0xD9, 0xF1,  # Pre-charge period
            0xDB, 0x40,  # VCOMH deselect level
            0x2E,        # Deactivate scroll
            0xA4,        # Output follows RAM
            0xA6,        # Normal display (not inverted)
            0xAF         # Display ON!
        )
        for c in cmds:
            self.write_cmd(c)
            time.sleep_ms(1)
        
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(0xAE)

    def poweron(self):
        self.write_cmd(0xAF)

    def contrast(self, contrast):
        self.write_cmd(0x81)
        self.write_cmd(contrast & 0xFF)

    def invert(self, invert):
        self.write_cmd(0xA7 if invert else 0xA6)

    def show(self):
        try:
            # Set col address and page address range
            for c in (0x21, 0, self.width - 1, 0x22, 0, self.pages - 1):
                self.write_cmd(c)
            # Send pages with 2ms pacing for reliable display buffer write
            for p in range(self.pages):
                chunk = bytearray([0x40]) + self.buffer[p * self.width : (p + 1) * self.width]
                self.i2c.writeto(self.addr, chunk)
                time.sleep_ms(2)
        except Exception:
            pass
