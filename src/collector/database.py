from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session
from collector.settings import settings

engine = create_engine(settings.db_uri)


async def init_db():
    from collector.model import ContainerOrm as _
    SQLModel.metadata.create_all(bind=engine)


async def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
