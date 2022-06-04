import typing as t
from lightning import LightningFlow, LightningWork
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from deepdiff import DeepHash
from lightning.components.python import TracerPythonScript
import os
import requests
from time import time

class ServeWork(TracerPythonScript):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, parallel=True, **kwargs)

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(serve_work=self, **kwargs)

    def alive(self):
        return self.url != ""

class BaseRouter(TracerPythonScript):

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            parallel=True,
            script_path=os.path.join(os.path.dirname(__file__), "router.py"),
            raise_exception=True,
            **kwargs,
        )
        self.routing = None

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(router=self, **kwargs)

    def alive(self):
        return self.url != ""

class ServeFlow(LightningFlow):

    def __init__(
        self,
        work_cls: t.Type[LightningWork],
        strategy: Strategy,
        work_kwargs: t.Optional[t.Dict[str, t.Any]] = None,
        router_refresh: int = 1,
    ):
        super().__init__()
        self._work_cls = work_cls
        self._work_kwargs = work_kwargs
        self._strategy = strategy
        self.serve_works = List()
        self.hashes = []
        self.router = BaseRouter()
        self.base_url = ""
        self._router_refresh = router_refresh
        self._last_update_time = time()

    def run(self, **kwargs):
        if not self.router.has_started:
            self.router.run()
        call_hash = DeepHash(kwargs)[kwargs]
        if call_hash not in self.hashes:
            serve_work = self._work_cls(**(self._work_kwargs or {}))
            self.hashes.append(call_hash)
            self.serve_works.append(serve_work)
            serve_work.run(**kwargs)

        if self.router.alive() and self.serve_works[-1].alive():
            res = self._strategy.run(self.serve_works)
            if len(res) == 1:
                self.base_url = list(res.keys())[0]
            else:
                new_update_time = time()
                if (new_update_time - self._last_update_time) > self._router_refresh:
                    assert sum(res.values()) == 1.0
                    requests.post(self.router.url + "/update_router", json=res)
                    self._last_update_time = new_update_time
                    self.base_url = self.router.url