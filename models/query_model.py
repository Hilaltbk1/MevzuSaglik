from pydantic import BaseModel

#request - giriş
class QueryRequest(BaseModel):
    query:str
    user_name:str

#response - çıkış
class QueryResponse(BaseModel):
    query:str
    answer : str
    status:str

