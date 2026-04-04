import pytest
from fastapi.testclient import TestClient
from web.main import app
from engine.task_queue import get_task_queue
from db.repository import save_review
from db.models import init_db, engine
from sqlalchemy import text
from unittest.mock import MagicMock, patch

@pytest.fixture
def client():
    """建立測試客戶端"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_review_data():
    """樣本審查資料"""
    return {
        "verdict": "通過審查",
        "risks": [{"level": "low", "issue": "x", "suggestion": "y"}],
        "missing": [],
        "improvements": [],
        "good_points": []
    }

class TestIndexRoute:
    def test_index_success(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "DSS" in response.text

    def test_index_with_reviews(self, client, sample_review_data):
        save_review("Test Project", sample_review_data)
        response = client.get("/")
        assert response.status_code == 200
        assert "Test Project" in response.text

    def test_index_error_handling(self, client):
        """測試資料庫失敗時的錯誤頁面"""
        with patch("web.main.get_recent_reviews", side_effect=Exception("DB Error")):
            response = client.get("/")
            assert response.status_code == 200 # FastAPI templates usually return 200 for error pages
            assert "DB Error" in response.text

class TestReviewFormRoute:
    def test_review_new_page(self, client):
        response = client.get("/review/new")
        assert response.status_code == 200
        assert "提交新審查" in response.text

    def test_review_submit_success(self, client):
        # Mock task_queue.submit_task to avoid real queue processing in web tests
        with patch("engine.task_queue.TaskQueue.submit_task", return_value="mock-task-id"):
            response = client.post(
                "/review/submit",
                data={"project_name": "New Project", "specification": "Spec content"}
            )
            assert response.status_code == 200
            assert "mock-task-id" in response.text
            assert "提交成功" in response.text

    def test_review_submit_error(self, client):
        """測試輸入欄位缺失的情況"""
        # FastAPI Form(...) will return 422 if fields are missing in modern FastAPI
        # But we check the app's handling
        response = client.post("/review/submit", data={"project_name": "Just name"})
        assert response.status_code == 422 # Validation error

class TestReviewDetailRoute:
    def test_detail_not_found(self, client):
        response = client.get("/review/999999")
        assert response.status_code == 404
        assert "找不到" in response.text

    def test_detail_success(self, client, sample_review_data):
        review_id = save_review("Beta", sample_review_data)
        response = client.get(f"/review/{review_id}")
        assert response.status_code == 200
        assert "Beta" in response.text

    def test_detail_error(self, client):
        with patch("web.main.get_review_by_id", side_effect=Exception("Fetch Error")):
            response = client.get("/review/1")
            assert "Fetch Error" in response.text

class TestKnowledgeBaseRoute:
    def test_knowledge_base(self, client):
        response = client.get("/knowledge")
        assert response.status_code == 200
        assert "基礎" in response.text or "知識" in response.text

class TestAPIs:
    def test_task_status_api(self, client):
        # Mock the queue to return a task status
        mock_status = {"task_id": "test-id", "status": "processing"}
        with patch("engine.task_queue.TaskQueue.get_task_status", return_value=mock_status):
            response = client.get("/task/test-id/status")
            assert response.status_code == 200
            assert response.json()["status"] == "processing"

    def test_task_status_not_found(self, client):
        with patch("engine.task_queue.TaskQueue.get_task_status", return_value=None):
            response = client.get("/task/no-id/status")
            assert "error" in response.json()

    def test_health_check_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_unhealthy(self, client):
        with patch("sqlalchemy.engine.base.Engine.connect", side_effect=Exception("Connect Error")):
            response = client.get("/health")
            assert response.json()["status"] == "unhealthy"

def test_static_files(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert b"body" in response.content
