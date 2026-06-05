import os
import pytest
from fastapi.testclient import TestClient

# Injection d'une fausse clé API pour l'environnement de test
os.environ["API_KEY"] = "testsecretkey"

from api.main import app
from api.poller import SERVERS_DB

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    """Vide la base de données simulée avant chaque test."""
    SERVERS_DB.clear()
    yield

def test_route_health():
    """Le endpoint /health doit renvoyer un statut OK public."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_route_metrics():
    """Le endpoint /metrics doit être fonctionnel."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "cpu_percent" in response.json()

def test_register_server_without_auth_fails():
    """Toute création sans entête API valide doit être bloquée (403)."""
    payload = {"id": "srv-1", "name": "Srv Test", "host": "localhost", "port": 80}
    response = client.post("/servers", json=payload)
    assert response.status_code == 403

def test_register_and_list_server_lifecycle():
    """Cycle de vie complet : création légitime, listage puis suppression."""
    payload = {"id": "srv-ok", "name": "Serveur Stable", "host": "127.0.0.1", "port": 8080}
    headers = {"X-API-Key": "testsecretkey"}
    
    # 1. Ajout (201 Created)
    res_post = client.post("/servers", json=payload, headers=headers)
    assert res_post.status_code == 201
    assert res_post.json()["status"] == "UNKNOWN"
    
    # 2. Liste (200 OK)
    res_get = client.get("/servers")
    assert res_get.status_code == 200
    assert len(res_get.json()) == 1
    assert res_get.json()[0]["id"] == "srv-ok"

    # 3. Suppression (200 OK)
    res_del = client.delete("/servers/srv-ok", headers=headers)
    assert res_del.status_code == 200
    
    # 4. Vérification après suppression (404 Not Found)
    res_del_404 = client.delete("/servers/srv-ok", headers=headers)
    assert res_del_404.status_code == 404

def test_trigger_manual_check_lifecycle():
    """Teste le déclenchement du health check manuel (augmente la couverture du poller)."""
    headers = {"X-API-Key": "testsecretkey"}
    payload = {"id": "srv-check", "name": "Srv Monitor", "host": "localhost", "port": 9999}
    
    # 1. Enregistrer un serveur
    client.post("/servers", json=payload, headers=headers)
    
    # 2. Déclencher le check manuel (va forcer l'exécution de code dans poller.py)
    response = client.post("/servers/srv-check/check")
    assert response.status_code == 200
    assert response.json()["status"] == "DOWN"  # DOWN car aucun vrai serveur ne tourne sur le port 9999

def test_trigger_manual_check_404():
    """Vérifie l'erreur 404 du check manuel sur un serveur inexistant."""
    response = client.post("/servers/unknown-srv/check")
    assert response.status_code == 404

def test_websocket_endpoint():
    """Teste le endpoint WebSocket pour valider son fonctionnement et couvrir api/main.py."""
    with client.websocket_connect("/ws/metrics") as websocket:
        data = websocket.receive_json()
        assert "cpu_percent" in data
        assert "memory_percent" in data