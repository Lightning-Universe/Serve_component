from lightning import LightningWork
from lightning.structures import List
from typing import Any
import abc
import requests
import numpy as np
from fastapi import Request

class Strategy(abc.ABC):

    def __init__(self):
        pass

    async def on_router_request(self, request: Request, full_path: str, local_router_metadata: Any):
        random_url = np.random.choice(list(local_router_metadata.keys()), p=list(local_router_metadata.values()))
        response = getattr(requests, request.method)(random_url + "/" + full_path, data=await request.body())
        return response.json()

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass
