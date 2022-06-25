from datetime import datetime

from lightning import LightningApp, LightningFlow

from lightning_serve import ServeFlow


class RootFlow(LightningFlow):
    def __init__(self):
        super().__init__()

        self.serve = ServeFlow(
            strategy="shadow",
            script_path="./scripts/serve.py",
        )

    def run(self):
        # Deploy a new server every time the provided input changes
        # and shutdown the previous server once the new one is ready.
        self.serve.run(random_kwargs=datetime.now().strftime("%m/%d/%Y, %H:%M"))

    def configure_layout(self):
        return [
            {"name": "Serve", "content": self.serve.proxy.url + "/predict"},
            {"name": "API Testing", "content": self.serve.locust},
        ]


app = LightningApp(RootFlow(), debug=True)
