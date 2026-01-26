from fastapi import FastAPI
from routers import search

app = FastAPI(title="MevzuSaglik")

#routers dahil etme
app.include_router(search.router)

@app.get("/")
def home():
    return {"Hello": "World"}