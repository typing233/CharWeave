import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openlibrary import search_books, fetch_book_text
from nlp_pipeline import extract_characters, build_relationships, generate_mermaid
from cache import AnalysisCache
from text_processing import split_into_chapters


analysis_cache = AnalysisCache()
_jobs: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load transformer model in background to avoid first-request delay
    asyncio.get_event_loop().run_in_executor(None, _preload_model)
    yield


def _preload_model():
    from relation_extractor import get_extractor
    get_extractor()


app = FastAPI(title="CharWeave API", lifespan=lifespan)

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


class CharacterItem(BaseModel):
    name: str
    mentions: int


class RelationshipItem(BaseModel):
    source: str
    target: str
    weight: int
    type: str
    confidence: float
    direction: str
    passages: list[str] = []


class AnalyzeResponse(BaseModel):
    title: str
    characters: list[CharacterItem]
    relationships: list[RelationshipItem]
    mermaid: str


@app.post("/api/search")
async def search(req: SearchRequest):
    results = await search_books(req.query, req.search_type)
    clean = []
    for r in results:
        clean.append({
            "key": r["key"],
            "title": r["title"],
            "authors": r["authors"],
            "year": r["year"],
            "ia_id": r["ia_id"],
            "has_text": r["has_text"],
        })
    return {"results": clean}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    cached = analysis_cache.get(req.ia_id)
    if cached:
        return AnalyzeResponse(**cached)

    text = await fetch_book_text(req.ia_id)
    if not text:
        raise HTTPException(status_code=404, detail="无法获取书籍全文，该书可能不是公版书或不支持文本格式。")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_analysis_sync, text, req.title)
    analysis_cache.set(req.ia_id, result)
    return AnalyzeResponse(**result)


@app.post("/api/analyze/start")
async def start_analysis(req: AnalyzeRequest):
    cached = analysis_cache.get(req.ia_id)
    if cached:
        job_id = str(uuid.uuid4())
        _jobs[job_id] = {"status": "complete", "progress": 100, "stage": "完成", "result": cached}
        return {"job_id": job_id}

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running", "progress": 0, "stage": "初始化...", "result": None}
    asyncio.create_task(_run_analysis_async(job_id, req.ia_id, req.title))
    return {"job_id": job_id}


@app.get("/api/analyze/progress/{job_id}")
async def get_progress(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def _run_analysis_async(job_id: str, ia_id: str, title: str):
    try:
        _jobs[job_id]["stage"] = "正在下载书籍文本..."
        _jobs[job_id]["progress"] = 5

        text = await fetch_book_text(ia_id)
        if not text:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["stage"] = "无法获取书籍全文"
            return

        _jobs[job_id]["progress"] = 15
        _jobs[job_id]["stage"] = "正在提取人物实体..."

        loop = asyncio.get_event_loop()

        def progress_cb(pct):
            _jobs[job_id]["progress"] = pct
            _jobs[job_id]["stage"] = "正在分析人物关系..."

        result = await loop.run_in_executor(
            None, _run_analysis_with_progress, text, title, progress_cb
        )

        analysis_cache.set(ia_id, result)
        _jobs[job_id]["status"] = "complete"
        _jobs[job_id]["progress"] = 100
        _jobs[job_id]["stage"] = "完成"
        _jobs[job_id]["result"] = result

    except Exception as e:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["stage"] = f"分析失败: {str(e)}"


def _run_analysis_with_progress(text: str, title: str, progress_callback) -> dict:
    progress_callback(20)
    characters, alias_map = extract_characters(text)
    if not characters:
        raise ValueError("未能从文本中提取到人物实体。")

    progress_callback(40)
    chapters = split_into_chapters(text)
    full_text = text if len(chapters) < 3 else "\n\n".join(chapters)

    progress_callback(50)
    relationships = build_relationships(
        full_text, characters, alias_map, progress_callback=progress_callback
    )
    mermaid = generate_mermaid(characters, relationships)

    return {
        "title": title,
        "characters": [{"name": c["name"], "mentions": c["mentions"]} for c in characters],
        "relationships": relationships,
        "mermaid": mermaid,
    }


def _run_analysis_sync(text: str, title: str) -> dict:
    characters, alias_map = extract_characters(text)
    if not characters:
        raise ValueError("未能从文本中提取到人物实体。")

    chapters = split_into_chapters(text)
    full_text = text if len(chapters) < 3 else "\n\n".join(chapters)

    relationships = build_relationships(full_text, characters, alias_map)
    mermaid = generate_mermaid(characters, relationships)

    return {
        "title": title,
        "characters": [{"name": c["name"], "mentions": c["mentions"]} for c in characters],
        "relationships": relationships,
        "mermaid": mermaid,
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}
