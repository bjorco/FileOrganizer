import logging
import tkinter as tk
import tkinter.ttk as ttk
from itertools import count
from pathlib import Path
from typing import Union

from PIL import Image, ImageTk


ICONSIZE = 16

logger = logging.getLogger(__name__)

def prepare_image(image_path: Path, size: int = 0) -> ImageTk.PhotoImage:
    """ Create an image from path and add it to self as an attribute """
    dim = size if size else ICONSIZE
    try:
        img = Image.open(image_path).resize((dim, dim), Image.ANTIALIAS)
        tk_img = ImageTk.PhotoImage(img)
        return tk_img
    except FileNotFoundError:
        logger.debug(f'Image not found: {image_path}')
        return None


class ImageButton(ttk.Button):
    """ Button that displays an image when given a valid filepath """
    def __init__(self, master, path: Union[Path, str], text: str, *args, **kwargs):
        super().__init__(master, *args, text=text, **kwargs)
        
        self.path = path
        self._set_image()

    def _set_image(self, path = None) -> Union[ImageTk.PhotoImage, None]:
        """ Create a photoimage and add it to button """
        try:
            img = Image.open(self.path if path is None else path).resize((ICONSIZE, ICONSIZE), Image.ANTIALIAS)
            self.image = ImageTk.PhotoImage(img)
            self.configure(image=self.image)
        except FileNotFoundError:
            logger.debug(f'Image not found - {self.path.name}')


class ImageMenuButton(ttk.Menubutton):
    """ Button that display an image when given a valid filepath """
    def __init__(self, master, path: Union[Path, str], text: str, *args, **kwargs):
        super().__init__(master, *args, text=text, **kwargs)
        self.path = path
        self._set_image()
        self.menu = tk.Menu(self, tearoff=0)
        self['menu'] = self.menu

        self.menu.configure(font='helvetica')

    def _set_image(self) -> Union[ImageTk.PhotoImage, None]:
        """ Create a photoimage and add it to button """
        image = self.prepare_image(self.path)
        self.configure(image=image)

    
    def prepare_image(self, image_path: Path, size: int = 0) -> ImageTk.PhotoImage:
        """ Create an image from path and add it to self as an attribute """
        dim = size if size else ICONSIZE
        try:
            img = Image.open(image_path).resize((dim, dim), Image.ANTIALIAS)
            tk_img = ImageTk.PhotoImage(img)

            # Keep reference to image to avoid garbage collection
            setattr(self, image_path.stem, tk_img)
        except FileNotFoundError:
            logger.debug(f'Image not found - {self.path.name}')
            tk_img = None
        finally:
            return tk_img


    def add_command(self, *args, **kwargs):
        """ Add commands to menu """
        if 'compound' not in kwargs: kwargs['compound'] = tk.LEFT

        self.menu.add_command(*args, **kwargs)


    def add_separator(self, *args, **kwargs):
        """ Add seperator to menu """
        self.menu.add_separator(*args, **kwargs)



class ImageLabel(tk.Label):
    """ Label that displays images, and plays them if they are gifs """
    def __init__(self, master, image, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config(borderwidth=0)

        self.load(image)


    def load(self, im):
        """ Load image into frames """
        try:
            im = Image.open(im)
        except FileNotFoundError:
            logger.debug('Loading image not found')
            return

        self.current = 0
        self.frames = []
        
        try:
            for i in count(1):
                self.frames.append(ImageTk.PhotoImage(im.copy()))
                im.seek(i)
        except EOFError:
            pass

        try:
            self.delay = im.info['duration']
        except KeyError:
            self.delay = 100

        if len(self.frames) == 1:
            self.config(image=self.frames[0])
        else:
            self.next_frame()

    def unload(self):
        self.config(image=None)
        self.frames = None

    def next_frame(self):
        if self.frames:
            self.current = self.current + 1
            self.current = self.current % len(self.frames)
            self.config(image=self.frames[self.current])

            self.after(self.delay, self.next_frame)


class ImageCanvas(tk.Canvas):
    formats = ['.jpg', '.png']

    def __init__(self, master, image: str, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.image_path = Path(image) if image else None
        self.image_bitmap = self.process_image(self.image_path) if image else None
        if self.image_bitmap is not None:
            self.draw_image()

    def process_image(self, image_path: Path) -> ImageTk.PhotoImage:
        if image_path.exists() and image_path.suffix in self.formats:
            bbox = (int(self['width']), int(self['height']))
            img = Image.open(image_path)
            img.thumbnail(bbox, Image.ANTIALIAS)
            return ImageTk.PhotoImage(image=img)
        return None

    def draw_image(self):
        """ Draw image to canvas """
        self.configure(width=self.image_bitmap.width(), height=self.image_bitmap.height())
        self.create_image(self.image_bitmap.width()//2, self.image_bitmap.height()//2, anchor='center', image=self.image_bitmap)
