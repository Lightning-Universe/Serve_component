import multiprocessing
import os
import pickle
import subprocess
import sys
import typing as t
from time import time

from deepdiff import DeepHash
from lightning import LightningFlow
from lightning.app import BuildConfig, LightningWork
from lightning.app.components.python import TracerPythonScript
from lightning.app.structures import List
import gunicorn
from lightning_serve.strategies import _STRATEGY_REGISTRY
from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import _configure_session, get_url


class ServeWork(TracerPythonScript):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, parallel=True, **kwargs)

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(serve_work=self, **kwargs)

    def alive(self):
        return self.url != ""


class ServeWork(LightningWork):
    def __init__(self, *args, script_path: str, workers=None, **kwargs):
        super().__init__(
            *args,
            parallel=True,
            raise_exception=True,
            **kwargs,
        )
        self.script_path = script_path
        self.workers = workers or int(multiprocessing.cpu_count() / 2)
        self._process = None

    def run(self, random_kwargs="", **kwargs):
        self._process = subprocess.run(
            f"{sys.executable} -m gunicorn --workers {self.workers} -k uvicorn.workers.UvicornWorker serve:app -b {self.host}:{self.port}",
            check=True,
            shell=True,
            env={"random_kwargs": random_kwargs},
        )

    def alive(self):
        return self.url != ""


class Proxy(LightningWork):
    def __init__(self, *args, workers=None, **kwargs):
        super().__init__(
            *args,
            parallel=True,
            raise_exception=True,
            **kwargs,
        )
        self.workers = workers or int(multiprocessing.cpu_count() / 2)

    def run(self, strategy=None, **kwargs):
        os.chdir(os.path.dirname(__file__))
        with open("strategy.p", "wb") as f:
            pickle.dump(strategy, f)

        # subprocess.run(
        #     f"{sys.executable} -m uvicorn --workers {self.workers} proxy:app --host {self.host} --port {self.port}",
        #     check=True,
        #     shell=True,
        # )

        subprocess.run(
            f"{sys.executable} -m gunicorn --workers {self.workers} -k uvicorn.workers.UvicornWorker proxy:app -b {self.host}:{self.port}",
            check=True,
            shell=True,
        )

    def alive(self):
        return self.url != ""


# class Proxy(TracerPythonScript):
#     def __init__(self, *args, **kwargs):
#         super().__init__(
#             *args,
#             parallel=True,
#             script_path=os.path.join(os.path.dirname(__file__), "proxy.py"),
#             raise_exception=True,
#             **kwargs,
#         )
#         self.routing = None
#         self.workers = 1

#     def run(self, strategy=None, **kwargs):
#         os.chdir(os.path.dirname(__file__))
#         with open("strategy.p", "wb") as f:
#             pickle.dump(strategy, f)
#         self.script_args += [f"--host={self.host}", f"--port={self.port}"]
#         print(self.script_args)
#         super().run(proxy=self, **kwargs)

#     def alive(self):
#         return self.url != ""


class PrometheusWork(LightningWork):
    def __init__(self):
        super().__init__(
            cloud_build_config=BuildConfig(
                image="gcr.io/grid-backend-266721/prom/prometheus-serve:v0.0.1"
            ),
            port=9090,
        )

    def run(self):
        raise Exception("HERE")


class GrafanaWork(LightningWork):
    def __init__(self):
        super().__init__(
            cloud_build_config=BuildConfig(
                image="gcr.io/grid-backend-266721/grafana-serve:v0.0.1"
            ),
            port=3000,
        )

    def run(self):
        subprocess.run(
            [
                "/bin/bash",
                "./grafana.sh",
            ],
            check=True,
            env={
                "GF_SECURITY_ADMIN_PASSWORD": "admin",
                "GF_USERS_ALLOW_SIGN_UP": "false",
                "GF_SECURITY_ALLOW_EMBEDDING": "true",
            },
        )


class Locust(LightningWork):
    def __init__(self, num_users: int):
        super().__init__(port=8089, parallel=True)
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
        self._strategy_run_after = 5
        self._last_update_time = time()
        self.locust = Locust(100)
        self._previous_hash = None
        self._has_run_after = False
        # self.grafana = GrafanaWork()
        # self.prometheus = PrometheusWork()

    def run(self, **kwargs):
        # # Step 1: Start the proxy
        if not self.proxy.has_started:
            self.proxy.run(strategy=self._strategy)

        # Step 2: Compute a hash of the keyword arguments.
        call_hash = DeepHash(kwargs)[kwargs]
        if call_hash not in self.hashes:
            serve_work = self._work_cls(**(self._work_kwargs or {}))
            self.hashes.append(call_hash)
            self.serve_works.append(serve_work)
            serve_work.run(**kwargs)

        if self.proxy.url != "":
            res = self._strategy.run(self.serve_works)
            res_hash = DeepHash(res)[res]
            new_update_time = time()
            if res_hash == self._previous_hash:
                if self._has_run_after:
                    return
                if (new_update_time - self._last_update_time) > self._strategy_run_after:
                    self._strategy.on_after_run(self.serve_works, res)
                    self._has_run_after = True
            elif (new_update_time - self._last_update_time) > self._router_refresh:
                # Send a burst of requests to update with the new information.
                for _ in range(self.proxy.workers * 50):
                    _configure_session().post(self.proxy.url + "/api/v1/proxy", json=res)
                self._last_update_time = new_update_time
                self._previous_hash = res_hash
                self._has_run_after = False

        if self.proxy.alive():
            self.locust.run(self.proxy.url)

    def configure_layout(self):
        proxy_url = self.proxy.url + "/predict" if self._previous_hash else ""
        return [
            {"name": "Serve", "content": proxy_url},
            {"name": "API Testing", "content": self.locust},
        ]