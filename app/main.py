from fastapi import FastAPI
from .database import Base, engine
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def default_route():
    return {"message": "Hello, World!"}