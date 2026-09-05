import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database.session import get_db, SessionLocal
from app.database.models.workflow import Workflow, WorkflowStatus
from app.agents.supervisor.agent import SupervisorAgent
from app.api.auth import get_current_user
from app.core.logging import get_logger

logger = get_logger('api.chat')
router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

async def run_workflow_bg(workflow_id: str, query: str, merchant_id: str, conversation_id: str):
    """Asynchronous background worker executing multi-agent DAG and emitting SSE events."""
    db = SessionLocal()
    try:
        agent = SupervisorAgent(db, merchant_id)
        async for _ in agent.run_workflow(query, merchant_id, conversation_id, workflow_id):
            pass
        logger.info(f"Workflow {workflow_id} background execution completed successfully.")
    except Exception as e:
        logger.error(f"Background execution failed for workflow {workflow_id}: {e}", exc_info=True)
        try:
            wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if wf:
                wf.status = WorkflowStatus.failed
                wf.error = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

@router.post('/chat')
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Intake endpoint for merchant natural language questions and problem statements.
    Initializes workflow in database and kicks off asynchronous multi-agent supervisor.
    """
    if not user.merchant_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Merchant onboarding required before initiating multi-agent intelligence analysis. Please complete onboarding at /onboarding."
        )

    conversation_id = req.conversation_id or str(uuid.uuid4())
    
    workflow = Workflow(
        merchant_id=user.merchant_id,
        user_query=req.query,
        conversation_id=conversation_id,
        status=WorkflowStatus.initializing
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Launch async task
    asyncio.create_task(run_workflow_bg(workflow.id, req.query, user.merchant_id, conversation_id))

    return {
        'workflow_id': workflow.id,
        'conversation_id': conversation_id,
        'status': 'running'
    }
