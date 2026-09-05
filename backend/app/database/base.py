from sqlalchemy.orm import DeclarativeBase
import uuid

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Base(DeclarativeBase):
    pass
