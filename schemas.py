from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    username: str
    password: str

class TaskCreate(BaseModel):
    title: str

class TaskResponse(BaseModel):
    id:int
    title: str
    completed: bool
    owner_id: int

    # class Config:
    #    orm_mode = True

    # Pydantic v2 replaces 'class Config' with 'model_config'
    model_config = ConfigDict(from_attributes=True) 