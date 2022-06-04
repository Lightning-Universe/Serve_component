from lightning_serve.strategies.blue_green import BlueGreenStrategy
from lightning_serve.strategies.ab_testing import ABTestingStrategy
from lightning_serve.strategies.recreate import RecreateStrategy

_STRATEGY_REGISTRY = {
    "blue_green": BlueGreenStrategy,
    "ab_testing": ABTestingStrategy,
    "recreate": RecreateStrategy
}

__all__ = ["ABTestingStrategy", "BlueGreenStrategy", "RecreateStrategy"]

