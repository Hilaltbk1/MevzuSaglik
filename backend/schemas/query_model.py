from typing import List, Optional

from pydantic import BaseModel

#request - giriş
class QueryRequest(BaseModel):
    query:str
    user_name:str
    session_uuid: str

#response - çıkış
class QueryResponse(BaseModel):
    query:str
    answer : str
    sources : List[str]
    status: Optional[str] = None
    session_uuid:str

