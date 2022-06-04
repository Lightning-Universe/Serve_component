from lightning import LightningWork
from lightning.structures import List
from lightning_serve.strategies.base import Strategy
from lightning.utilities.enum import WorkStageStatus


class RolloutStrategy(Strategy):

    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) < 2:
            return {w.url: 1.0 for w in serve_works}

        latest_serve_work = serve_works[-1]
        if latest_serve_work.url != "":
            for serve_work in serve_works[:-1]:
                serve_work.stop()

        return {w.url: 1.0 for w in serve_works if w.status.stage != WorkStageStatus.FAILED}