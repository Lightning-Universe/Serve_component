import abc
from typing import Any

import numpy as np
import requests
from fastapi import Request
from requests import Response

from lightning import LightningWork
from lightning.structures import List


class Strategy(abc.ABC):
    async def make_request(
        self, request: Request, full_path: str, local_router_metadata: Any
    ) -> Response:
        method = request.method.lower()
        keys = list(local_router_metadata)
        if len(keys) > 1:
            selected_url = np.random.choice(
                keys, p=list(local_router_metadata.values())
            )
        else:
            selected_url = keys[0]
        return getattr(requests, method)(
            selected_url + "/" + full_path, data=await request.body()
        )

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass
