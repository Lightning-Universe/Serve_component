from lightning import LightningFlow, LightningApp
from lightning_serve import ServeFlow, ServeWork
from lightning_serve.strategies import WeightedStrategy

class RootFlow(LightningFlow):

    def __init__(self):
        super().__init__()

        self.serve = ServeFlow(
            ServeWork,
            strategy=WeightedStrategy(),
            work_kwargs=dict(script_path="./scripts/serve.py", raise_exception=True)
        )
        self.counter = 1

    def run(self):
        self.serve.run(counter=self.counter)
        if self.counter < 2:
            self.counter += 1

    def configure_layout(self):
        return {"name": "Serve", "content": self.serve.base_url + "/predict"}

app = LightningApp(RootFlow(), debug=True)