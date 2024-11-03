from enum import Enum
from typing import Any, Generic, Literal, Self, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: int
    y: int


class CollectorInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    position: Position
    url: str


class Container(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    current: int = Field(default=0, ge=0)
    max: int = Field(frozen=True, ge=0)

    @model_validator(mode="after")
    def current_not_overflows_max(self) -> Self:
        if self.current > self.max:
            raise ValueError(f"must not overflow maximum that is {self.max}")
        return self


class WasteType(str, Enum):
    glass = "glass"
    plastic = "plastic"
    bio = "bio"


T = TypeVar("T")


class WasteTypeMapping(BaseModel, Generic[T]):  # handtype: WasteType
    glass: T | None = Field(default=None)
    plastic: T | None = Field(default=None)
    bio: T | None = Field(default=None)

    def get(self, key: WasteType) -> T | None:
        match key:
            case WasteType.glass:
                return self.glass
            case WasteType.plastic:
                return self.plastic
            case WasteType.bio:
                return self.bio

    def set(self, key: WasteType, value: T | None):
        match key:
            case WasteType.glass:
                self.glass = value
            case WasteType.plastic:
                self.plastic = value
            case WasteType.bio:
                self.bio = value

    def is_all_none(self) -> bool:  # handtype: WasteType
        return (self.glass is None) and (self.plastic is None) and (self.bio is None)


type UnsupportedWasteTypeLiteral = Literal[
    "There is no container for this type of waste"
]
UnsupportedWasteType: UnsupportedWasteTypeLiteral = (
    "There is no container for this type of waste"
)


class HTTPExceptionModel(BaseModel):
    detail: Any = None
