from typing import Annotated
from sqlmodel import Field, SQLModel  # type: ignore

from common.model import WasteType


class ContainerOrm(SQLModel, table=True):
    type: Annotated[WasteType, Field(default=..., primary_key=True)]
    current: int = Field(default=0, ge=0)
    max: int = Field(default=..., ge=0)
