from lightning import LightningWork
from lightning.app.structures import List

from lightning_serve.strategies.base import Strategy


def get_url(work):
    ip_address = work.ip_address
    return f"http://{ip_address}:{work.port}"


class BlueGreenStrategy(Strategy):
    def run(self, serve_works: List[LightningWork]):
        if len(serve_works) == 1:
            return {get_url(serve_works[-1]): 1.0}

        if serve_works[-1].alive():
            for serve_work in serve_works[:-1]:
                serve_work.stop()
            return {get_url(serve_works[-1]): 1.0}
        else:
            return {get_url(serve_works[-2]): 1.0}
