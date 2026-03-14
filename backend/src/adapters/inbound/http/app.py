from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.adapters.inbound.http.exception_handlers import register_exception_handlers
from src.adapters.inbound.http.routers.submissions import router as submissions_router
from src.config.settings import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    """
    Factory function que cria e configura a aplicacao FastAPI.

    Por que factory function e nao instancia direta?
    Facilita testes -- cada teste pode criar sua propria
    instancia limpa sem compartilhar estado global.
    """
    app = FastAPI(
        title="Submission Service",
        description="Microservico para registro e correcao assincrona de respostas discursivas.",
        version=settings.app_version,
        # Desabilita docs em producao
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS
    # Em producao, substituir ["*"] pelos dominios permitidos
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(
        submissions_router,
        prefix=settings.api_prefix,
    )

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """
        Endpoint de health check.
        Usado pelo Docker, Kubernetes e load balancers para
        verificar se a aplicacao esta em pe/saudavel.
        """
        return {"status": "ok", "version": settings.app_version}

    return app


# Instancia global - uvicorn
app = create_app()
