from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
 
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
        return f'{self.prefix}{self.current}'
    
    def save(self) -> None:
        self.number = self.current_number
    
    def reset(self) -> None:
        self.current_number = self.number

@dataclass 
class FolderMapping:
    souce: Path
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
        self.status = ''