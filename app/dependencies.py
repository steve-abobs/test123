from fastapi import Request

from app.search_backend import SearchBackend


def get_search_backend(request: Request) -> SearchBackend:
    return request.app.state.search_backend
