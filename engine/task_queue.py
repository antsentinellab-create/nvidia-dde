"""
Async Task Queue for Review Processing
使用 ThreadPoolExecutor + asyncio.Queue 實現非同步審查任務
"""
import asyncio
import uuid
from datetime import datetime
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
    created_at: datetime = field(default_factory=datetime.utcnow)
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
        self.queue: asyncio.Queue[ReviewTask] = asyncio.Queue()
        self.tasks: Dict[str, ReviewTask] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """啟動背景 worker"""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            
    async def stop(self):
        """停止背景 worker"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
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
        task_id = str(uuid.uuid4())
        task = ReviewTask(
            task_id=task_id,
            project_name=project_name,
            specification=specification
        )
        
        self.tasks[task_id] = task
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
                print(f"Worker 錯誤：{e}")
    
    def _execute_task(self, task: ReviewTask):
        """
        執行單個審查任務（在 thread pool 中運行）
        
        Args:
            task: 要執行的任務
        """
        try:
            # 更新任務狀態
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            
            # TODO: 這裡需要整合實際的 review engine
            # 目前先模擬執行過程
            
            # Stage 1: 載入知識庫 (10%)
            task.current_stage = "載入知識庫..."
            task.progress = 10
            
            # Stage 2: Risk Analyst 審查 (40%)
            task.current_stage = "風險分析師審查中..."
            task.progress = 40
            # TODO: 呼叫实际的 risk analyst
            
            # Stage 3: Completeness Reviewer 審查 (70%)
            task.current_stage = "完整性審查員審查中..."
            task.progress = 70
            # TODO: 呼叫实际的 completeness reviewer
            
            # Stage 4: Improvement Advisor 審查 (90%)
            task.current_stage = "改進顧問審查中..."
            task.progress = 90
            # TODO: 呼叫实际的 improvement advisor
            
            # Stage 5: Aggregator 裁決 (100%)
            task.current_stage = "生成最終裁決..."
            task.progress = 100
            
            # TODO: 實際應該要整合 engine/loader.py 和 design_decision_engine.py
            # 這裡先返回一個模擬的結果
            task.result = {
                "verdict": "通過審查（模擬結果）",
                "risks": [],
                "missing": [],
                "improvements": [],
                "good_points": []
            }
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            print(f"任務失敗 {task.task_id}: {e}")
    
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
