import os
import subprocess
import typing as t
from time import time

import requests
from deepdiff import DeepHash
from lightning import LightningFlow, LightningWork
from lightning.app.components.python import TracerPythonScript
from lightning.app.structures import List

from lightning_serve.proxy import PROXY_ENDPOINT
from lightning_serve.strategies import _STRATEGY_REGISTRY
from lightning_serve.strategies.base import Strategy


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


class Locust(LightningWork):
    def __init__(self, num_users: int):
        super().__init__(port=8089)
        self.num_users = num_users

    def run(self, host: str):
        cmd = " ".join(
            [
                "locust",
                "--master-host",
                str(self.host),
                "--master-port",
                str(self.port),
                "--host",
                str(host),
                "-u",
                str(self.num_users),
            ]
        )
        subprocess.Popen(cmd, shell=True).wait()


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
        self._strategy = (
            strategy
            if isinstance(strategy, Strategy)
            else _STRATEGY_REGISTRY[strategy]()
        )
        self.serve_works = List()
        self.hashes = []
        self.proxy = Proxy()
        self._router_refresh = router_refresh
        self._last_update_time = time()
        self.locust = Locust(100)

    def run(self, **kwargs):
        # Step 1: Start the proxy
        if not self.proxy.has_started:
            self.proxy.run(strategy=self._strategy)

        if self.proxy.alive():
            self.locust.run(self.proxy.url)

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
