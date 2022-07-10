from datetime import datetime, timedelta

from lightning import LightningApp, LightningFlow

from lightning_serve import ServeFlow


class RootFlow(LightningFlow):
    def __init__(self):
        super().__init__()

        self.serve = ServeFlow(
            strategy="blue_green_v2",
            script_path="./scripts/serve.py",
        )
        self._current_deploy_date = None
        self._next_deploy_date = None

    def run(self):
        now = datetime.now()
        if self._next_deploy_date is None or now > self._next_deploy_date:
            self._current_deploy_date = now
            self._next_deploy_date = now + timedelta(seconds=30)

        self.serve.run(
            random_kwargs=self._current_deploy_date.strftime("%m/%d/%Y %H:%M:%S")
        )

    def configure_layout(self):
        return self.serve.configure_layout()


app = LightningApp(RootFlow(), debug=True)
