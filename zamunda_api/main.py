
"""
main.py
This module defines a FastAPI application for the Zamunda API. It includes
routes for searching the Zamunda API with optional caching and a default
root route. The application also includes a background thread for cleaning
up expired cache entries.
Modules:
    logging: Provides logging capabilities.
    threading: Provides threading capabilities.
    fastapi: Provides FastAPI framework for building web APIs.
    uvicorn: Provides ASGI server for serving FastAPI applications.
    zamunda: Provides Zamunda API client.
    datetime: Provides date and time manipulation capabilities.
Functions:
    app_lifespan: Defines the lifespan event handlers for the FastAPI app.
    read_root: Default route that returns the API version.
    search: Route for searching the Zamunda API with optional caching.
Constants:
    CACHE_EXPIRATION: The duration for which cache entries are considered valid.
Usage:
    Run this module directly to start the FastAPI server with Uvicorn.
"""
import logging
import threading
from datetime import datetime, timedelta
import fastapi
import uvicorn
try:
    from zamunda_api.zamunda import Zamunda
except ImportError:
    from .zamunda import Zamunda

logger = logging.getLogger("uvicorn")
logger.info("Starting server...")

z = Zamunda()

# Cache storage
cache = {}
CACHE_EXPIRATION = timedelta(minutes=60)

def app_lifespan(_: fastapi.FastAPI):
    """Define a FastAPI app with lifespan event handlers"""
    def cleanup_cache():
        while True:
            current_time = datetime.now()
            keys_to_delete = [
                key for key, value in cache.items()
                if value['timestamp'] < current_time - CACHE_EXPIRATION
            ]
            logger.info("Cleaning up %d expired cache entries", len(keys_to_delete))
            for key in keys_to_delete:
                del cache[key]
                logger.info("Deleted expired cache entry: %s", key)
            # Sleep for some time before next cleanup
            threading.Event().wait(60 * 5)  # Every 5 minutes

    logger.info("Starting cache cleanup thread...")
    cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
    cleanup_thread.start()
    yield

app = fastapi.FastAPI(lifespan=app_lifespan)


@app.get("/")
def read_root():
    """default route"""
    return "Zamunda API v1"

@app.get("/search")
def search(
    q: str,
    user: str,
    password: str,
    force_search: bool = False,
    provide_magnet: bool = False
    ):
    """
    Search the Zamunda API with optional caching.

    Args:
        q (str): Query string.
        user (str): Username.
        password (str): Password.
        force_search (bool): If True, bypass cache and perform a fresh search.
        provide_magnet (bool): If True, provide magnet links in the search results.

    Returns:
        dict: Search results.
    """
    # Generate cache key
    cache_key = f"{q}-{provide_magnet}"
    current_time = datetime.now()

    if not force_search:
        # Check if the query is cached and not expired
        if cache_key in cache:
            cached_entry = cache[cache_key]
            if cached_entry['timestamp'] > current_time - CACHE_EXPIRATION:
                logger.info("Returning cached result")
                return cached_entry['response']
            else:
                # Remove expired cache
                del cache[cache_key]

    # Perform the search
    logger.info("Performing search")
    response = z.search(q, user, password, provide_magnet)

    # Cache the response
    cache[cache_key] = {
        'response': response,
        'timestamp': current_time
    }

    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
