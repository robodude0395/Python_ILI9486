import ILI9486 as LCD
import config
from spidev import SpiDev
import RPi.GPIO as GPIO
from canvas import Canvas

spi = SpiDev()
GPIO.setmode(GPIO.BCM)
spi.open(config.SPI_BUS, config.SPI_DEVICE)
spi.mode = 0b10
spi.max_speed_hz = 64000000

lcd = LCD.ILI9486(dc=config.DC_PIN, rst=config.RST_PIN, spi=spi).begin()
lcd.set_rotation(3)

# Create canvas
canvas = Canvas(lcd.dimensions(), background=(128, 0, 128))  # purple background

# Draw text and shapes
canvas.text((50, 50), "Hello Canvas!", color=(255, 255, 255))
canvas.rectangle((40, 40, 200, 80), outline=(255, 255, 0), width=2)

# Display
lcd.display(canvas.get_image())
