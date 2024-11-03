import traceback
from typing import Annotated, Literal, Mapping

from fastapi import Depends, HTTPException, logger, status
from pydantic import PositiveInt
from sqlalchemy import delete
from sqlmodel import select
from collector.database import SessionDep
from collector.model import ContainerOrm
from collector.util import container_orms_to_mapping, mapping_to_container_orms
from common.model import Container, UnsupportedWasteType, UnsupportedWasteTypeLiteral, WasteType, WasteTypeMapping


class ContainersService:
    def __init__(self, session: SessionDep) -> None:
        self.session = session

    async def info(self) -> Mapping[WasteType, Container]:
        containers = self.session.exec(select(ContainerOrm)).all()
        return {c.type: Container(current=c.current, max=c.max) for c in containers}

    async def set(self, containers: WasteTypeMapping[Container]):
        try:
            self.session.connection().execute(delete(ContainerOrm))
            new_containers = mapping_to_container_orms(containers)
            self.session.add_all(new_containers)
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def clear(self):
        try:
            containers = self.session.exec(select(ContainerOrm)).all()
            for container in containers:
                container.current = 0
            self.session.add_all(containers)
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def put(
        self, wastes: WasteTypeMapping[PositiveInt]
    ) -> Literal[True] | WasteTypeMapping[PositiveInt | UnsupportedWasteTypeLiteral]:
        container_orms = self.session.exec(select(ContainerOrm)).all()
        containers = container_orms_to_mapping(container_orms)

        errors: WasteTypeMapping[PositiveInt | UnsupportedWasteTypeLiteral] = (
            WasteTypeMapping()
        )
        for type in list(WasteType):
            waste = wastes.get(type)
            if waste is None:
                continue
            container = containers.get(type)
            if container is None:
                errors.set(type, UnsupportedWasteType)
                continue
            remainder = container.max - container.current
            if remainder < waste:
                errors.set(type, waste - remainder)

        if not errors.is_all_none():
            return errors

        try:
            for container in container_orms:
                waste = wastes.get(container.type)
                if waste is None:
                    continue
                container.current += waste
            self.session.add_all(container_orms)
            self.session.commit()
        except Exception:
            self.session.rollback()
            logger.logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return True


ContainersServiceDep = Annotated[ContainersService, Depends()]
