from fastapi import FastAPI
from routers import search, history

app = FastAPI(title="MevzuSaglik")

#routers dahil etme
app.include_router(search.router)
app.include_router(history.router)

@app.get("/")
def home():
    return {"Hello": "World"}