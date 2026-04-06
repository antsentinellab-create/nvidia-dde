import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
import time
import pytest_asyncio
from engine.task_queue import (
    TaskQueue, 
    ReviewTask, 
    TaskStatus, 
    get_task_queue, 
    init_task_queue, 
    shutdown_task_queue
)

@pytest_asyncio.fixture
async def fresh_queue():
    """建立全新的任務佇列實例"""
    q = TaskQueue(max_workers=1)
    await q.start()
    yield q
    await q.stop()

class TestReviewTask:
    """測試 ReviewTask 資料結構"""
    def test_review_task_to_dict(self):
        task = ReviewTask("t1", "p1", "s1")
        d = task.to_dict()
        assert d["task_id"] == "t1"
        assert d["project_name"] == "p1"
        assert d["status"] == "pending"
        assert "created_at" in d

class TestTaskQueueCore:
    """測試 TaskQueue 核心邏輯"""
    
    @pytest.mark.asyncio
    async def test_submit_and_get_task(self, fresh_queue):
        queue = fresh_queue
        task_id = await queue.submit_task("Project Name", "Spec")
        
        task = queue.get_task(task_id)
        assert task is not None
        assert task.project_name == "Project Name"
        
        status = queue.get_task_status(task_id)
        assert status["task_id"] == task_id
        assert status["status"] in ["pending", "processing", "completed"]

    @pytest.mark.asyncio
    async def test_list_tasks(self, fresh_queue):
        queue = fresh_queue
        await queue.submit_task("P1", "S1")
        await queue.submit_task("P2", "S2")
        
        tasks = queue.list_tasks(limit=10)
        assert len(tasks) >= 2
        assert tasks[0]["project_name"] in ["P1", "P2"]

    @pytest.mark.asyncio
    async def test_worker_processing_success(self, fresh_queue):
        """測試 Worker 成功處理任務"""
        queue = fresh_queue
        
        # Mock review_project to return success immediately
        mock_result = {"risks": [], "verdict": "OK"}
        with patch("design_decision_engine.review_project", return_value=mock_result), \
             patch("engine.task_queue.review_project", return_value=mock_result), \
             patch("db.repository.save_review", return_value=123):
            
            task_id = await queue.submit_task("Test", "Spec")
            
            # 等待 Worker 處理完成或超時
            # 使用 poll 檢查狀態
            max_wait = 5.0
            start = time.time()
            while time.time() - start < max_wait:
                status = queue.get_task_status(task_id)
                if status["status"] == "completed":
                    break
                await asyncio.sleep(0.1)
                
            status = queue.get_task_status(task_id)
            assert status["status"] == "completed"
            assert status["result"] == mock_result

    @pytest.mark.asyncio
    async def test_worker_processing_failure(self, fresh_queue):
        """測試 Worker 處理失敗"""
        queue = fresh_queue
        
        # Mock review_project to raise exception
        with patch("design_decision_engine.review_project", side_effect=Exception("Failed!")), \
             patch("engine.task_queue.review_project", side_effect=Exception("Failed!")), \
             patch("db.repository.save_review"):
            
            task_id = await queue.submit_task("Fail Test", "Spec")
            
            max_wait = 5.0
            start = time.time()
            while time.time() - start < max_wait:
                status = queue.get_task_status(task_id)
                if status["status"] == "failed":
                    break
                await asyncio.sleep(0.1)
                
            status = queue.get_task_status(task_id)
            assert status["status"] == "failed"
            assert "Failed!" in status["error"]

class TestGlobalQueueFunctions:
    """測試全域佇列管理函數"""
    
    @pytest.mark.asyncio
    async def test_init_and_shutdown(self):
        q = await init_task_queue()
        assert q._running is True
        
        await shutdown_task_queue()
        # Due to singleton pattern, if we shutdown, the global instance is still there but stopped
        assert q._running is False
