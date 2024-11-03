from typing import Sequence

from collector.model import ContainerOrm
from common.model import Container, WasteType, WasteTypeMapping


def container_orms_to_mapping(
    containers: Sequence[ContainerOrm],
) -> WasteTypeMapping[Container]:
    answer: WasteTypeMapping[Container] = WasteTypeMapping()
    for container in containers:
        answer.set(
            container.type, Container(current=container.current, max=container.max)
        )
    return answer


def mapping_to_container_orms(
    containers: WasteTypeMapping[Container],
) -> Sequence[ContainerOrm]:
    result: Sequence[ContainerOrm] = []
    for type in list(WasteType):
        container = containers.get(type)
        if container is not None:
            result.append(
                ContainerOrm(type=type, current=container.current, max=container.max)
            )
    return result
