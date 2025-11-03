
from fastapi import FastAPI
from mangum import Mangum

from app.routers import campaigns, graphql

# --- Aplicación FastAPI ---
app = FastAPI(
    title="OmniPro Email Ingestion Service",
    description="API para la ingestión de campañas de email por lotes y consulta de estado.",
    version="0.1.0",
)

# --- Endpoints / Routers ---

@app.get("/", summary="Endpoint de Bienvenida", tags=["General"])
def read_root() -> dict:
    """
    Endpoint de prueba que devuelve un mensaje de bienvenida.
    """
    return {"message": "Hello World"}

# Router para GraphQL
app.include_router(graphql.graphql_router, prefix="/graphql")

# Router para Campañas (upload)
app.include_router(campaigns.router)


# --- AWS Lambda Handler ---
handler = Mangum(app)


# --- Ejecución Local ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
