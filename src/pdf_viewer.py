import logging
import math
import tkinter as tk
import warnings
from pathlib import Path
from tkinter import ttk
from typing import Union

import fitz
from PIL import Image, ImageTk

logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class PdfViewer(ttk.Frame):
    """ Converts pdf to images using PyMuPDF and displays them in the frame """

    supported_formats = ['.png', '.pdf', '.tiff', '.jpg', '.tif']

    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.temp_dir = Path('.')
        self._file = None
        self._doc = None
        self.width = kwargs.get('width', 0)
        self._current_page = 0
        self.rotation = 0

        self.__isloading = False
        self.__scheduled_file_update = None
        self.transaction_number = 0
        
        self._init_widgets()
    

    def _init_widgets(self):
        """ Initialize the widgets """
        self.loading_view = None

        self.var_page = tk.IntVar(self, value=1)
        self.var_pagecount = tk.IntVar(self, value=1)

        self._canvas = CanvasImage(self)
        # frame = self._create_nav_buttons(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._canvas.grid(row=0, column=0)
        # frame.grid(row=2, column=0)

    # def _create_nav_buttons(self, canvas):
    #     """ Create a frame containing widgets to controll the display """
    #     frame = ttk.Frame(canvas)
    #     txt_frame = self._create_page_num_display(frame)

    #     self._btn_first = ImageButton(frame, path=ImageButton.resource.img_first, text='Første', command=lambda: self.jump_to_page(0))
    #     self._btn_last = ImageButton(frame, path=ImageButton.resource.img_last, text='Siste', command=lambda: self.jump_to_page(self.pages))
    #     self._btn_prev = ImageButton(frame, path=ImageButton.resource.img_prev, text='Forrige', command=self.prev_page)
    #     self._btn_next = ImageButton(frame, path=ImageButton.resource.img_next, text='Neste', command=self.next_page)

    #     self._btn_rotate_left = ImageButton(frame, path=ImageButton.resource.img_rotate_left, text='Roter venstre', command=lambda: self.rotate(90))
    #     self._btn_rotate_right = ImageButton(frame, path=ImageButton.resource.img_rotate_right, text='Roter høyre', command=lambda: self.rotate(-90))

    #     frame.grid_columnconfigure(3, weight=1)
    #     self._btn_first.grid(row=0, column=0, pady=5)
    #     self._btn_prev.grid(row=0, column=1)
    #     self._btn_rotate_left.grid(row=0, column=2)

    #     txt_frame.grid(row=0, column=3)

    #     self._btn_rotate_right.grid(row=0, column=4)
    #     self._btn_next.grid(row=0, column=5)
    #     self._btn_last.grid(row=0, column=6)
    #     return frame
    

    def _create_page_num_display(self, canvas):
        """ Create a frame on canvas containing the page numbers of the document """
        txt_frame = ttk.Frame(canvas)

        self._txt_of_num = ttk.Label(txt_frame, text='av')
        self._txt_pagecount = ttk.Label(txt_frame, textvariable=self.var_pagecount)
        self._etr_page = ttk.Entry(txt_frame, textvariable=self.var_page, width=3)
        self._etr_page.bind('<Return>', self.on_return_page_num)
        
        txt_frame.grid_columnconfigure(0, weight=1)
        txt_frame.grid_columnconfigure(4, weight=1)
        self._etr_page.grid(row=0, column=1, padx=10, sticky='ew')
        self._txt_of_num.grid(row=0, column=2, sticky='ew')
        self._txt_pagecount.grid(row=0, column=3, padx=10, sticky='ew')

        return txt_frame

    @property
    def file(self):
        return self._file
  
    @file.setter
    def file(self, path: Union[Path, str, None]):
        """ Sets file and updates the display """
        self.set_file(path)

    def set_file(self, path: Union[Path, str, None]):
        """ Set file if valid and update display """
        if str(self._file) == str(path):
            return
        else:
            # Close old file
            self.close()
        
        if path is None:
            # Disable display if passed None
            self.enabled(False)
            return
        elif path.suffix.lower() not in self.supported_formats:
            self.enabled(False)
            self._canvas.file_name(f'No preview for file format: {path.suffix}')
            return

        try:
            self._file = Path(path)
            self._doc = fitz.open(self._file)
        except RuntimeError:
            self.enabled(False)
            self._canvas.file_name('File not found')
            logger.debug(f'File not found: {path}')
            return

        self.enabled(True)

        # Sets page to 0 and display it
        self.page = 0
        self.var_page.set(self.page+1)
        self.var_pagecount.set(self.pages)

    
    @property
    def page(self) -> int:
        return self._current_page


    @page.setter
    def page(self, new_page: int):
        """ Set page value to new page and display """
        if self._doc is None:
            return

        if 0 <= new_page < self.pages:
            self._current_page = new_page
        elif new_page < 0:
            self._current_page = 0
        else:
            self._current_page = self.pages - 1

        self.rotation = 0
        self._display_page(page=self._current_page)
        # self.modify_button_state()

    @property
    def pages(self):
        """ Return number of pages in the document """
        if self._doc is not None:
            return self._doc.pageCount
        else:
            return 0

    def close(self):
        """ Close the pdf file """
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def enabled(self, value: bool):
        """ Set the enabled state of the widget """
        # if not value:
        #     self._file = None
        #     self._doc = None
        #     self.var_page.set(0)
        #     self.var_pagecount.set(0)
        #     self._canvas.clear()

        # self._canvas.file_name(self._file.name if self._file else 'Ingen fil')
        # self._canvas.file_name_coords(center=value)

        # state = tk.NORMAL if value else tk.DISABLED
        # self._etr_page.configure(state=state)
        # self._btn_first.configure(state=state)
        # self._btn_last.configure(state=state)
        # self._btn_next.configure(state=state)
        # self._btn_prev.configure(state=state)
        # self._btn_rotate_right.configure(state=state)
        # self._btn_rotate_left.configure(state=state)
        pass

    # def modify_button_state(self):
    #     """ Change the state of page selection buttons """
    #     state = tk.NORMAL if self.page > 0 else tk.DISABLED
    #     self._btn_first.configure(state=state)
    #     self._btn_prev.configure(state=state)

    #     self._etr_page.configure(state=tk.NORMAL if self.pages > 1 else tk.DISABLED)

    #     state = tk.NORMAL if self.page+1 < self.pages else tk.DISABLED
    #     self._btn_next.configure(state=state)
    #     self._btn_last.configure(state=state)


    def _image_to_canvas(self, page: int = 0, event: tk.Event=None):
        """ Converts page of pdf file to an image that scales to fit the frame """
        self._canvas.clear()
        pix = self._doc.get_page_pixmap(page)
        
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        
        w, h = img.size
        width = self._canvas.canvas.winfo_width()
        percent = width / w
        h = int(h*percent)
        
        img = img.resize((width, h), Image.ANTIALIAS)
        img = img.rotate(self.rotation, expand=True, translate=(0,0))
        temp = self.temp_dir / 'temp.png'
        img.save(temp, format='PNG')
        
        self._canvas.switch_image(temp)


    def _display_page(self, page: int = 0):
        """ Display page from doc in canvas """
        self._image_to_canvas(page=page)
        self.var_page.set(page+1)


    def next_page(self):
        """ Display next page """
        self.page = self.page + 1

    
    def prev_page(self):
        """ Display previous page """
        self.page = self.page - 1


    def jump_to_page(self, page: int = 0):
        """ Display given page number """
        self.page = page

    
    def on_return_page_num(self, event):
        """ Jump to the page user has specified """
        try:
            num = int(self.var_page.get()) - 1
        except tk.TclError:
            # Reset text to valid type
            self.var_page.set(self.page + 1)
        else:
            self.jump_to_page(page=num)


    def rotate(self, angle: int):
        """ Rotate the image by angle """
        self.rotation = (self.rotation + angle) % 360
        self._display_page(page=self.page)



