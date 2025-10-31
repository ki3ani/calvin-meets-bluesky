.PHONY: format lint test clean install build

# Format code using black and isort
format:
	black .
	isort .

# Run linting checks
lint:
	flake8 app/ --extend-ignore=W503,E203 --max-line-length=120

# Run AI agent system tests
test:
	python test_agent_system.py

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# Install dependencies
install:
	pip install -r requirements.txt

# Build Lambda package
build:
	./build_lambda.sh

# Run all quality checks
check: format lint