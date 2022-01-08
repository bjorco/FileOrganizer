from tkinter import ttk, font
from typing import Any, TypeVar, Dict, Tuple
import abc
from scrollbar_treeview import ScrollbarTreeview

class TreeviewAdapter(abc.ABC):
    """ Abstract class for containing objects to be displayed in a treeview """
    def __init__(self, item):
        self.item = item
        self.iid = None
        self.is_comments_allowed = True

    @abc.abstractmethod
    def text(self): return

    @abc.abstractmethod
    def values(self): return

    def tag(self, index) -> Tuple[str]:
        return ('odd',) if index % 2 else ('even',)

    def key(self) -> str:
        return self.generate_key(self.item)
    
    @staticmethod
    def generate_key(item) -> str:
        return f'<{item.__class__.__qualname__}({item.link})>'

class DocumentInfoAdapter(TreeviewAdapter):
    headings = ['DATE', 'FOLDER', 'NAME', 'STAUTS']

    def __init__(self, document_info):
        super().__init__(document_info)

    def folder(self) -> str:
        if self.item.dst_folder is None:
            return self.item.source.name
        else:
            src = self.item.source.name
            dst = self.item.dst_folder.name
            return f'{src}->{dst}'

    def text(self):
        return self.item.link
    
    def values(self):
        return (
            f'{self.item.date:%Y-%m-%d}',
            self.folder(),
            self.item.name,
            self.item.status
        )
    
    def key(self) -> str:
        return self.item.link


Adapter = TypeVar('Adapter', bound=DocumentInfoAdapter)

class ItemTreeview(ttk.Treeview):
    def __init__(self, master, adapter, *args, **kwargs):
        super().__init__(master, columns=adapter.headings, show='headings', **kwargs)
        self.adapter_class = adapter

        self.font = 'helvetica 10'
        self.style = ttk.Style()
        self.style.configure('Treeview', 
                font=self.font,
                rowheight=font.Font(font=self.font).metrics('linespace') + 5)
        self.style.configure('Treeview.Heading', 
                font=self.font,
                rowheight=font.Font(font=self.font).metrics('linespace') + 20)
        self.style.configure('Scaling.Treeview',  
                rowheight=font.Font(font=self.font).metrics('linespace') + 5)

        self.style.map('Treeview', foreground=self.fixed_map('foreground'), background=self.fixed_map('background'))

        self.displayed_columns = []
        for h in self.adapter_class.headings:
            self.heading(h, text=h, command=lambda h=h: self.on_sort(h))
            self.column(h, width=10, stretch=True)

            self.displayed_columns.append(h)
        
        self['displaycolumns'] = self.displayed_columns

        self.tag_configure('even', background='lightsteelblue', foreground='blue4')
        self.tag_configure('odd', background='whitesmoke', foreground='blue4')

        self._content: Dict[str, Adapter] = {}
        self._item_content: Dict[str, Adapter] = {}
    
    def fixed_map(self, option):
        """
            Fix for setting text colour for Tkinter 8.6.9
            From: https://core.tcl.tk/tk/info/509cafafae
            
            Returns the style map for 'option' with any styles starting with
            ('!disabled', '!selected', ...) filtered out.

            style.map() returns an empty list for missing options, so this
            should be future-safe.
        """
        return [elm for elm in self.style.map('Treeview', query_opt=option) if elm[:2] != ('!disabled', '!selected')]

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, objects):
        self._content = {}

        for o in objects:
            adapter = self.create_adapter(o)
            self._content[adapter.key()] = adapter

        self.build_tree()
    
    @property
    def selected_text(self):
        return self.item(self.focus())['text']
    
    @property
    def selected(self):
        return self._item_content.get(self.focus(), None)
    
    def create_adapter(self, object) -> Adapter:
        return self.adapter_class(object)

    def focus_to_position(self, pos=-1):
        """ Move focus to item in position if possible """
        # Focus on view incase application is focused elsewhere
        self.focus_set()

        children = self.get_children()
        if -1 < pos < len(children):
            self.focus(children[pos])
            self.selection_set(children[pos])
        elif pos >= len(children) and len(children):
            self.focus(children[-1])
            self.selection_set(children[-1])
        else:
            self.focus_set()
            self.selection_set()

    def update_object(self, object: Any):
        object_adapter = self.create_adapter(object)
        key = object_adapter.key()

        if key in self.content:
            adapter = self.content[key]

            if object is None:
                self.delete(adapter.iid)
                del self._item_content[adapter.iid]
                del self.content[key]
            else:
                adapter.object = object
                index = self.index(adapter.iid)
                self.item(adapter.iid, values=adapter.values(), tag=adapter.tag(index))
        else:
            if object is not None:
                adapter = self.create_adapter(object)
                self.create_item(adapter, index=len(self.content))

                self._content[key] = adapter

                self.focus(adapter.iid)
                self.selection_set(adapter.iid)

    def delete_object(self, object: Any):
        key = self.adapter_class.generate_key(object)
        if key in self.content:
            adapter = self._content[key]
            
            self.delete(adapter.iid)

            del self._content[key]
            del self._item_content[adapter.iid]

    def build_tree(self):
        self.clear_tree()

        for i, adapter in enumerate(self.content.values()):
            self.create_item(adapter, i)

    def clear_tree(self):
        self._item_content = {}
        self.delete(*self.get_children())

    def create_item(self, adapter, index):
        adapter.iid = self.insert(
            parent='', 
            index='end', 
            text=adapter.text(), 
            values=adapter.values(), 
            tag=adapter.tag(index)
        )
        
        self._item_content[adapter.iid] = adapter

    def on_sort(self, heading: str = None, reverse: bool = True):
        # Create list with a tuple of value at selected column and itemid
        if heading is None:
            heading = self.adapter_class.headings[0]
            reverse = False
          
        l = [(self.set(iid, heading), iid) for iid in self.get_children()]

        # Try to sort as numbers
        try:
            l.sort(key=lambda t: float(str(t[0]).replace(' ','').replace(',','.')), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]), reverse=reverse)

        # Move items based on itemid
        for index, (_, iid) in enumerate(l):
            adapter = self._item_content[iid]
            self.item(iid, tags=adapter.tag(index))
            self.move(iid, '', index)

        # Reverse sorting function
        self.heading(heading, command=lambda h=heading: self.on_sort(h, not reverse))



class SearchableTree(ttk.Treeview):
    """ Treeview with search method for items """
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self._detached = set()

        # Number for columns to search 
        self._num_search_values = 2

    def searcher(self, query: str):
        """ Checks if treeview contains query and attaches/detaches them. The detached items are
            stored in a set so they can be reattached later. 
        """
        children = list(self._detached) + list(self.get_children())
        self._detached = set()

        i_r = -1
        for item_id in children:
            values = self.item(item_id)['values'][:self._num_search_values]
            text = ', '.join(str(v).lower() for v in values)
            if query.lower() in text:
                i_r += 1
                self.reattach(item_id, '', i_r)
            else:
                self._detached.add(item_id)
                self.detach(item_id)
        
        self.event_generate('<<TreeviewSearched>>')

class DocumentInfoTree(ItemTreeview, SearchableTree, ScrollbarTreeview):
    def __init__(self, master, **kwargs):
        super().__init__(master=master, adapter=DocumentInfoAdapter)
        self._num_search_values = 3