# Copyright (c)
# Authors: Tony DiCola, Liqun Hu, Thorben Yzer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from enum import Enum
import time
import numpy as np
from PIL import Image, ImageDraw
import RPi.GPIO as GPIO
from spidev import SpiDev

# constants
LCD_WIDTH = 320
LCD_HEIGHT = 480

# commands
CMD_RDPXLFMT = 0x0C
CMD_SLPIN = 0x10
CMD_SLPOUT = 0x11
CMD_INVOFF = 0x20
CMD_INVON = 0x21
CMD_DISPOFF = 0x28
CMD_DISPON = 0x29
CMD_SETCA = 0x2A
CMD_SETPA = 0x2B
CMD_WRMEM = 0x2C
CMD_RDMEM = 0x2E
CMD_MADCTL = 0x36
CMD_IDLOFF = 0x38
CMD_IDLON = 0x39
CMD_PXLFMT = 0x3A
CMD_IFMODE = 0xB0
CMD_PWRCTLNOR = 0xC2
CMD_VCOMCTL = 0xC5
CMD_PGAMCTL = 0xE0
CMD_NGAMCTL = 0xE1


def image_to_data(image: Image):
    """Converts a PIL image to 666RGB format that can be drawn on the LCD."""
    pb = np.array(image.convert('RGB')).astype('uint16')
    return np.dstack((pb[:, :, 0] & 0xFC,
                      pb[:, :, 1] & 0xFC,
                      pb[:, :, 2] & 0xFC)).flatten().tolist()


class Origin(Enum):
    """Display origin definitions."""
    UPPER_LEFT = 0x28
    UPPER_LEFT_MIRRORED = 0xA8
    LOWER_LEFT = 0x48
    LOWER_LEFT_MIRRORED = 0x08
    UPPER_RIGHT = 0x88
    UPPER_RIGHT_MIRRORED = 0xC8
    LOWER_RIGHT = 0xE8
    LOWER_RIGHT_MIRRORED = 0x68


class ILI9486:
    """ILI9486 TFT Display Driver"""

    @classmethod
    def landscape_dimensions(cls):
        return LCD_HEIGHT, LCD_WIDTH

    @classmethod
    def portrait_dimensions(cls):
        return LCD_WIDTH, LCD_HEIGHT

    def __init__(self, spi: SpiDev, dc: int, rst: int = None, *, origin: Origin = Origin.UPPER_LEFT):
        self.__spi = spi
        self.__dc = dc
        self.__rst = rst
        self.__origin = origin
        self.__width = LCD_WIDTH
        self.__height = LCD_HEIGHT
        self.__inverted = False
        self.__idle = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__dc, GPIO.OUT)
        GPIO.output(self.__dc, GPIO.HIGH)
        if self.__rst is not None:
            GPIO.setup(self.__rst, GPIO.OUT)
            GPIO.output(self.__rst, GPIO.HIGH)

        # adjust dimensions if origin is landscape
        if self.__origin.value & 0x20:
            self.__width, self.__height = self.__height, self.__width

        self.__buffer = Image.new('RGB', (self.__width, self.__height), (0, 0, 0))

    def dimensions(self):
        return self.__width, self.__height

    def is_landscape(self):
        return bool(self.__origin.value & 0x20)

    def send(self, data, is_data=True, chunk_size=4096):
        GPIO.output(self.__dc, is_data)
        if isinstance(data, int):
            self.__spi.writebytes([data])
        else:
            for start in range(0, len(data), chunk_size):
                end = min(start + chunk_size, len(data))
                self.__spi.writebytes(data[start:end])
        return self

    def command(self, data):
        return self.send(data, False)

    def data(self, data):
        return self.send(data, True)

    def reset(self):
        if self.__rst is not None:
            GPIO.output(self.__rst, GPIO.HIGH)
            time.sleep(.001)
            GPIO.output(self.__rst, GPIO.LOW)
            time.sleep(.0001)
            GPIO.output(self.__rst, GPIO.HIGH)
            time.sleep(.120)
            self.__inverted = False
            self.__idle = False
        return self

    def _init_sequence(self):
        self.command(CMD_IFMODE).data(0x00)
        self.command(CMD_SLPOUT)
        time.sleep(0.020)

        self.command(CMD_PXLFMT).data(0x66)
        self.command(CMD_RDPXLFMT).data(0x66)
        self.command(CMD_PWRCTLNOR).command(0x44)
        self.command(CMD_VCOMCTL).send([0, 0, 0, 0], True, chunk_size=1)
        self.command(CMD_PGAMCTL).send(
            [0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00],
            True, chunk_size=1)
        self.command(CMD_NGAMCTL).send(
            [0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00],
            True, chunk_size=1)
        self.command(CMD_MADCTL).data(self.__origin.value)
        self.command(CMD_SLPOUT)
        self.command(CMD_DISPON)
        return self

    def begin(self):
        return self.reset()._init_sequence()

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        if x1 is None:
            x1 = self.__width - 1
        if y1 is None:
            y1 = self.__height - 1
        self.command(CMD_SETCA)
        self.data(x0 >> 8)
        self.data(x0 & 0xFF)
        self.data(x1 >> 8)
        self.data(x1 & 0xFF)
        self.command(CMD_SETPA)
        self.data(y0 >> 8)
        self.data(y0 & 0xFF)
        self.data(y1 >> 8)
        self.data(y1 & 0xFF)
        return self

    def display(self, image=None, x0=0, y0=0):
        if image is None:
            image = self.__buffer

        disp_buffer = Image.new('RGB', (self.__width, self.__height))

        # Map MADCTL to rotation and flips
        transform_map = {
            0x28: lambda im: im,                       # portrait
            0xE8: lambda im: im.rotate(270),           # landscape
            0xA8: lambda im: im.rotate(180),           # portrait flipped
            0x68: lambda im: im.rotate(90),            # landscape flipped
        }

        transform = transform_map.get(self.__origin & 0xE8, lambda im: im)
        rotated_image = transform(image)

        # Center image in buffer
        dx = (self.__width - rotated_image.width) // 2
        dy = (self.__height - rotated_image.height) // 2
        disp_buffer.paste(rotated_image, (dx, dy))

        self.set_window(0, 0, self.__width - 1, self.__height - 1)
        data = image_to_data(disp_buffer)
        self.command(CMD_WRMEM)
        self.data(list(data))
        return self

    def clear(self, color=(0, 0, 0)):
        width, height = self.__buffer.size
        self.__buffer.putdata([color] * (width * height))
        return self

    def draw(self):
        return ImageDraw.Draw(self.__buffer)

    def is_inverted(self):
        return self.__inverted

    def invert(self, state=True):
        self.command(CMD_INVON if state else CMD_INVOFF)
        self.__inverted = state
        return self

    def is_idle(self):
        return self.__idle

    def idle(self, state=True):
        self.command(CMD_IDLON if state else CMD_IDLOFF)
        self.__idle = state
        return self

    def on(self):
        return self.command(CMD_DISPON)

    def off(self):
        return self.command(CMD_DISPOFF)

    def sleep(self):
        self.command(CMD_SLPIN)
        time.sleep(0.005)
        return self

    def wake_up(self):
        self.command(CMD_SLPOUT)
        time.sleep(0.005)
        return self

    def set_rotation(self, rotation: int):
        rotation = rotation % 4
        if rotation == 0:
            madctl = 0x28
            self.__width, self.__height = LCD_WIDTH, LCD_HEIGHT
        elif rotation == 1:
            madctl = 0xE8
            self.__width, self.__height = LCD_HEIGHT, LCD_WIDTH
        elif rotation == 2:
            madctl = 0xA8
            self.__width, self.__height = LCD_WIDTH, LCD_HEIGHT
        else:
            madctl = 0x68
            self.__width, self.__height = LCD_HEIGHT, LCD_WIDTH

        self.__origin = madctl
        self.command(CMD_MADCTL).data(madctl)
        self.__buffer = Image.new('RGB', (self.__width, self.__height), (0, 0, 0))
