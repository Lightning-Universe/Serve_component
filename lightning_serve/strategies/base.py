from lightning import LightningWork
from lightning.structures import List
from typing import Any
import abc
import requests
import numpy as np
from fastapi import Request

class Strategy(abc.ABC):

    async def process_request(self, request: Request, full_path: str, local_router_metadata: Any):
        keys = list(local_router_metadata)
        if len(keys) > 1:
            base_url = np.random.choice(keys, p=list(local_router_metadata.values()))
        else:
            base_url = keys[0]
        response = getattr(requests, request.method.lower())(base_url + "/" + full_path, data=await request.body())
        return response.json()

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass
