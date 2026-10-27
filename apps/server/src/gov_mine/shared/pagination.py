"""One page of a list, as every list route serves it: the rows asked for, how many there are in
all, and the window they came from. The dashboard's tables page through `total`."""

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

# What a list route takes, and the largest page it serves.
Limit = Annotated[int, Query(ge=1, le=500)]
Offset = Annotated[int, Query(ge=0)]


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
