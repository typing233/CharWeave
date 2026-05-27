import httpx

BASE_URL = "https://openlibrary.org"
ARCHIVE_URL = "https://archive.org"
HEADERS = {"User-Agent": "CharWeave/1.0 (book character analysis tool)"}


async def search_books(query: str, search_type: str = "title") -> list[dict]:
    params = {"q": query, "limit": 10, "fields": "key,title,author_name,first_publish_year,edition_key,ia"}
    if search_type == "author":
        params = {"author": query, "limit": 10, "fields": "key,title,author_name,first_publish_year,edition_key,ia"}

    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        resp = await client.get(f"{BASE_URL}/search.json", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for doc in data.get("docs", []):
        ia_ids = doc.get("ia", [])
        results.append({
            "key": doc.get("key", ""),
            "title": doc.get("title", ""),
            "authors": doc.get("author_name", []),
            "year": doc.get("first_publish_year"),
            "ia_id": ia_ids[0] if ia_ids else None,
        })
    return results


async def fetch_book_text(ia_id: str) -> str | None:
    url = f"{ARCHIVE_URL}/stream/{ia_id}/{ia_id}_djvu.txt"
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=HEADERS) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            text = resp.text
            # Strip HTML wrapper if present
            if "<body" in text[:5000]:
                import re
                match = re.search(r"<pre[^>]*>(.*)</pre>", text, re.DOTALL)
                if match:
                    text = match.group(1)
            return text
    return None
