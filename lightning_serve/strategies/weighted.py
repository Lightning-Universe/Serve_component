from lightning import LightningWork
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from lightning.utilities.enum import WorkStageStatus


class WeightedStrategy(Strategy):

    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) < 2:
            return {w.url: 1.0 for w in serve_works}

        works = [w for w in serve_works if w.url != '']
        return {w.url: 1.0 / len(works) for w in works}