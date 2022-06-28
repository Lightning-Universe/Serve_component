import abc
from typing import Any

import httpx
import numpy as np
from fastapi import Request
from lightning import LightningWork
from lightning.app.structures import List
from requests import Response


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

        async with httpx.AsyncClient() as client:
            return await getattr(client, method)(selected_url + "/" + full_path)

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass
