import psutil

def get_system_metrics() -> dict:
    """
    Retourne un snapshot instantané de l'utilisation du CPU, 
    de la mémoire et du disque (non-bloquant).
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }