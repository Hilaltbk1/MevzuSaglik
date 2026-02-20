from typing import List

from pydantic import BaseModel

#request - giriş
class QueryRequest(BaseModel):
    query:str
    user_name:str

#response - çıkış
class QueryResponse(BaseModel):
    query:str
    answer : str
    sources : List[str]
    status:str

