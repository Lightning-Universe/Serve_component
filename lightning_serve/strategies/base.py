from lightning import LightningWork
from lightning.structures import List
import abc
from typing import Dict

class Strategy(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Dict[str, float]:
        pass
