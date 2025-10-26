import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    def __init__(self, task_id: str, url: str):
        self.task_id = task_id
        self.url = url
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.completed_at = None
    
    def update_status(self, status: TaskStatus):
        self.status = status
        self.updated_at = datetime.now()
        if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
            self.completed_at = datetime.now()
    
    def set_result(self, result: Dict):
        self.result = result
        self.update_status(TaskStatus.COMPLETED)
    
    def set_error(self, error: str):
        self.error = error
        self.error = error
        self.update_status(TaskStatus.FAILED)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class TaskManager:
    def __init__(self, max_tasks: int = 1000):
        self.tasks: Dict[str, Task] = {}
        self.max_tasks = max_tasks
        self._lock = asyncio.Lock()
    
    def generate_task_id(self) -> str:
        return str(uuid.uuid4())
    
    async def create_task(self, url: str) -> str:
        async with self._lock:
            task_id = self.generate_task_id()
            task = Task(task_id, url)
            self.tasks[task_id] = task
            
            # Limpiar tareas antiguas si hay demasiadas
            await self._cleanup_old_tasks()
            
            logger.info(f"Tarea creada: {task_id} para URL: {url}")
            return task_id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        async with self._lock:
            return self.tasks.get(task_id)
    
    async def update_task_status(self, task_id: str, status: TaskStatus):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.update_status(status)
                logger.info(f"Tarea {task_id} actualizada a estado: {status.value}")
    
    async def set_task_result(self, task_id: str, result: Dict):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.set_result(result)
                logger.info(f"Tarea {task_id} completada exitosamente")
    
    async def set_task_error(self, task_id: str, error: str):
        async with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.set_error(error)
                logger.error(f"Tarea {task_id} falló: {error}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "url": task.url,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
    
    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                return {"error": task.error, "status": "failed"}
            else:
                return {"status": task.status.value, "message": "Task not completed yet"}
    
    async def _cleanup_old_tasks(self):
        if len(self.tasks) > self.max_tasks:
            # Ordenar por fecha de actualización
            sorted_tasks = sorted(
                self.tasks.items(),
                key=lambda x: x[1].updated_at
            )
            
            # Eliminar las más antiguas
            to_remove = len(self.tasks) - self.max_tasks
            for task_id, _ in sorted_tasks[:to_remove]:
                del self.tasks[task_id]
                logger.debug(f"Tarea antigua eliminada: {task_id}")
    
    async def get_all_tasks(self) -> Dict[str, Dict]:
        async with self._lock:
            return {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
    
    async def count_tasks_by_status(self) -> Dict[str, int]:
        async with self._lock:
            counts = {status.value: 0 for status in TaskStatus}
            for task in self.tasks.values():
                counts[task.status.value] += 1
            return counts