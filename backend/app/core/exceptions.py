from fastapi import HTTPException, status

class MerchantNotFoundError(HTTPException):
    def __init__(self, merchant_id: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'Merchant {merchant_id} not found')

class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = 'Not authorized to access this resource'):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class PolicyRejectionError(HTTPException):
    def __init__(self, reason: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'Policy rejected action: {reason}')

class DuplicateActionError(HTTPException):
    def __init__(self, idempotency_key: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f'Action already executed. Idempotency key: {idempotency_key}')

class AgentExecutionError(HTTPException):
    def __init__(self, agent: str, error: str):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Agent {agent} failed: {error}')

class WorkflowNotFoundError(HTTPException):
    def __init__(self, workflow_id: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f'Workflow {workflow_id} not found')
