from app.crud.base import CRUDBase
from app.models.entity import Entity, Instance, User
from app.schemas.entity import EntityCreate, EntityUpdate, InstanceCreate, InstanceUpdate, UserCreate, UserUpdate

class CRUDEntity(CRUDBase[Entity, EntityCreate, EntityUpdate]):
    pass

class CRUDInstance(CRUDBase[Instance, InstanceCreate, InstanceUpdate]):
    pass

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    pass

entity = CRUDEntity(Entity)
instance = CRUDInstance(Instance)
user = CRUDUser(User)
