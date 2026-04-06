"""
Async Task Queue for Review Processing
使用 ThreadPoolExecutor + asyncio.Queue 實現非同步審查任務
"""
import asyncio
import uuid
from datetime import datetime, timezone, timezone
from typing import Dict, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
import os


class TaskStatus(Enum):
    """任務狀態列舉"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReviewTask:
    """審查任務資料結構"""
    task_id: str
    project_name: str
    specification: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0  # 0-100
    current_stage: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """轉換為字典供 JSON 序列化"""
        return {
            "task_id": self.task_id,
            "project_name": self.project_name,
            "specification": self.specification,
            "status": self.status.value,
            "progress": self.progress,
            "current_stage": self.current_stage,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class TaskQueue:
    """
    任務佇列管理器
    使用 asyncio.Queue + ThreadPoolExecutor 管理非同步審查任務
    """
    
    def __init__(self, max_workers: int = None):
        """
        初始化任務佇列
        
        Args:
            max_workers: 最大並發 worker 數量，預設 3
        """
        if max_workers is None:
            max_workers = int(os.getenv("MAX_WORKERS", "3"))
        
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.queue: Optional[asyncio.Queue[ReviewTask]] = None
        self.tasks: Dict[str, ReviewTask] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """啟動背景 worker"""
        if not self._running:
            if self.queue is None:
                self.queue = asyncio.Queue()
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            
    async def stop(self):
        """停止背景 worker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        if self.executor:
            self.executor.shutdown(wait=False)
    
    async def submit_task(self, project_name: str, specification: str) -> str:
        """
        提交新的審查任務
        
        Args:
            project_name: 專案名稱
            specification: 規格說明
            
        Returns:
            str: 任務 ID
        """
        # Ensure queue exists and worker is running
        if not self._running or self.queue is None:
            await self.start()

        task_id = str(uuid.uuid4())
        task = ReviewTask(
            task_id=task_id,
            project_name=project_name,
            specification=specification
        )
        
        self.tasks[task_id] = task
        if self.queue:
            await self.queue.put(task)
        
        return task_id
    
    async def _worker(self):
        """背景 worker - 處理佇列中的任務"""
        while self._running:
            try:
                # 從佇列獲取任務
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                # 執行任務（在 executor 中運行以避免阻塞）
                future = self.executor.submit(self._execute_task, task)
                await asyncio.wrap_future(future)
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # 超時表示佇列為空，繼續等待
                continue
            except asyncio.CancelledError:
                # 被取消，退出 worker
                break
            except Exception as e:
                import json
                from datetime import datetime, timezone, timezone
                log_entry = {
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0800"),
                    "lvl": "ERROR",
                    "script": "task_queue.py",
                    "fn": "_worker",
                    "msg": f"Worker 錯誤：{e}",
                    "elapsed_ms": 0
                }
                print(json.dumps(log_entry, ensure_ascii=False))
    
    def _execute_task(self, task: ReviewTask):
        """
        執行單個審查任務（在 thread pool 中運行）
        
        Args:
            task: 要執行的任務
        """
        import json
        from datetime import datetime, timezone, timezone
        
        start_time = datetime.now(timezone.utc)
        
        def log_progress(stage: str, progress: int, msg: str):
            """記錄進度日誌"""
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_entry = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "lvl": "INFO",
                "script": "task_queue.py",
                "fn": "_execute_task",
                "msg": msg,
                "extra": {
                    "task_id": task.task_id,
                    "project": task.project_name,
                    "stage": stage,
                    "progress": progress
                },
                "elapsed_ms": int(elapsed)
            }
            print(json.dumps(log_entry, ensure_ascii=False))
        
        try:
            log_progress("", 0, f"🚀 開始執行任務：{task.task_id} | 專案：{task.project_name}")
            
            # 更新任務狀態
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now(timezone.utc)
            
            # Stage 1: 載入知識庫 (10%)
            task.current_stage = "載入知識庫..."
            task.progress = 10
            log_progress(task.current_stage, 10, "📚 [10%] 載入知識庫...")
            
            # Stage 2: Risk Analyst 審查 (40%)
            task.current_stage = "風險分析師審查中..."
            task.progress = 40
            log_progress(task.current_stage, 40, "⚠️  [40%] 風險分析師審查中...")
            
            # Stage 3: Completeness Reviewer 審查 (70%)
            task.current_stage = "完整性審查員審查中..."
            task.progress = 70
            log_progress(task.current_stage, 70, "✅ [70%] 完整性審查員審查中...")
            
            # Stage 4: Improvement Advisor 審查 (90%)
            task.current_stage = "改進顧問審查中..."
            task.progress = 90
            log_progress(task.current_stage, 90, "💡 [90%] 改進顧問審查中...")
            
            # Stage 5: Aggregator 裁決 (100%)
            task.current_stage = "生成最終裁決..."
            task.progress = 100
            log_progress(task.current_stage, 100, "🏛️ [100%] 生成最終裁決...")
            
            # 呼叫實際的審查引擎
            log_progress(task.current_stage, 100, "🔍 呼叫 AI 審查引擎...")
            import design_decision_engine as _dde
            result = _dde.review_project(task.specification)
            
            log_progress(task.current_stage, 100, f"✅ 審查完成！風險:{len(result.get('risks', []))} 缺失:{len(result.get('missing', []))} 建議:{len(result.get('improvements', []))} 優點:{len(result.get('good_points', []))}")
            
            # 保存到資料庫
            log_progress(task.current_stage, 100, "💾 儲存到資料庫...")
            from db.repository import save_review
            review_id = save_review(
                project_name=task.project_name,
                result_json=result
            )
            log_progress(task.current_stage, 100, f"✅ 已儲存，審查 ID: {review_id}")
            
            # 設置任務結果
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            
            total_elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_entry = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "lvl": "INFO",
                "script": "task_queue.py",
                "fn": "_execute_task",
                "msg": f"✅ 任務完成：{task.task_id}",
                "extra": {
                    "task_id": task.task_id,
                    "project": task.project_name,
                    "review_id": review_id,
                    "status": "COMPLETED"
                },
                "elapsed_ms": int(total_elapsed)
            }
            print(json.dumps(log_entry, ensure_ascii=False))
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            total_elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            log_entry = {
                "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "lvl": "ERROR",
                "script": "task_queue.py",
                "fn": "_execute_task",
                "msg": f"❌ 任務失敗 {task.task_id}: {e}",
                "extra": {
                    "task_id": task.task_id,
                    "project": task.project_name,
                    "error": str(e),
                    "status": "FAILED"
                },
                "elapsed_ms": int(total_elapsed)
            }
            print(json.dumps(log_entry, ensure_ascii=False))
            import traceback
            traceback.print_exc()
    
    def get_task(self, task_id: str) -> Optional[ReviewTask]:
        """
        獲取任務狀態
        
        Args:
            task_id: 任務 ID
            
        Returns:
            Optional[ReviewTask]: 任務物件，若不存在則為 None
        """
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        獲取任務狀態（字典格式）
        
        Args:
            task_id: 任務 ID
            
        Returns:
            Optional[dict]: 任務狀態字典
        """
        task = self.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    def list_tasks(self, limit: int = 10) -> list:
        """
        列出最近的任務
        
        Args:
            limit: 限制數量
            
        Returns:
            list: 任務列表
        """
        # 按創建時間排序，取最新的 N 個
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.created_at,
            reverse=True
        )
        return [t.to_dict() for t in sorted_tasks[:limit]]


# Global task queue instance
_global_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """獲取全域任務佇列實例"""
    global _global_queue
    if _global_queue is None:
        _global_queue = TaskQueue()
    return _global_queue


async def init_task_queue():
    """初始化並啟動任務佇列"""
    queue = get_task_queue()
    await queue.start()
    return queue


async def shutdown_task_queue():
    """關閉任務佇列"""
    queue = get_task_queue()
    await queue.stop()
