import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import test settings before importing app
from tests.test_config import TestSettings
import unittest.mock as mock

# Mock the settings before importing app
test_settings = TestSettings()
with mock.patch('app.config.get_settings', return_value=test_settings):
    from app.main import app
    from app.database.models import Base

# Use SQLite in-memory database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="module")
def client():
    # Mock settings for the duration of the tests
    with mock.patch('app.config.get_settings', return_value=test_settings):
        with TestClient(app) as c:
            yield c