import json
import subprocess

from lightning import LightningWork
from lightning.app.storage import Path


class MLServer(LightningWork):
    def __init__(self, name: str, implementation: str, workers: int = 1, **kwargs):
        super().__init__(parallel=True, **kwargs)
        self.settings = {
            "debug": True,
            "parallel_workers": workers,
        }
        self.model_settings = {
            "name": name,
            "implementation": implementation,
        }
        self.version = 1

    def run(self, model_path: Path):
        self.settings.update({"host": self.host, "http_port": self.port})

        with open("settings.json", "w") as f:
            json.dump(self.settings, f)

        self.model_settings["parameters"] = {
            "version": f"v0.0.{self.version}",
            "uri": str(model_path.absolute()),
        }
        with open("model-settings.json", "w") as f:
            json.dump(self.model_settings, f)

        subprocess.Popen("mlserver start .", shell=True).wait()

    def alive(self):
        return self.url != ""
