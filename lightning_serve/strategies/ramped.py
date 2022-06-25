from time import time

from lightning.app.structures import List

from lightning_serve.strategies.base import Strategy
from lightning_serve.utils import get_url


class RampedStrategy(Strategy):
    def __init__(self, transition_time_in_seconds: float = 120.0):
        super().__init__()
        self.transition_time_in_seconds = transition_time_in_seconds
        self.serve_works_ramped_time = {}
        self.ramped_scores = {}

    def run(self, serve_works: List["LightningWork"]):
        # Step 1: Get ready time for each work.
        if len(serve_works) == 1:
            return {get_url(serve_works[-1]): 1.0}

        # Step 2: Compute the current ramped score to transfer requests load.
        current_time = time()
        total_ramped_score = 0.0
        running_serve_works = [
            w
            for w in serve_works[:-1]
            if (get_url(w) in self.ramped_scores and self.ramped_scores[get_url(w)]) > 0
            or get_url(w) not in self.ramped_scores
        ]
        for w in running_serve_works:
            if get_url(w) not in self.serve_works_ramped_time:
                self.serve_works_ramped_time[get_url(w)] = current_time
                self.ramped_scores[get_url(w)] = 1.0

            time_left = current_time - self.serve_works_ramped_time[get_url(w)]
            if time_left < self.transition_time_in_seconds:
                ramped_score = (self.transition_time_in_seconds - time_left) / (
                    self.transition_time_in_seconds * len(running_serve_works)
                )
                self.ramped_scores[get_url(w)] = ramped_score
                total_ramped_score += ramped_score

            else:
                self.ramped_scores[get_url(w)] = 0

        self.ramped_scores[get_url(serve_works[-1])] = 1.0 - total_ramped_score
        return {k: v for k, v in self.ramped_scores.items() if v > 0}
