from tkinter import ttk

class AutohideScrollbar(ttk.Scrollbar):
    """ Scrollbar that automaticaly palces and hide with on mousewheel scroll """

    HIDE_DELAY = 800

    def __init__(self, *args, **kwargs):
        self.margin_top = kwargs.pop('margin_top') if 'margin_top' in kwargs else 0
        command_wrapper = kwargs.pop('command_wrapper') if 'command_wrapper' in kwargs else None
        super().__init__(*args, **kwargs)

        self.configure(orient=kwargs['orient'] if 'orient' in kwargs else 'vertical')
        self.configure(command=kwargs['command'] if 'command' in kwargs else self.master.yview)
        
        yscrollcommand = self.set if command_wrapper is None else lambda *args: command_wrapper(self.set, *args)
        self.master.configure(yscrollcommand=yscrollcommand)

        self.__isplaced = False
        self.__isactive = False
        self.__ismousedown = False
        self.__cancel_id = None 

        self.__init_bindings()

    
    def __init_bindings(self):
        """ Initialize bindings """
        self.master.bind('<Enter>', lambda _: self.bind_all('<MouseWheel>', self.display))
        self.master.bind('<Leave>', lambda _: self.unbind_all('<MouseWheel>'))

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

        self.bind('<Button-1>', self._on_mousedown)
        self.bind('<ButtonRelease-1>', self._on_mouserelease)

    def _on_enter(self, event):
        """ Called when mouse enters widget """
        self.cancel_hide()
        self.__isactive = True
    
    def _on_leave(self, event):
        """ Called when mouse leaves widget """
        if not self.__ismousedown:
            self.schedule_hide()
        self.__isactive = False
    
    def _on_mousedown(self, event):
        """ Called when mouse clicks widget """
        self.__ismousedown = True

    def _on_mouserelease(self, event):
        """ Called when mouse is released """
        self.__ismousedown = False
        self.schedule_hide()
    
    def schedule_hide(self, time: int = 0):
        """ Set widget to be hidden after a time """
        self.cancel_hide()
        self.__cancel_id = self.after(time if time else self.HIDE_DELAY, self.hide)

    def cancel_hide(self):
        """ Cancel scheduled hide """
        if self.__cancel_id is not None:
            self.after_cancel(self.__cancel_id)

    def display(self, event):
        """ Place in master and schedule hide """
        if not self.__isplaced:
            self.place(relx=1, x=-1, rely=0, y=self.margin_top + 1, relheight=1, height=-self.margin_top - 1, anchor='ne')
            self.__isplaced = True
        
        self.schedule_hide()
    
    def hide(self):
        """ Remove from master """
        if self.__isplaced and not self.__isactive:
            self.place_forget()
            self.__isplaced = False


class ScrollbarTreeview(ttk.Treeview):
    """ Treeview with a scrollbar that calls on_scroll() """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.scrollbar = AutohideScrollbar(self, command_wrapper=self.__wrapper)

    def __wrapper(self, callback, *args):
        callback(*args)
        self.on_scroll()
    
    def on_scroll(self):
        pass