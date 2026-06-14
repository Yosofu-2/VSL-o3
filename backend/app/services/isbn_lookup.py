# -*- coding: utf-8 -*-
"""ISBN lookup service using Google Books API."""

import httpx


async def lookup_isbn(isbn: str) -> dict:
    """Look up book info by ISBN using Google Books API."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("totalItems", 0) > 0:
                item = data["items"][0]["volumeInfo"]
                return {
                    "title": item.get("title", ""),
                    "authors": ", ".join(item.get("authors", [])),
                    "publisher": item.get("publisher", ""),
                    "publication_year": int(item.get("publishedDate", "0000")[:4]) if item.get("publishedDate") else None,
                    "pages": item.get("pageCount"),
                    "language": item.get("language", ""),
                    "description": item.get("description", ""),
                }
    except Exception:
        pass
    return {}
