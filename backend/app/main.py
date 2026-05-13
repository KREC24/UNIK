import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, get_project_name, get_debug_mode, get_log_level
from app.core.database import init_db, close_db
from app.api.routes.parser import router as parser_router
from app.api.routes.projects import router as projects_router
from app.api.routes.ogz import router as ogz_router
from app.api.routes.clients import router as clients_router
from app.api.routes.settings import router as settings_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.search import router as search_router
from app.api.routes.incoming import router as incoming_router
from app.api.routes.employees import router as employees_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.offers import router as offers_router

_log_level = getattr(logging, get_log_level().upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("DB init: creating tables if needed...")
    await init_db()
    logger.info("App starting: title=%s debug=%s log_level=%s",
                get_project_name(), get_debug_mode(), get_log_level())
    yield
    logger.info("App shutting down")
    await close_db()


app = FastAPI(
    title=get_project_name(),
    version=settings.VERSION,
    debug=get_debug_mode(),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parser_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(ogz_router, prefix=settings.API_V1_PREFIX)
app.include_router(clients_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(search_router, prefix=settings.API_V1_PREFIX)
app.include_router(incoming_router, prefix=settings.API_V1_PREFIX)
app.include_router(employees_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(offers_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "debug_mode": get_debug_mode(),
    }
