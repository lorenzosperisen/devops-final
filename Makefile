.PHONY: up down logs test lint dev

up:
	@echo "Démarrage de la stack Docker Compose..."
	docker compose up --build -d

down:
	@echo "Arrêt de la stack et nettoyage..."
	docker compose down -v

logs:
	@echo "Affichage des logs en temps réel..."
	docker compose logs -f

test:
	@echo "Exécution des tests avec couverture de code..."
	python3 -m pytest tests/ -v --cov=api --cov-fail-under=75

lint:
	@echo "Analyse statique du code (flake8)..."
	flake8 api/ dashboard/ tests/

dev:
	@echo "Lancement en mode développement local (sans Docker)..."
	@echo "Démarrage de l'API sur le port 8000..."
	python3 -m uvicorn api.main:app --reload --port 8000 &
	@echo "Démarrage du Dashboard Streamlit sur le port 8501..."
	python3 -m streamlit run dashboard/app.py