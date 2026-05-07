# ===== Config =====
PYTHON := python3
PIP := pip3
APP := main.spec

# ===== Default =====
.DEFAULT_GOAL := help

# ===== Help =====
help:
	@echo ""
	@echo "Comandi disponibili:"
	@echo "  make install        Installa le dipendenze"
	@echo "  make run            Avvia l'app"
	@echo "  make build          Crea installer con PyInstaller"
	@echo "  make clean          Rimuove cache e file temporanei"
	@echo "  make clean-build    Rimuove artefatti build/dist"
	@echo "  make format         Format codice con black"
	@echo "  make lint           Controlli lint con ruff"
	@echo "  make test           Esegue i test pytest"
	@echo "  make freeze         Aggiorna requirements.txt"
	@echo ""

# ===== Setup =====
install:
	$(PIP) install -r requirements.txt

# ===== Run =====
run:
	$(PYTHON) main.py

# ===== Build =====
build:
	pyinstaller $(APP) --noconfirm

# ===== Tests =====
test:
	pytest

# ===== Formatting =====
format:
	black .

lint:
	ruff check .

# ===== Requirements =====
freeze:
	$(PIP) freeze > requirements.txt

# ===== Cleanup =====
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete

clean-build:
	rm -rf build dist *.spec

# ===== Full reset =====
reset: clean clean-build