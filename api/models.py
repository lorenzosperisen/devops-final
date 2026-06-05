from dataclasses import dataclass
from pydantic import BaseModel, Field

@dataclass
class Server:
    id: str
    name: str
    host: str
    port: int
    status: str = "UNKNOWN"

    def base_url(self) -> str:
        """Retourne l'URL de base pour interroger le serveur."""
        return f"http://{self.host}:{self.port}"

class ServerIn(BaseModel):
    id: str = Field(..., description="Identifiant unique du serveur")
    name: str = Field(..., description="Nom lisible du serveur")
    host: str = Field(..., description="Hôte ou adresse IP (ex: api, localhost)")
    port: int = Field(..., max_digits=None, ge=1, le=65535, description="Port valide (1-65535)")

class ServerOut(BaseModel):
    id: str
    name: str
    host: str
    port: int
    status: str