from lightning import LightningWork
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from fastapi import Request
import requests
from requests import Response
from typing import Any
from multiprocessing.pool import ApplyResult
from multiprocessing.dummy import Pool
from functools import partial

class ShadowStrategy(Strategy):

    def __init__(self, wait_for_shadow_result: bool = False):
        super().__init__()
        self.pool = None
        self.wait_for_shadow_result = wait_for_shadow_result

    async def make_request(self, request: Request, full_path: str, local_router_metadata: Any) -> Response:
        if not self.pool:
            self.pool = Pool()

        if len(local_router_metadata) == 1:
            return await super().make_request(request, full_path, local_router_metadata)
        else:
            method_fn = getattr(requests, request.method.lower())
            current_endpoint, shadow_endpoint = local_router_metadata

            data = await request.body()
            current_future: ApplyResult = self.pool.apply_async(partial(method_fn, url=current_endpoint + "/" + full_path, data=data))
            shadow_future: ApplyResult = self.pool.apply_async(partial(method_fn, url=shadow_endpoint + "/" + full_path, data=data))

            current_result = current_future.get()
            if self.wait_for_shadow_result:
                shadow_result = shadow_future.get()
                if shadow_result.status_code != 200:
                    print(f"The shadow server hasn't properly processed the request {shadow_result.json()}")
            return current_result

    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) == 1:
            return {serve_works[-1].url: 1.0}

        for w in serve_works[:-2]:
            w.stop()

        return [w.url for w in serve_works[-2:]]
