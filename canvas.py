from PIL import Image, ImageDraw, ImageFont

class Canvas:
    def __init__(self, width: int, height: int, background=(0, 0, 0)):
        self.width = width
        self.height = height
        self.background = background
        self.image = Image.new("RGB", (self.width, self.height), self.background)
        self.draw = ImageDraw.Draw(self.image)

    def clear(self, color=None):
        if color is None:
            color = self.background
        self.draw.rectangle([(0, 0), (self.width, self.height)], fill=color)
        return self

    def set_background(self, color):
        self.background = color
        self.clear(color)
        return self

    def text(self, position, content, color=(255, 255, 255), text_size=12, font_path=None):
        """
        Draw text with a specific size.
        font_path: path to a TTF font file. If None, uses default font.
        """
        if font_path is not None:
            font = ImageFont.truetype(font_path, text_size)
        else:
            font = ImageFont.load_default()
        self.draw.text(position, content, fill=color, font=font)
        return self

    def rectangle(self, xy, outline=None, fill=None, width=1):
        self.draw.rectangle(xy, outline=outline, fill=fill, width=width)
        return self

    def line(self, xy, fill=(255, 255, 255), width=1):
        self.draw.line(xy, fill=fill, width=width)
        return self

    def get_image(self):
        return self.image
