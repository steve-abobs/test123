from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routers import documents, search
from app.search_backend import ElasticsearchBackend


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    backend = ElasticsearchBackend(settings.elastic_url, settings.elastic_index)
    await backend.ensure_index()
    app.state.search_backend = backend

    yield

    await backend.close()
    await engine.dispose()


app = FastAPI(
    title="Document Search Service",
    description=(
        "Простой сервис полнотекстового поиска по документам: данные хранятся в "
        "базе данных, поисковый индекс — в Elasticsearch."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(search.router)
app.include_router(documents.router)


@app.get("/health", tags=["service"], summary="Проверка работоспособности сервиса")
async def health() -> dict[str, str]:
    return {"status": "ok"}
