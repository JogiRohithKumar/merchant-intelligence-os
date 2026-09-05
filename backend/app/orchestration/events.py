import asyncio
from typing import AsyncGenerator, Dict, List, Optional
from app.schemas.workflow import WorkflowEvent, WorkflowEventType
from app.core.logging import get_logger

logger = get_logger('orchestration.events')

class EventBroadcaster:
    """
    Thread-safe, workflow-scoped event broadcaster for SSE streaming.
    Maintains workflow history for late-joining subscribers and ensures merchant isolation.
    """
    def __init__(self):
        self.listeners: Dict[str, List[asyncio.Queue]] = {}
        self.history: Dict[str, List[WorkflowEvent]] = {}
        self._lock = asyncio.Lock()

    def emit(self, workflow_id: str, event: WorkflowEvent):
        """Emits an event to a specific workflow stream and stores in memory history."""
        if workflow_id not in self.history:
            self.history[workflow_id] = []
        self.history[workflow_id].append(event)

        queues = self.listeners.get(workflow_id, [])
        for queue in queues:
            try:
                queue.put_nowait(event)
            except Exception as e:
                logger.warning(f"Failed to queue event for workflow {workflow_id}: {e}")

    async def broadcast(self, event: WorkflowEvent):
        """Backward compatibility broadcast."""
        workflow_id = event.workflow_id
        self.emit(workflow_id, event)

    async def stream(self, workflow_id: str, timeout_seconds: float = 120.0) -> AsyncGenerator[WorkflowEvent, None]:
        """
        Yields workflow events to SSE client.
        First replays historical events for the workflow, then waits for real-time events.
        """
        queue = asyncio.Queue()

        async with self._lock:
            if workflow_id not in self.listeners:
                self.listeners[workflow_id] = []
            self.listeners[workflow_id].append(queue)

            # Replay existing events for this workflow
            past_events = list(self.history.get(workflow_id, []))

        # Yield historical events first
        for past_event in past_events:
            yield past_event
            if past_event.event_type in [WorkflowEventType.WORKFLOW_COMPLETED, WorkflowEventType.WORKFLOW_FAILED]:
                # Workflow already completed
                return

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                    yield event
                    if event.event_type in [WorkflowEventType.WORKFLOW_COMPLETED, WorkflowEventType.WORKFLOW_FAILED]:
                        break
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield WorkflowEvent(
                        event_type=WorkflowEventType.STREAM_CLOSED,
                        workflow_id=workflow_id,
                        agent='system',
                        message='Stream timed out due to inactivity.'
                    )
                    break
        finally:
            async with self._lock:
                if workflow_id in self.listeners and queue in self.listeners[workflow_id]:
                    self.listeners[workflow_id].remove(queue)
                if workflow_id in self.listeners and not self.listeners[workflow_id]:
                    del self.listeners[workflow_id]

event_broadcaster = EventBroadcaster()
