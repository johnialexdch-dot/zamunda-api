"""
main.py
Zamunda API сървър с FastAPI. Поддържа търсене и Stremio stream endpoint.
"""

import logging
import threading
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

try:
    from zamunda_api.zamunda import Zamunda
except ImportError:
    from zamunda import Zamunda

zamunda = Zamunda(
    base_url="https://zamunda.net",
    user="coyec75395",
    password="rxM6N.h2N4aYe7_"
)


logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# Кеш
cache = {}
CACHE_EXPIRATION = timedelta(minutes=60)

def cleanup_cache():
    while True:
        current_time = datetime.now()
        keys_to_delete = [
            key for key, value in cache.items()
            if value['timestamp'] < current_time - CACHE_EXPIRATION
        ]
        if keys_to_delete:
            logger.info("Cleaning up %d expired cache entries", len(keys_to_delete))
        for key in keys_to_delete:
            del cache[key]
            logger.info("Deleted expired cache entry: %s", key)
        threading.Event().wait(300)  # 5 минути

threading.Thread(target=cleanup_cache, daemon=True).start()

app = FastAPI()

@app.get("/")
def read_root():
    return "Zamunda API v1"

@app.get("/search")
def search(
    q: str,
    user: str,
    password: str,
    force_search: bool = False,
    provide_infohash: bool = False
):
    """
    Търсене в Zamunda с кеш.
    """
    cache_key = f"{q}-{provide_infohash}"
    current_time = datetime.now()

    if not force_search and cache_key in cache:
        cached_entry = cache[cache_key]
        if cached_entry['timestamp'] > current_time - CACHE_EXPIRATION:
            logger.info("Returning cached result for %s", q)
            return cached_entry['response']
        else:
            del cache[cache_key]

    try:
        logger.info("Performing Zamunda search for: %s", q)
        response = zamunda.search(q, user, password, provide_infohash)
    except Exception as e:
        logger.error("Search failed: %s", e)
        return JSONResponse(status_code=500, content={"error": "Search failed"})

    cache[cache_key] = {
        'response': response,
        'timestamp': current_time
    }
    return response

@app.get("/stream/{type}/{id}")
def stream(type: str, id: str, request: Request):
    """
    Stremio stream endpoint — използва IMDb ID (tt...)
    """
    user = request.query_params.get("user")
    password = request.query_params.get("password")

    if not user or not password:
        return JSONResponse(status_code=400, content={"error": "Missing 'user' or 'password'"})

    logger.info(f"Stremio stream request: {type=} {id=}")

    try:
        results = zamunda.search(id, user, password, provide_infohash=True)
    except Exception as e:
        logger.error("Stremio search error: %s", e)
        return JSONResponse(status_code=500, content={"error": "Search failed"})

    streams = []
    for result in results.get("results", []):
        if 'magnet' in result:
            streams.append({
                "name": "Zamunda",
                "type": "torrent",
                "infoHash": result.get("infohash", ""),
                "title": result.get("title", ""),
                "sources": [result["magnet"]],
            })

    return streams

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")

