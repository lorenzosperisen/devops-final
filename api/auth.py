import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Vérifie la présence et la validité de la clé API reçue dans les headers.
    Lève une exception 403 Forbidden si elle est invalide ou manquante.
    """
    expected_api_key = os.getenv("API_KEY")
    
    # Sécurité au cas où la variable d'environnement n'est pas définie en local
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API de configuration est manquante sur le serveur."
        )
        
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé : Clé API invalide ou manquante."
        )
    return api_key