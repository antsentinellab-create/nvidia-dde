import pytest
from unittest.mock import MagicMock
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True)
def mock_openai(monkeypatch):
    """
    Globally mock the OpenAI client to prevent real API calls and hanging.
    """
    mock_client_instance = MagicMock()
    mock_completions = MagicMock()
    mock_client_instance.chat.completions = mock_completions
    
    # Mock the return value of create()
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"risks": [], "verdict": "Mocked verdict"}'
    mock_message.reasoning_content = None
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_completions.create.return_value = mock_response
    
    # Mock the OpenAI class constructor
    # We mock it in both design_decision_engine and any other place it might be imported
    monkeypatch.setattr("design_decision_engine.OpenAI", MagicMock(return_value=mock_client_instance))
    
    return mock_client_instance

@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database is initialized and clean for each test if using SQLite"""
    from db.models import init_db, engine, Base
    from sqlalchemy import text
    
    # Initialize schema
    init_db()
    
    yield
    
    # Cleanup after test
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()

@pytest.fixture(autouse=True)
def stop_task_queue(monkeypatch):
    """Ensure task queue is reset after each test"""
    from engine.task_queue import get_task_queue
    import engine.task_queue
    
    # Run the test
    yield
    
    # Since this is a sync fixture for both sync and async tests,
    # we don't await queue.stop() here (it's risky without a running loop).
    # Instead, we force-clear the singleton and shutdown executors.
    queue = get_task_queue()
    if queue:
        if queue.executor:
            queue.executor.shutdown(wait=False)
        queue._running = False
        # Reset the global singleton
        engine.task_queue._global_queue = None
