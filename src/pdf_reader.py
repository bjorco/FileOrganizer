import calendar
import enum
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from tkinter.filedialog import askdirectory
from typing import Dict, Optional

import pyautogui
from PyPDF2 import PdfFileReader


def enter_invoice(invoice):
    pyautogui.PAUSE = 0.2
    pyautogui.hotkey('alt', 'tab')

    pyautogui.write(invoice.date)
    pyautogui.press('tab')
    pyautogui.write(invoice.number)
    pyautogui.press('down', presses=2)
    pyautogui.write(invoice.amount)
    pyautogui.press('down', presses=3)
    pyautogui.press('tab')
    pyautogui.write(invoice.workorder)
    pyautogui.press('enter')

MONTHS = {month: index for index, month in enumerate(calendar.month_abbr) if month}

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

class InvoiceParsingException(Exception):
        def __init__(self, message):
            super().__init__(message)

class MissingWorkorderException(Exception): pass

def match_invoice_text(text, search_term, match_regex):
    if match := re.search(f'{search_term}{match_regex}', text):
        return match.group(1)
    else:
        raise InvoiceParsingException(f'Unable to parse "{search_term}"')

class InvoiceStatus(enum.Enum):
    PENDING = enum.auto()
    OK = enum.auto()
    ERROR_MISSING_WO = enum.auto()
    ERROR = enum.auto()

class NCL_Invoice:
    def __init__(self):
        self.status = InvoiceStatus.PENDING
        self._number = ''
        self._date = ''
        self._amount = ''
        self._workorder = ''
    
    @property
    def number(self) -> str: return self._number

    @number.setter
    def number(self, value: str) -> None:
        self._number = value

    @property
    def date(self) -> str: return self._date

    @date.setter
    def date(self, value: str) -> None:
        month = MONTHS[value[:3]]
        day = value[4:6]
        year = value[8:]

        self._date = f'{day}{month}{year}'
    
    @property
    def amount(self) -> str: return self._amount

    @amount.setter
    def amount(self, value: str) -> None:
        self._amount = value.replace(',', '').replace('.', ',')

    @property
    def workorder(self) -> str: return self._workorder

    @workorder.setter
    def workorder(self, value: str) -> None:
        p1, p2 = value.split('/')
    
        if p1[0] == '9':
            self._workorder = p1
        elif p2[0] == '9':
            self._workorder = p2
        else:
            raise MissingWorkorderException

    def __str__(self) -> str:
        return f'{self.__class__.__qualname__}({self.number!r}, {self.date!r}, {self.amount!r}, {self.workorder!r})'

def print_ncl_info(document: Path):
    pdf_text = extract_text(document)
    invoice = NCL_Invoice()

    invoice.number = match_invoice_text(pdf_text, 'Invoice Number:', '(\d+)')
    invoice.date = match_invoice_text(pdf_text, 'Invoice Date:', r'(\w{3} \d{2}[,] \d{4})')
    invoice.amount = match_invoice_text(pdf_text, 'Invoice Total:', 'EUR (\d{1,3}(?:,\d{3})*\.\d{2})')
    
    try:
        invoice.workorder = match_invoice_text(pdf_text, 'Booking Number:', '(\d+[/]\d+)')
    except MissingWorkorderException:
        invoice.status = InvoiceStatus.ERROR_MISSING_WO
    print(f'{document.name} - {invoice}')
    return invoice

def parse_invoice_folder():
    folder = Path(askdirectory())
    error_folder = folder / 'error'
    error_folder.mkdir(exist_ok=True)
            
    for f in folder.glob('*.pdf'):
        try:
            invoice = print_ncl_info(f)
        except InvoiceParsingException:
            shutil.copy2(f, error_folder)        
            print(f'{f.name} - Error')
        else:
            if input('Enter document? ') == 'ok':
                enter_invoice(invoice)
            else:
                break


if __name__ == '__main__':
    parse_invoice_folder()
