import abc
from typing import Any

import httpx
import numpy as np
from asyncer import asyncify
from fastapi import Request
from lightning import LightningWork
from lightning.app.structures import List
from requests import Response


class Strategy(abc.ABC):
    def select_method(self, request, local_router_metadata):
        method = request.method.lower()
        keys = list(local_router_metadata)
        if len(keys) > 1:
            selected_url = np.random.choice(
                keys, p=list(local_router_metadata.values())
            )
        else:
            selected_url = keys[0]
        return selected_url, method

    async def make_request(
        self, request: Request, full_path: str, local_router_metadata: Any
    ) -> Response:

        selected_url, method = await asyncify(self.select_method)(
            request, local_router_metadata
        )
        async with httpx.AsyncClient() as client:
            return await getattr(client, method)(selected_url + "/" + full_path)

    @abc.abstractmethod
    def run(self, serve_works: List[LightningWork]) -> Any:
        pass

    def on_after_run(self, serve_works: List[LightningWork], res):
        pass
