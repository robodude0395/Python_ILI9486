from PIL import Image, ImageDraw, ImageFont

class Canvas:
    def __init__(self, width: int, height: int, background=(0, 0, 0)):
        """
        Initialize a canvas with given size and background color.
        """
        self.width = width
        self.height = height
        self.background = background
        self.image = Image.new("RGB", (self.width, self.height), self.background)
        self.draw = ImageDraw.Draw(self.image)

    def clear(self, color=None):
        """
        Clear the canvas with the background color or provided color.
        """
        if color is None:
            color = self.background
        self.draw.rectangle([(0, 0), (self.width, self.height)], fill=color)
        return self

    def set_background(self, color):
        """
        Change the background color and clear the canvas with it.
        """
        self.background = color
        self.clear(color)
        return self

    def text(self, position, content, color=(255, 255, 255), font=None):
        """
        Draw text on the canvas at the given position.
        """
        if font is None:
            font = ImageFont.load_default()
        self.draw.text(position, content, fill=color, font=font)
        return self

    def rectangle(self, xy, outline=None, fill=None, width=1):
        """
        Draw a rectangle.
        xy: (x0, y0, x1, y1)
        """
        self.draw.rectangle(xy, outline=outline, fill=fill, width=width)
        return self

    def line(self, xy, fill=(255, 255, 255), width=1):
        """
        Draw a line.
        xy: [(x0,y0),(x1,y1),...]
        """
        self.draw.line(xy, fill=fill, width=width)
        return self

    def get_image(self):
        """
        Return the current PIL Image to be sent to the display.
        """
        return self.image
