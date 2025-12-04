from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class ResponseBase(BaseModel):
    pass
