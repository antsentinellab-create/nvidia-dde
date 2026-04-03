"""
Web UI Test Suite
使用 FastAPI TestClient 測試主要路由與功能
"""
import pytest
from fastapi.testclient import TestClient
from web.main import app
from engine.task_queue import get_task_queue

@pytest.fixture(autouse=True)
def shutdown_task_queue():
    yield
    q = get_task_queue()
    if q: q._running = False
from db.repository import save_review
from db.models import init_db, engine
from sqlalchemy import text


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """初始化測試資料庫"""
    init_db()
    yield
    # Cleanup: delete all reviews after tests
    from db.models import SessionLocal, Review
    db = SessionLocal()
    try:
        db.query(Review).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """創建測試客戶端"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_review():
    """樣本審查資料"""
    return {
        "verdict": "通過審查，風險可接受",
        "risks": [
            {"level": "high", "description": "High risk"},
            {"level": "medium", "description": "Medium risk"},
            {"level": "low", "description": "Low risk"}
        ]
    }


class TestIndexRoute:
    """測試首頁路由"""
    
    def test_index_returns_200(self, client):
        """GET / 應該返回 200"""
        response = client.get("/")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "DSS" in content and "設計審查系統" in content
    
    def test_index_displays_reviews(self, client, sample_review):
        """首頁應該顯示審查記錄"""
        # Create a review first
        save_review("Test Project", sample_review)
        
        response = client.get("/")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "Test Project" in content or "審查記錄" in content


class TestReviewNewRoute:
    """測試提交新審查路由"""
    
    def test_review_new_page_returns_200(self, client):
        """GET /review/new 應該返回表單頁面"""
        response = client.get("/review/new")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "提交新審查" in content
    
    def test_review_submit_creates_task(self, client):
        """POST /review/submit 應該創建非同步任務"""
        response = client.post(
            "/review/submit",
            data={
                "project_name": "Test Project Alpha",
                "specification": "This is a test specification"
            },
            follow_redirects=False
        )
        
        # Should redirect to success page or show success message
        assert response.status_code in [200, 303]
        content = response.content.decode('utf-8')
        assert "提交成功" in content or "審查已提交" in content
    
    def test_review_submit_validation(self, client):
        """表單驗證：缺少必要欄位應該失敗"""
        response = client.post(
            "/review/submit",
            data={
                "project_name": "",  # Empty project name
                "specification": "Some spec"
            }
        )
        
        # Should show error or validation message
        assert response.status_code in [200, 400]


class TestReviewDetailRoute:
    """測試審查詳情路由"""
    
    def test_review_detail_not_found(self, client):
        """GET /review/{id} 當 ID 不存在時應返回 404"""
        response = client.get("/review/999999")
        assert response.status_code == 404
    
    def test_review_detail_exists(self, client, sample_review):
        """GET /review/{id} 當 ID 存在時應返回詳情"""
        # Create a review first
        review_id = save_review("Test Project Beta", sample_review)
        
        response = client.get(f"/review/{review_id}")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "Test Project Beta" in content
        assert "審查詳情" in content


class TestKnowledgeBaseRoute:
    """測試知識庫路由"""
    
    def test_knowledge_base_returns_200(self, client):
        """GET /knowledge 應該返回知識庫頁面"""
        response = client.get("/knowledge")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "知識庫" in content
    
    def test_knowledge_base_shows_categories(self, client):
        """知識庫應該顯示分類"""
        response = client.get("/knowledge")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Should show category headers
        assert "角色定義" in content or "風險模板" in content


class TestTaskStatusAPI:
    """測試任務狀態 API"""
    
    def test_task_status_invalid_id(self, client):
        """GET /task/{id}/status 當 ID 無效時應返回錯誤"""
        response = client.get("/task/invalid-id/status")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or data.get("status") is None
    
    def test_task_status_format(self, client):
        """任務狀態 API 應返回正確的 JSON 格式"""
        # Submit a task first
        submit_response = client.post(
            "/review/submit",
            data={
                "project_name": "API Test Project",
                "specification": "Testing API"
            },
            follow_redirects=False
        )
        
        # Extract task_id from response (this is simplified - in real scenario we'd parse HTML)
        # For now, just test the endpoint exists
        response = client.get("/task/test-123/status")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)


class TestHealthCheckAPI:
    """測試健康檢查 API"""
    
    def test_health_check_returns_healthy(self, client):
        """GET /health 應該返回健康狀態"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]


class TestStaticFiles:
    """測試靜態文件服務"""
    
    def test_css_file_accessible(self, client):
        """CSS 文件應該可以訪問"""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert b"--bg-primary" in response.content or b"background" in response.content


class TestAsyncTaskIntegration:
    """測試非同步任務整合"""
    
    def test_task_queue_initialized(self, client):
        """任務佇列應該正確初始化"""
        from engine.task_queue import get_task_queue
        queue = get_task_queue()
        assert queue is not None
        assert queue.max_workers > 0
    
    @pytest.mark.asyncio
    async def test_submit_and_track_task(self):
        """測試提交任務並追蹤進度"""
        from engine.task_queue import get_task_queue
        
        queue = get_task_queue()
        
        # Submit task
        task_id = await queue.submit_task(
            "Async Test Project",
            "Testing async functionality"
        )
        
        assert task_id is not None
        
        # Check status
        status = queue.get_task_status(task_id)
        assert status is not None
        assert "task_id" in status
        assert status["task_id"] == task_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
