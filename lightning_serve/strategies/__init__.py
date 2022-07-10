from functools import partial

from lightning_serve.strategies.ab_testing import ABTestingStrategy
from lightning_serve.strategies.blue_green import BlueGreenStrategy
from lightning_serve.strategies.blue_green_v2 import BlueGreenStrategyV2
from lightning_serve.strategies.ramped import RampedStrategy
from lightning_serve.strategies.recreate import RecreateStrategy
from lightning_serve.strategies.shadow import ShadowStrategy

_STRATEGY_REGISTRY = {
    "blue_green": BlueGreenStrategy,
    "blue_green_v2": BlueGreenStrategyV2,
    "ab_testing": ABTestingStrategy,
    "recreate": RecreateStrategy,
    "ramped": RampedStrategy,
    "shadow": ShadowStrategy,
    "weighted": partial(ABTestingStrategy, method="weighted"),
}

__all__ = [
    "ABTestingStrategy",
    "BlueGreenStrategy",
    "RampedStrategy",
    "RecreateStrategy",
    "ShadowStrategy",
]
