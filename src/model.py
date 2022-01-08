import enum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class Status(enum.Enum):
    OK = enum.auto()
    PENDING = enum.auto()
    MOVED = enum.auto()

class NumberSeries:
    def __init__(self, prefix, number):
        self.prefix = prefix
        self.number = number
        self.current_number = self.number
    
    def restart_series(self, number):
        """ Restart the series from the given number. """
        self.number = number
        self.current_number = self.number

    def next(self) -> str:
        """ Returns the next filenumber in the series. """
        self.current_number += 1
        return f'{self.prefix}{self.current_number}'
    
    def save(self) -> None:
        self.number = self.current_number
    
    def reset(self) -> None:
        self.current_number = self.number
    
    def __str__(self) -> str:
        return f'<{self.__class__.__qualname__}({self.prefix!r}, {self.number!r})>'
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__qualname__}({self.prefix!r}, {self.number!r})>'

@dataclass 
class FolderMapping:
    source: Path
    destination: Path
    prefix: str

@dataclass
class DocumentInfo:
    def __init__(self, link: Path):
        self.link = link
        self.source = link.parent
        self.name = self.link.name
        self.date = datetime.now()
        self.dst_folder = None
        self.status = Status.OK
    
    @property
    def is_pending(self) -> bool:
        return self.status == Status.PENDING
