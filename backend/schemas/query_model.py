from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query:str
    user_name:str
    session_uuid: str


class QueryResponse(BaseModel):
    query:str
    answer : str
    sources : List[str]
    status: Optional[str] = None
    session_uuid:str

