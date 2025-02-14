.PHONY: format lint test clean install

# Format code using black and isort
format:
	black .
	isort .

# Run linting checks
lint:
	flake8 .
	black . --check
	isort . --check

# Run tests
test:
	pytest -v

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Install dependencies
install:
	pip install -r requirements.txt

# Run all quality checks
check: format lint test