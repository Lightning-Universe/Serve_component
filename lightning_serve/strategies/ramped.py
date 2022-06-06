from lightning import LightningWork
from lightning_serve.strategies.base import Strategy
from lightning.structures import List
from time import time


class RampedStrategy(Strategy):

    def __init__(self, transition_time_in_seconds: float = 120.):
        super().__init__()
        self.transition_time_in_seconds = transition_time_in_seconds
        self.serve_works_ramped_time = {}
        self.ramped_scores = {}

    def run(self, serve_works: List["LightningWork"]):
        # Step 1: Get ready time for each work.
        if len(serve_works) == 1:
            return {serve_works[-1].url: 1.0}

        # Step 2: Compute the current ramped score to transfer requests load.
        current_time = time()
        total_ramped_score = .0
        running_serve_works = [w for w in serve_works[:-1] if (w.url in self.ramped_scores and self.ramped_scores[w.url]) > 0 or w.url not in self.ramped_scores]
        for w in running_serve_works:
            if w.url not in self.serve_works_ramped_time:
                self.serve_works_ramped_time[w.url] = current_time
                self.ramped_scores[w.url] = 1.0

            time_left = current_time - self.serve_works_ramped_time[w.url]
            if time_left < self.transition_time_in_seconds:
                ramped_score = (self.transition_time_in_seconds - time_left) / (self.transition_time_in_seconds * len(running_serve_works))
                self.ramped_scores[w.url]  = ramped_score
                total_ramped_score += ramped_score

            else:
                self.ramped_scores[w.url] = 0

        self.ramped_scores[serve_works[-1].url] = 1.0 - total_ramped_score
        return {k: v for k, v in self.ramped_scores.items() if v > 0}
