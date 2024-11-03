import math
from common.model import CollectorInfo
from producer.settings import settings


def distance_to_collector(collector: CollectorInfo) -> float:
    return math.sqrt(
        (settings.position_x - collector.position.x) ** 2
        + (settings.position_y - collector.position.y) ** 2
    )
