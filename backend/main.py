from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openlibrary import search_books, fetch_book_text
from nlp_pipeline import extract_characters, build_relationships, generate_mermaid

app = FastAPI(title="CharWeave API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    search_type: str = "title"


class AnalyzeRequest(BaseModel):
    ia_id: str
    title: str = ""


class AnalyzeResponse(BaseModel):
    title: str
    characters: list[str]
    relationships: list[dict]
    mermaid: str


@app.post("/api/search")
async def search(req: SearchRequest):
    results = await search_books(req.query, req.search_type)
    return {"results": results}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    text = await fetch_book_text(req.ia_id)
    if not text:
        raise HTTPException(status_code=404, detail="无法获取书籍全文，该书可能不是公版书或不支持文本格式。")

    characters = extract_characters(text)
    if not characters:
        raise HTTPException(status_code=422, detail="未能从文本中提取到人物实体。")

    relationships = build_relationships(text, characters)
    mermaid = generate_mermaid(characters, relationships)

    return AnalyzeResponse(
        title=req.title,
        characters=characters,
        relationships=relationships,
        mermaid=mermaid,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}
