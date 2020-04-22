import typing

from .folder import Folder
from .phrase import Phrase
from .script import Script

Item = typing.Union[Folder, Phrase, Script]
