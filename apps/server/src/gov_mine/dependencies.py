"""FastAPI dependencies that read the resources the lifespan put on `request.state`."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from gov_mine.config import Settings
from gov_mine.integrations.storage import ObjectStore
from gov_mine.resources import Resources


def get_resources(request: Request) -> Resources:
    resources: Resources = request.state.resources
    return resources


ResourcesDep = Annotated[Resources, Depends(get_resources)]


def get_settings(resources: ResourcesDep) -> Settings:
    return resources.settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_session(resources: ResourcesDep) -> AsyncIterator[AsyncSession]:
    """One session per request; handlers commit explicitly."""
    async with resources.session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_object_store(resources: ResourcesDep) -> ObjectStore:
    return resources.object_store


ObjectStoreDep = Annotated[ObjectStore, Depends(get_object_store)]