class CanvasImage:
    """ Display and zoom image """
    def __init__(self, placeholder, path = None):
        """ Initialize the ImageFrame """
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__delta = 1.2  # zoom magnitude
        self.__filter = Image.LANCZOS # could be: NEAREST, BILINEAR, BICUBIC and ANTIALIAS
        self.__previous_state = 0  # previous state of the keyboard
        self.org_path = path
        self.path = path  # path to the image, should be public for outer classes
        self._scheduled_config_call = 0
        
        # Create ImageFrame in placeholder widget
        self.__imframe = tk.Frame(placeholder)  # placeholder of the ImageFrame object
        
        # Vertical and horizontal scrollbars for canvas
        hbar = ttk.Scrollbar(self.__imframe, orient='horizontal')
        vbar = ttk.Scrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 14000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        
        if path is not None:
            self.__create_image()
        
        self.id_name_display = self.canvas.create_text(15, 15, text='', anchor='w')
        self.__bind_events()


    file_name = lambda self, name: self.canvas.itemconfigure(self.id_name_display, text=name)
    file_name_coords = lambda self, center: self.canvas.coords(self.id_name_display, 
                                                        10 if center else (self.canvas.winfo_width() // 2), 
                                                        10 if center else (self.canvas.winfo_height() // 2))

    def __create_image(self):
        """ Create image from path """
        self.imscale = 1.0
        
        Image.MAX_IMAGE_PIXELS = 1000000000  # suppress DecompressionBombError for the big image
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes

        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
           self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [self.__image.tile[0][0],  # it have to be 'raw'
                           [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                           self.__offset,
                           self.__image.tile[0][3]]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))

        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()
        

    def __bind_events(self):
        """ Bind events to canvas """
        self.canvas.bind('<Configure>', self.__schedule_resize)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B1-Motion>',     self.__move_to)  # move canvas to the new position
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.__wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.__wheel)  # zoom for Linux, wheel scroll up
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))

    def __bind_configure_event(self):
        """ Bind the configure event to the canvas """
        self.canvas.bind('<Configure>', self.__schedule_resize)

    def __unbind_configure_event(self):
        """ Unbind the confifure event from the canvas """
        self.canvas.unbind('<Configure>')

    def __schedule_resize(self, event):
        """ Schedile resize after a certain time """
        if self.path is None:
            self.file_name_coords(False)
            return

        if self._scheduled_config_call:
            self.canvas.after_cancel(self._scheduled_config_call)
        self._scheduled_config_call = self.canvas.after(300, self.__resize_image)

    def __resize_image(self):
        """ Resize image to equal canvas width """
        self._scheduled_config_call = 0

        self.close_image()
        img = Image.open(self.org_path)

        width = self.canvas.winfo_width()
        w, h = img.size
        change = width / w
        height = int(h * change)

        img = img.resize((width, height), self.__filter)
        self.path = self.path.parent / 'scaled.png'
        img.save(self.path)
        self.__create_image()

    def switch_image(self, path: Path):
        """ Change image displayed in canvas """
        self.org_path = path
        self.path = path
        self.__create_image()

    def refresh(self):
        """ Refresh image """
        self.__show_image()

    def smaller(self):
        """ Resize image proportionally and return smaller image """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k)+1), self.__filter), (0, int(i * k)))
            i += band
            j += 1
        print('\r' + 30*' ' + '\r', end='')  # hide printed string
        return image

    def redraw_figures(self):
        """ Dummy function to redraw figures in the children classes """
        pass

    def replace_image(self, path):
        """ Replace current image with new """
        self.path = path

    def close_image(self):
        """ Close image file and destory content """
        if self.path is not None:
            self.__image.close()
        
        if hasattr(self, '__pyramid'):
            map(lambda i: i.close, self.__pyramid)  # close all pyramid images
            del self.__pyramid[:]  # delete pyramid list
            del self.__pyramid  # delete pyramid variable

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        if self.path is None: return

        self.__unbind_configure_event()
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly

        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            self.canvas.imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(self.canvas.imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
            self.__bind_configure_event()

    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        if self.path is None: return

        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 102]:  # scroll right, keys 'd' or 'Right'
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in [65, 100]:  # scroll left, keys 'a' or 'Left'
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 104]:  # scroll up, keys 'w' or 'Up'
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 98]:  # scroll down, keys 's' or 'Down'
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def clear(self):
        """ Clear image from canvas """
        if self.path is not None:
            if hasattr(self.canvas, 'imageid'):
                self.canvas.delete(self.canvas.imageid)
            self.canvas.delete(self.container)
            self.canvas.configure(scrollregion=(0,0,self.canvas.winfo_width(), self.canvas.winfo_height()))  # set scroll region
            self.close_image()
            self.path = None

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()





if __name__ == "__main__":
    import ctypes
    from tkinter.filedialog import askopenfilename
    app = tk.Tk()
    ctypes.windll.shcore.SetProcessDpiAwareness(0)
    viewer = PdfViewer(app, width=900, height=900)
    viewer.pack(fill=tk.BOTH, expand=tk.TRUE)

    viewer.file = askopenfilename()
    app.mainloop()
