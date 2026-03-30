from fastapi import FastAPI
from pydantic import BaseModel
from tavily_pool import TavilyPool
import os

app = FastAPI()

API_KEYS = os.getenv("TAVILY_KEYS").split(",")

pool = TavilyPool(API_KEYS)

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
def search(req: SearchRequest):
    result = pool.search(
        query=req.query,
        search_depth="advanced",
        max_results=5
    )
    return result