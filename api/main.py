import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.metrics import get_system_metrics
from api.auth import verify_api_key
from api.models import Server, ServerIn, ServerOut
from api.poller import SERVERS_DB, run_poll_loop, poll_server

# Utilisation du lifespan pour démarrer la boucle de polling en arrière-plan au démarrage de l'API
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage de la tâche de fond
    polling_task = asyncio.create_task(run_poll_loop())
    yield
    # Annulation de la tâche à la fermeture de l'application
    polling_task.cancel()

app = FastAPI(
    title="DevOps Monitoring API",
    description="Backend de collecte de métriques et supervision de serveurs",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour permettre au Dashboard Streamlit de communiquer librement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES PUBLIQUES ---

@app.get("/health")
def get_health():
    """Endpoint de Liveness Probe requis pour Azure Container Apps."""
    return {"status": "ok"}

@app.get("/metrics")
def get_metrics():
    """Retourne l'état instantané des ressources matérielles de la machine."""
    return get_system_metrics()

# --- ROUTE WEBSOCKET ---

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """Stream des données JSON de métriques système toutes les secondes."""
    await websocket.accept()
    try:
        while True:
            metrics_snapshot = get_system_metrics()
            await websocket.send_json(metrics_snapshot)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        # Gestion propre de la déconnexion du client sans faire crasher l'API
        pass

# --- ROUTES CRUD SERVEURS (Sécurisées par clé API) ---

@app.post("/servers", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def register_server(server_in: ServerIn, api_key: str = Depends(verify_api_key)):
    """Enregistre un nouveau serveur à surveiller."""
    if server_in.id in SERVERS_DB:
        raise HTTPException(status_code=400, detail="Un serveur avec cet ID existe déjà.")
    
    new_server = Server(
        id=server_in.id,
        name=server_in.name,
        host=server_in.host,
        port=server_in.port
    )
    SERVERS_DB[new_server.id] = new_server
    return new_server

@app.get("/servers", response_model=list[ServerOut])
def list_servers():
    """Liste tous les serveurs enregistrés ainsi que leur état de santé actuel."""
    return list(SERVERS_DB.values())

@app.delete("/servers/{server_id}")
def delete_server(server_id: str, api_key: str = Depends(verify_api_key)):
    """Supprime un serveur de la liste de surveillance."""
    if server_id not in SERVERS_DB:
        raise HTTPException(status_code=404, detail="Serveur introuvable.")
    del SERVERS_DB[server_id]
    return {"message": f"Serveur {server_id} supprimé avec succès."}

@app.post("/servers/{server_id}/check", response_model=ServerOut)
async def trigger_manual_check(server_id: str):
    """Force un diagnostic immédiat (health check manuel) sur un serveur."""
    if server_id not in SERVERS_DB:
        raise HTTPException(status_code=404, detail="Serveur introuvable.")
    
    server = SERVERS_DB[server_id]
    await poll_server(server)
    return server