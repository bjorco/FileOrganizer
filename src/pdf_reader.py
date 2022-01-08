from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from PyPDF2 import PdfFileReader


@dataclass
class DocumentInfo:
    status: str
    sysped_ref: str
    tr_no: int
    po_no: int
    listdate: str
    listtime: str
    etd: str
    eta: str
    link: str


def extract_text(pdf_file: Path) -> str:
    """ Extract text from PDF """
    with open(pdf_file, 'rb') as stream:
        reader = PdfFileReader(stream)
        page = reader.getPage(0)
        return page.extractText()

def print_pdf_text(pdf_file: Path) -> None:
    """ Print content of PDF file """
    text = extract_text(pdf_file)

    for i, line in enumerate(text.split()):
        print(f'{i:03d} - {line}')

def extract_info(pdf_file: Path) -> DocumentInfo:
    """ Extract content from PDF and construct an object """
    text = extract_text(pdf_file)
    arr = text.split()[:18]

    # TODO: Validate content
    if arr[1] not in ('(UPDATED)', '(NEW)'):
        arr.insert(1, '(?)')

    return DocumentInfo(
        status=arr[1],
        sysped_ref=f'{arr[7]}/{arr[9]}',
        tr_no=arr[11],
        po_no=arr[13],
        listdate=arr[3],
        listtime=arr[5] if len(arr[5]) == 8 else f'0{arr[5]}',
        etd=arr[15],
        eta=arr[17],
        link=str(pdf_file)
    )

def parse_folder_content(folder: Path, exclude: Optional[Dict[str, DocumentInfo]] = None) -> Dict[str, DocumentInfo]:
    """ Parse PDFs in given folder for info and add them to documents """
    if exclude is None:
        exclude = {}

    documents = {}

    for pdf in folder.glob('*.pdf'):
        # Skip PDFs that have been stored in documents before
        if str(pdf) in exclude:
            continue

        info = extract_info(pdf)
        documents[info.link] = info
    
    return documents
