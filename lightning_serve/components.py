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

from lightning_serve.strategies import _STRATEGY_REGISTRY
from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import _configure_session


class ServeWork(TracerPythonScript):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, parallel=True, **kwargs)

    def run(self, **kwargs):
        self.script_args += [f"--host={self.host}", f"--port={self.port}"]
        super().run(serve_work=self, **kwargs)

    def alive(self):
        return self.url != ""


class ServeWork(LightningWork):
    def __init__(self, *args, script_path: str, workers=6, **kwargs):
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
    def __init__(self, *args, workers=4, **kwargs):
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


class GinProxyBuildConfig(BuildConfig):
    def build_commands(self):
        return [
            "wget -c https://golang.org/dl/go1.18.1.linux-amd64.tar.gz",
            "sudo tar -C /usr/local -xvzf go1.18.1.linux-amd64.tar.gz",
        ]


class GinProxy(LightningWork):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            parallel=True,
            raise_exception=True,
            **kwargs,
            cloud_build_config=GinProxyBuildConfig(),
        )
        self.workers = 1

    def run(self, strategy=None, **kwargs):
        subprocess.run(
            f"PATH=$PATH:/usr/local/go/bin go get .",
            check=True,
            shell=True,
            cwd=os.path.join(os.path.dirname(__file__), "reverse_proxy"),
        )

        subprocess.run(
            f"PATH=$PATH:/usr/local/go/bin go run main.go --host {self.host} --port {self.port}",
            check=True,
            shell=True,
            cwd=os.path.join(os.path.dirname(__file__), "reverse_proxy"),
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
                "./run.sh",
            ],
            check=True,
            env={
                "GF_SECURITY_ADMIN_PASSWORD": "admin",
                "GF_USERS_ALLOW_SIGN_UP": "false",
                "GF_SECURITY_ALLOW_EMBEDDING": "true",
            },
        )


class ApacheHTTPServerBenchmarkingBuildConfig(BuildConfig):
    def build_commands(self):
        return ["sudo apt-get install -y apache2-utils"]


class ApacheHTTPServerBenchmarking(LightningWork):
    def __init__(self):
        super().__init__(
            cloud_build_config=ApacheHTTPServerBenchmarkingBuildConfig(), parallel=True
        )

    def run(self, host: str):
        cmd = f'ab -n 10000 -c 1 -p payload.json -T "application/json" {host}/predict'
        subprocess.Popen(cmd, shell=True).wait()


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
        self.proxy = GinProxy() if strategy == "blue_green_v2" else Proxy()
        self._warmup_steps_limit = 0 if strategy == "blue_green_v2" else 20
        self._multiplier = 1 if strategy == "blue_green_v2" else self.proxy.workers * 20
        self.performance_tester = ApacheHTTPServerBenchmarking() if strategy == "blue_green_v2" else Locust(100)
        self._strategy = (
            strategy
            if isinstance(strategy, Strategy)
            else _STRATEGY_REGISTRY[strategy]()
        )
        self.ws = List()
        self.hashes = []
        self._router_refresh = router_refresh
        self._strategy_run_after = 10
        self._last_update_time = time()
        self._previous_hash = None
        self._has_run_after = False
        self._warmup_steps = 0

    def run(self, **kwargs):
        # # Step 1: Start the proxy
        if not self.proxy.has_started:
            self.proxy.run(strategy=self._strategy)

        # Step 2: Compute a hash of the keyword arguments.
        call_hash = DeepHash(kwargs)[kwargs]
        if call_hash not in self.hashes:
            serve_work = self._work_cls(**(self._work_kwargs or {}))
            self.hashes.append(call_hash)
            self.ws.append(serve_work)
            serve_work.run(**kwargs)

        if self.proxy.url != "":
            res = self._strategy.run(self.ws)
            new_update_time = time()
            if self._warmup_steps <= self._warmup_steps_limit:
                if (new_update_time - self._last_update_time) > self._router_refresh:
                    print(f"[WARMUP] Refresh proxy: {len(self.ws)} server(s).")
                    # Send a burst of requests to update with the new information.
                    for _ in range(self._multiplier):
                        _configure_session().post(
                            self.proxy.url + "/api/v1/proxy", json=res
                        )
                    self._last_update_time = new_update_time
                    self._warmup_steps += 1
            else:
                res_hash = DeepHash(res)[res]
                if res_hash == self._previous_hash:
                    if self._has_run_after:
                        return
                    if (
                        self.ws[-1].alive()
                        and (new_update_time - self._last_update_time)
                        > self._strategy_run_after
                    ):
                        self._strategy.on_after_run(self.ws, res)
                        self._has_run_after = True
                else:
                    # Send a burst of requests to update with the new information.
                    print(f"Refresh proxy: {len(self.ws)} server(s).")
                    for _ in range(self._multiplier):
                        _configure_session().post(
                            self.proxy.url + "/api/v1/proxy", json=res
                        )
                    self._last_update_time = new_update_time
                    self._previous_hash = res_hash
                    self._has_run_after = False

        if self.proxy.alive():
            self.performance_tester.run(self.proxy.url)

    def configure_layout(self):
        proxy_url = (
            self.proxy.url + "/predict"
            if self._warmup_steps >= self._warmup_steps_limit
            else ""
        )
        return [
            {"name": "Serve", "content": proxy_url},
            {"name": "API Testing", "content": self.performance_tester},
        ]
