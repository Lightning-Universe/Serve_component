from lightning import LightningWork
from lightning.app.structures import List

from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import get_url


class BlueGreenStrategy(Strategy):
    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) == 1:
            return {get_url(serve_works[-1]): 1.0}

        if serve_works[-1].alive():
            return {get_url(serve_works[-1]): 1.0}
        return {get_url(serve_works[-2]): 1.0}

    def on_after_run(self, serve_works: List[LightningWork], res):
        for serve_work in serve_works[:-1]:
            serve_work.stop()
            print(f"Killing the server {serve_work.name}")
