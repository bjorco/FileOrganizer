import ctypes
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import ttk
from tkinter.filedialog import askdirectory
from typing import Dict, List, Optional

import model
import pdf_viewer
from item_treeview import DocumentInfoTree


class Event:
    DO_UPDATE_DOCUMENTS = '<<DO_UPDATE_DOCUEMENTS>>'
    DO_SEARCH_DOCUMENTS = '<<DO_SEARCH_DOCUMENTS>>'
    DO_SELECT_FOLDER = '<<DO_FOLDER_SELECT>>'
    DO_DOCUMENT_SELECTED = '<<DO_DOCUMENT_SELECTED>>'
    DO_REGISTER_DOCUMENT = '<<DO_REGISTER_DOCUMENT>>'


class NumberSeriesEditor(tk.Frame):
    def __init__(self, master, numberseries: model.NumberSeries, **kwargs):
        super().__init__(master, **kwargs)
        self.numberseries = numberseries

        gui_list = tk.Listbox(self)
        gui_list.insert('end', *self.numberseries)




class DocumentStore:
    def __init__(self, location: Optional[Path]=None):
        self.location = location
        self.documents: Dict[str, model.DocumentInfo] = {}
        self.read_documents()
    
    def read_documents(self, event = None) -> None:
        if self.location is None:
            self.select_location()
        
        for doc in self.location.glob('*.pdf'):
            self.documents[str(doc)] = model.DocumentInfo(doc)

    def select_location(self, event = None) -> None:
        """ Select location for the document store """
        if path := askdirectory(title='Select source folder for documents.'):
            self.location = Path(path)

class DocumentOverview(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var_search_query = tk.StringVar()

        f_buttons = ttk.Frame(self)
        f_buttons.pack(side='top', fill='x')

        ttk.Entry(f_buttons, textvariable=self.var_search_query).pack(side='left')
        ttk.Button(f_buttons, text='Søk', command=self.on_search).pack(side='left')
        ttk.Button(f_buttons, text='Oppdater', command=self.on_update_documents).pack(side='left')
        ttk.Button(f_buttons, text='Velg mappe', command=self.on_select_folder).pack(side='left')

        self.documents = DocumentInfoTree(self)
        self.documents.pack(side='top', fill='both', expand=True)

        self.documents.bind('<<TreeviewSelect>>', self.on_document_selected)
        self.documents.bind('<F3>', self._on_register_document)
    
    @property
    def selected_document(self) -> Optional[model.DocumentInfo]:
        if adapter := self.documents.selected:
            return adapter.item
        else:
            return None
    
    def update_document(self, documentinfo: model.DocumentInfo) -> None:
        self.documents.update_object(documentinfo)
        
    def on_search(self) -> None:
        self.documents.searcher(self.var_search_query.get())
        self.event_generate(Event.DO_SEARCH_DOCUMENTS)
    
    def on_update_documents(self) -> None:
        self.event_generate(Event.DO_UPDATE_DOCUMENTS)
    
    def on_select_folder(self) -> None:
        self.event_generate(Event.DO_SELECT_FOLDER)
    
    def on_document_selected(self, event = None) -> None:
        self.event_generate(Event.DO_DOCUMENT_SELECTED)

    def _on_register_document(self, event = None) -> None:
        self.event_generate(Event.DO_REGISTER_DOCUMENT)

class App:
    def __init__(self, series, mappings):
        self.gui = tk.Tk()

        self.numberseries: List[model.NumberSeries] = series
        self.dst: List[model.FolderMapping] = mappings
        
        self.db = DocumentStore(Path('.'))
        self.pdf_viewer = pdf_viewer.PdfViewer()

        panes = ttk.Panedwindow(self.gui, orient='horizontal')
        self.document_overview = DocumentOverview(panes)
        self.viewer_frame = self.pdf_viewer.create_viewer(panes)

        self.document_overview.documents.content = self.db.documents.values()
        self.document_overview.bind(Event.DO_UPDATE_DOCUMENTS, self.on_update_documents)
        self.document_overview.bind(Event.DO_DOCUMENT_SELECTED, self.on_selected_document)
        self.document_overview.bind(Event.DO_SELECT_FOLDER, self.db.select_location)
        self.document_overview.bind(Event.DO_REGISTER_DOCUMENT, self.register_document)

        panes.pack(side='top', expand=True, fill='both')
        panes.add(self.document_overview, weight=1)
        panes.add(self.viewer_frame, weight=1)

    def on_update_documents(self, event = None) -> None:
        documents = []
        for mapping in self.dst:
            for f in mapping.source.glob('*.pdf'):
                documents.append(model.DocumentInfo(f))
        self.document_overview.documents.content = documents
        # self.db.read_documents()
        # self.document_overview.documents.content = self.db.documents.values()
    
    def on_selected_document(self, event = None) -> None:
        if f := self.document_overview.selected_document:
            self.pdf_viewer.display(Path(f.link))
    
    def register_document(self, event = None) -> None:
        doc = self.document_overview.selected_document

        if doc is None:
            return
        
        doc.name = f'ZK{self.numberseries}'
        self.numberseries += 1
        doc.dst_folder = self.dst
        doc.status = 'Pending'

        self.document_overview.update_document(doc)

def main() -> None:
    series = []
    mappings = []

    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    app = App(series, mappings)

    while input('Add numberseries? y/n ') == 'y':
        prefix = input('Series prefix: ')
        number = int(input('Number: '))
        ns = model.NumberSeries(prefix, number)
        series.append(ns)
        print(series)
    
    while input('Add folder mapping? y/n ') == 'y':
        prefix = input('Numberseries prefix: ')
        source = Path(askdirectory(title='Select source'))
        dest = Path(askdirectory(title='Select destination'))

        mappings.append(model.FolderMapping(source, dest, prefix))

    app.gui.mainloop()

if __name__ == '__main__':
    main()
