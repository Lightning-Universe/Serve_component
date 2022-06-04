from lightning import LightningWork
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from fastapi import Request
from typing import Any


class ABTestingStrategy(Strategy):

    METHODS = ["weighted", "headers", "cookie"]

    def __init__(self, method: str):
        assert method in self.METHODS
        self.method = method
        self.urls = {}

    async def on_router_request(self, request: Request, full_path: str, local_router_metadata: Any):
        if self.method == "weighted":
            return super().on_router_request(request, full_path, local_router_metadata)
        else:
            raise NotImplementedError

    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) < 2:
            return {w.url: 1.0 for w in serve_works}

        if self.method == "weighted":
            works = [w for w in serve_works if w.url != '']
            return {w.url: 1.0 / len(works) for w in works}
        else:
            raise NotImplementedError