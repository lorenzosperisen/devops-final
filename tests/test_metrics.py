from api.metrics import get_system_metrics

def test_get_system_metrics():
    """Vérifie que la capture retourne les bons champs avec des valeurs logiques (0-100%)."""
    metrics = get_system_metrics()
    
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics
    
    assert 0.0 <= metrics["cpu_percent"] <= 100.0
    assert 0.0 <= metrics["memory_percent"] <= 100.0
    assert 0.0 <= metrics["disk_percent"] <= 100.0