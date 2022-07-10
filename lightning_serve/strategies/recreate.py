from lightning import LightningWork
from lightning.app.structures import List

from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import get_url


class RecreateStrategy(Strategy):
    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) < 2:
            return {get_url(w): 1.0 for w in serve_works}

        latest_serve_work = serve_works[-1]
        # Stop before the new service is up and running.
        for serve_work in serve_works[:-1]:
            serve_work.stop()

        if get_url(latest_serve_work) != "":
            return {get_url(latest_serve_work): 1.0}
        else:
            return {}
