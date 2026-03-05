from fastapi import FastAPI
from database.db import init_db

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "Adaptive Gamified Quiz System running"}