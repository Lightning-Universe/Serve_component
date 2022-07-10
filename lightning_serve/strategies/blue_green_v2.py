from lightning import LightningWork
from lightning.app.structures import List

from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import get_url


class BlueGreenStrategyV2(Strategy):
    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) == 1:
            return [{100: [get_url(serve_works[-1])]}]

        if serve_works[-1].alive():
            return [{100: [get_url(serve_works[-1])]}]
        return [{100: [get_url(serve_works[-2])]}]

    def on_after_run(self, serve_works: List[LightningWork], res):
        for serve_work in serve_works[:-1]:
            serve_work.stop()
            print(f"Killing the server {serve_work.name}")
