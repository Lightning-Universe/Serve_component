from lightning import LightningWork
from lightning.structures import List
from typing import Any
import abc
import requests
import numpy as np
from fastapi import Request

class Strategy(abc.ABC):

    def select_url(self, request: Request, full_path: str, local_router_metadata: Any) -> str:
        keys = list(local_router_metadata)
        if len(keys) > 1:
            return np.random.choice(keys, p=list(local_router_metadata.values()))
        return keys[0]

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass
