from lightning_serve.strategies.blue_green import BlueGreenStrategy
from lightning_serve.strategies.ab_testing import ABTestingStrategy
from lightning_serve.strategies.recreate import RecreateStrategy
from lightning_serve.strategies.ramped import RampedStrategy

_STRATEGY_REGISTRY = {
    "blue_green": BlueGreenStrategy,
    "ab_testing": ABTestingStrategy,
    "recreate": RecreateStrategy,
    "ramped": RampedStrategy,
}

__all__ = ["ABTestingStrategy", "BlueGreenStrategy", "RampedStrategy", "RecreateStrategy"]

