# Calvin Meets Bluesky

A FastAPI-based bot that posts Calvin and Hobbes comics to Bluesky social network. This project automates the process of sharing comic strips while maintaining proper formatting and scheduling.

## Features

- 🎨 Automated comic strip posting to Bluesky
- 📊 Analytics tracking for posts
- 🗄️ S3 storage integration for comic images
- ⏰ Scheduled posting functionality
- 🌐 REST API endpoints for management
- 🐳 Docker support for easy deployment

## Tech Stack

- Python 3.12
- FastAPI (Web Framework)
- SQLAlchemy (Database ORM)
- AWS S3 (Image Storage)
- Docker & Docker Compose
- pytest (Testing Framework)

## Project Structure

```
app/
├── database/        # Database models and connection management
├── models/          # Pydantic models and data structures
├── routers/         # API route handlers
├── services/        # Business logic and external service integration
└── utils/          # Helper functions and utilities
```

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/calvin-meets-bluesky.git
cd calvin-meets-bluesky
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix or MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running with Docker

Development:
```bash
docker-compose -f docker-compose.dev.yml up
```

Production:
```bash
docker-compose up
```

## API Endpoints

- `/comics` - Comic management endpoints
- `/posts` - Post management and scheduling
- `/admin` - Administrative functions

## Testing

Run the test suite:
```bash
pytest
```

## License

[Add your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.