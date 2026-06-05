import asyncio
import httpx
from api.models import Server

# Dictionnaire global partagé pour stocker l'état des serveurs en mémoire vive
SERVERS_DB = {}

async def poll_server(server: Server):
    """
    Interroge l'endpoint /health d'un serveur spécifique 
    et met à jour son statut de manière asynchrone.
    """
    url = f"{server.base_url()}/health"
    async with httpx.AsyncClient() as client:
        try:
            # On met un timeout court de 3 secondes pour ne pas bloquer la boucle
            response = await client.get(url, timeout=3.0)
            
            if response.status_code == 200 and response.json().get("status") == "ok":
                server.status = "UP"
            else:
                server.status = "DEGRADED"
        except (httpx.HTTPError, asyncio.TimeoutError):
            server.status = "DOWN"

async def run_poll_loop():
    """
    Boucle infinie asynchrone qui s'exécute toutes les 10 secondes
    pour mettre à jour le statut de tous les serveurs enregistrés.
    """
    while True:
        if SERVERS_DB:
            # On crée une liste de tâches asynchrones (une par serveur)
            tasks = [poll_server(server) for server in SERVERS_DB.values()]
            # On les exécute toutes en parallèle de manière non-bloquante
            await asyncio.gather(*tasks)
        
        # Pause de 10 secondes avant la prochaine vague de vérifications
        await asyncio.sleep(10)