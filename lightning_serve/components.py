import typing as t
from lightning import LightningFlow
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from lightning_serve.strategies import _STRATEGY_REGISTRY
from deepdiff import DeepHash
from lightning.components.python import TracerPythonScript
import os
import requests
from lightning_serve.proxy import PROXY_ENDPOINT
from time import time




class ServeWork(TracerPythonScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, parallel=True, **kwargs)

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(serve_work=self, **kwargs)

    def alive(self):
        return self.url != ""

class Proxy(TracerPythonScript):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            parallel=True,
            script_path=os.path.join(os.path.dirname(__file__), "proxy.py"),
            raise_exception=True,
            **kwargs,
        )
        self.routing = None

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(proxy=self, **kwargs)

    def alive(self):
        return self.url != ""

class ServeFlow(LightningFlow):

    def __init__(
        self,
        strategy: t.Union[Strategy, "str"],
        router_refresh: int = 1,
        **work_kwargs,
    ):
        super().__init__()
        self._work_cls = ServeWork
        self._work_kwargs = work_kwargs
        self._strategy = strategy if isinstance(strategy, Strategy) else _STRATEGY_REGISTRY[strategy]()
        self.serve_works = List()
        self.hashes = []
        self.proxy = Proxy()
        self._router_refresh = router_refresh
        self._last_update_time = time()

    def run(self, **kwargs):
        # Step 1: Start the proxy
        if not self.proxy.has_started:
            self.proxy.run(strategy=self._strategy)

        # Step 2: Compute a hash of the keyword arguments.
        call_hash = DeepHash(kwargs)[kwargs]
        if call_hash not in self.hashes:
            serve_work = self._work_cls(**(self._work_kwargs or {}))
            self.hashes.append(call_hash)
            self.serve_works.append(serve_work)
            serve_work.run(**kwargs)

        if self.proxy.alive() and self.serve_works[-1].alive():
            res = self._strategy.run(self.serve_works)
            new_update_time = time()
            if (new_update_time - self._last_update_time) > self._router_refresh:
                requests.post(self.proxy.url + PROXY_ENDPOINT, json=res)
                self._last_update_time = new_update_time