""" Program to display, rename, and move PDF files in a company folder structure """
from pathlib import Path
import tkinter as tk
import tkinter.filedialog as tkfd
import dataclasses
import datetime
from typing import Generator, List

str_msg_select_folder = 'Select folder: '
str_select_folder_source = 'Select source folder'
str_select_folder_destination = 'Select destination folder'

def select_folder(win_title: str) -> Path:
    return Path(tkfd.askdirectory(title=win_title))

def select_folder_source() -> Path: return select_folder(str_select_folder_source)
def select_folder_destination() -> Path: return select_folder(str_select_folder_destination)

@dataclasses.dataclass
class Document:
    date: datetime.datetime
    link: Path
    source: Path
    name: str = ''

def get_documents(source: Path) -> Generator[Document, None, None]:
    for doc in source.glob('*.pdf'):
        yield Document(date=datetime.datetime.now(), link=doc, source=source)

def main() -> None:
    src = select_folder_source()
    dst = select_folder_destination()

    docs = get_documents(src)

    for d in docs:
        print(d)
    
    


if __name__ == '__main__':
    main()