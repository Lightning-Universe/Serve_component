from lightning import LightningWork
from lightning.app.structures import List
from lightning_serve.strategies.base import Strategy


class BlueGreenStrategy(Strategy):
    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) == 1:
            return {serve_works[-1].url: 1.0}

        if serve_works[-1].alive():
            for serve_work in serve_works[:-1]:
                serve_work.stop()
            return {serve_works[-1].url: 1.0}
        else:
            return {serve_works[-2].url: 1.0}
