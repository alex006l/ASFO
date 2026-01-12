.PHONY: help install dev test run clean

help:
	@echo "Slicer Service - Makefile commands"
	@echo ""
	@echo "  install    Install production dependencies"
	@echo "  dev        Install dev dependencies"
	@echo "  test       Run unit tests"
	@echo "  run        Run service locally"
	@echo "  clean      Clean generated files"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest test_ASFO.py -v

run:
	uvicorn ASFO.app:app --host 0.0.0.0 --port 8080 --reload

clean:
	rm -rf __pycache__ ASFO/__pycache__
	rm -rf .pytest_cache
	rm -f ASFO.db
	find . -name "*.pyc" -delete
