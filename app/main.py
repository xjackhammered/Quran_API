from fastapi import FastAPI
from app import models 
from app.database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Quran API")

@app.get("/")
def root():
    return {"message":"FastAPI is running"}