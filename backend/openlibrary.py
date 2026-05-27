import re
import httpx

BASE_URL = "https://openlibrary.org"
ARCHIVE_URL = "https://archive.org"
HEADERS = {"User-Agent": "CharWeave/1.0 (book character analysis tool)"}

TEXT_FILE_EXTENSIONS = ["_djvu.txt", ".txt", "_text.pdf"]


async def search_books(query: str, search_type: str = "title") -> list[dict]:
    params = {"q": query, "limit": 20, "fields": "key,title,author_name,first_publish_year,edition_key,ia"}
    if search_type == "author":
        params = {"author": query, "limit": 20, "fields": "key,title,author_name,first_publish_year,edition_key,ia"}

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
            "ia_ids": ia_ids,
            "ia_id": ia_ids[0] if ia_ids else None,
            "has_text": False,
        })

    results = await _check_text_availability(results)
    results.sort(key=lambda x: (not x["has_text"], 0 if x["ia_id"] else 1))
    return results[:10]


async def _check_text_availability(results: list[dict]) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
        for result in results:
            if not result["ia_ids"]:
                continue
            for ia_id in result["ia_ids"][:3]:
                files_url = f"{ARCHIVE_URL}/metadata/{ia_id}/files"
                try:
                    resp = await client.get(files_url)
                    if resp.status_code != 200:
                        continue
                    files = resp.json().get("result", [])
                    txt_file = _find_text_file(files, ia_id)
                    if txt_file:
                        result["has_text"] = True
                        result["ia_id"] = ia_id
                        result["_txt_file"] = txt_file
                        break
                except (httpx.TimeoutException, httpx.HTTPError):
                    continue
    return results


def _find_text_file(files: list[dict], ia_id: str) -> str | None:
    candidates = []
    for f in files:
        name = f.get("name", "")
        if name.endswith("_djvu.txt"):
            return name
        if name.endswith(".txt") and f.get("size", "0") != "0":
            size = int(f.get("size", 0))
            if size > 10000:
                candidates.append((size, name))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None


async def fetch_book_text(ia_id: str) -> str | None:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=HEADERS) as client:
        # First check metadata for actual available text files
        files_url = f"{ARCHIVE_URL}/metadata/{ia_id}/files"
        try:
            resp = await client.get(files_url)
            if resp.status_code == 200:
                files = resp.json().get("result", [])
                txt_file = _find_text_file(files, ia_id)
                if txt_file:
                    text = await _download_text(client, ia_id, txt_file)
                    if text:
                        return text
        except (httpx.TimeoutException, httpx.HTTPError):
            pass

        # Fallback: try the standard djvu.txt stream endpoint
        url = f"{ARCHIVE_URL}/stream/{ia_id}/{ia_id}_djvu.txt"
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return _clean_html_wrapper(resp.text)
        except (httpx.TimeoutException, httpx.HTTPError):
            pass

    return None


async def _download_text(client: httpx.AsyncClient, ia_id: str, filename: str) -> str | None:
    url = f"{ARCHIVE_URL}/download/{ia_id}/{filename}"
    try:
        resp = await client.get(url)
        if resp.status_code == 200 and len(resp.text) > 1000:
            return _clean_html_wrapper(resp.text)
    except (httpx.TimeoutException, httpx.HTTPError):
        pass
    return None


def _clean_html_wrapper(text: str) -> str:
    if "<body" in text[:5000] or "<html" in text[:5000]:
        match = re.search(r"<pre[^>]*>(.*?)</pre>", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    return text
