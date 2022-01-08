import ctypes
import shutil
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import ttk
from tkinter.filedialog import askdirectory
from typing import Dict, List, Optional

import model
import pdf_viewer
from item_treeview import DocumentInfoTree
import pickle

class Event:
    DO_UPDATE_DOCUMENTS = '<<DO_UPDATE_DOCUEMENTS>>'
    DO_SEARCH_DOCUMENTS = '<<DO_SEARCH_DOCUMENTS>>'
    DO_MOVE_DOCUMENTS = '<<DO_MOVE_DOCUMENTS>>'
    DO_DOCUMENT_SELECTED = '<<DO_DOCUMENT_SELECTED>>'
    DO_REGISTER_DOCUMENT = '<<DO_REGISTER_DOCUMENT>>'


class NumberSeriesEditor(tk.Frame):
    def __init__(self, master, numberseries: model.NumberSeries, **kwargs):
        super().__init__(master, **kwargs)
        self.numberseries = numberseries

        gui_list = tk.Listbox(self)
        gui_list.insert('end', *self.numberseries)

class DocumentOverview(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var_search_query = tk.StringVar()

        f_buttons = ttk.Frame(self)
        f_buttons.pack(side='top', fill='x')

        ttk.Entry(f_buttons, textvariable=self.var_search_query).pack(side='left')
        ttk.Button(f_buttons, text='Søk', command=self.on_search).pack(side='left')
        ttk.Button(f_buttons, text='Oppdater', command=self.on_update_documents).pack(side='left')
        ttk.Button(f_buttons, text='Bekreft', command=self.on_confirm_change).pack(side='left')

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
    
    def on_confirm_change(self) -> None:
        self.event_generate(Event.DO_MOVE_DOCUMENTS)
    
    def on_document_selected(self, event = None) -> None:
        self.event_generate(Event.DO_DOCUMENT_SELECTED)

    def _on_register_document(self, event = None) -> None:
        self.event_generate(Event.DO_REGISTER_DOCUMENT)

class App:
    def __init__(self, series, mappings):
        self.gui = tk.Tk()

        self.numberseries: Dict[str, model.NumberSeries] = series
        self.dst: List[model.FolderMapping] = mappings
        self.documents: List[model.DocumentInfo] = []
        
        self.pdf_viewer = pdf_viewer.PdfViewer()

        panes = ttk.Panedwindow(self.gui, orient='horizontal')
        self.document_overview = DocumentOverview(panes)
        self.viewer_frame = self.pdf_viewer.create_viewer(panes)
        self.document_overview.bind(Event.DO_UPDATE_DOCUMENTS, self.on_update_documents)
        self.document_overview.bind(Event.DO_DOCUMENT_SELECTED, self.on_selected_document)
        self.document_overview.bind(Event.DO_MOVE_DOCUMENTS, self.on_move_documents)
        # self.document_overview.bind(Event.DO_SELECT_FOLDER, self.db.select_location)
        self.document_overview.bind(Event.DO_REGISTER_DOCUMENT, self.register_document)

        panes.pack(side='top', expand=True, fill='both')
        panes.add(self.document_overview, weight=1)
        panes.add(self.viewer_frame, weight=1)

    def on_update_documents(self, event = None) -> None:
        self.documents = []
        for mapping in self.dst:
            for f in mapping.source.glob('*.pdf'):
                self.documents.append(model.DocumentInfo(f))
        self.document_overview.documents.content = self.documents
        
        # Reset numberseries to last saved default values
        for ns in self.numberseries.values():
            ns.reset()
    
    def on_selected_document(self, event = None) -> None:
        if f := self.document_overview.selected_document:
            self.pdf_viewer.display(Path(f.link))

    def on_move_documents(self, event = None) -> None:
        pending_documents = (d for d in self.documents if d.is_pending)

        for d in pending_documents:
            dst_name = d.dst_folder / f'{d.name}'
            shutil.copy2(d.link, dst_name)
            d.status = model.Status.MOVED
            self.document_overview.update_document(d)
        
        # Save the changes in numberseries
        for ns in self.numberseries.values():
            ns.save()
    
    def register_document(self, event = None) -> None:
        doc = self.document_overview.selected_document
        
        if doc is None:
            return
        
        if doc.status != model.Status.OK:
            return
        
        mapping = [m for m in self.dst if m.source == doc.source][0]

        num_ser = self.numberseries[mapping.prefix]
        doc.name =num_ser.next()
        doc.dst_folder = mapping.destination
        doc.status = model.Status.PENDING

        self.document_overview.update_document(doc)

def main() -> None:
    pkl_ms = Path('ms.p')
    pkl_ns = Path('ns.p')
    series = {}
    mappings = []

    if pkl_ms.exists():
        with open(pkl_ms, 'rb') as m:
            mappings = pickle.load(m)
    
    if pkl_ns.exists():
        with open(pkl_ns, 'rb') as s:
            series = pickle.load(s)


    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    app = App(series, mappings)

    print(series)
    while input('Add numberseries? y/n ') == 'y':
        prefix = input('Series prefix: ')
        number = int(input('Number: '))
        series[prefix] = model.NumberSeries(prefix, number)
        print(series)
    
    print(mappings)
    while input('Add folder mapping? y/n ') == 'y':
        prefix = input('Numberseries prefix: ')
        source = Path(askdirectory(title='Select source'))
        dest = Path(askdirectory(title='Select destination'))

        mappings.append(model.FolderMapping(source, dest, prefix))
        print(mappings)

    print('Open GUI.')
    app.gui.mainloop()

    with open(pkl_ms, 'wb') as m, open(pkl_ns, 'wb') as s:
        pickle.dump(mappings, m)
        pickle.dump(series, s)

if __name__ == '__main__':
    main()
