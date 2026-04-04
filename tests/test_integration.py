import pytest
import asyncio
from unittest.mock import patch
from engine.task_queue import TaskQueue, get_task_queue
from db.models import SessionLocal, Review

@pytest.mark.asyncio
async def test_full_system_flow():
    """模擬全流程端到端測試，啟動真實佇列並寫入真實 SQLite 資料庫"""
    # Create an independent task queue for this test
    queue = TaskQueue(max_workers=1)
    await queue.start()

    with patch("engine.loader.review_project", return_value={"risks": [{"level": "high", "issue": "x"}], "verdict": "Integration Test"}):
        task_id = await queue.submit_task("End-to-End Alpha", "Project Spec Data")
        
        # Wait for the task to be completed
        import time
        max_wait = 5.0
        start = time.time()
        while time.time() - start < max_wait:
            status = queue.get_task_status(task_id)
            if status and status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.1)

        status = queue.get_task_status(task_id)
        assert status is not None
        assert status["status"] == "completed"
        assert status["result"]["verdict"] == "Integration Test"

        # Verify DB insertion
        db = SessionLocal()
        record = db.query(Review).filter(Review.project == "End-to-End Alpha").first()
        assert record is not None
        assert record.risk_high == 1
        assert record.verdict == "Integration Test"
        db.close()

    await queue.stop()
