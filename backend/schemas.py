from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    code: str

class RequestCode(BaseModel):
    email: EmailStr

class VerifyRegisterCode(BaseModel):
    email: EmailStr
    code: str
    password: str
    full_name: Optional[str] = None

class ResetPassword(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(WorkspaceBase):
    pass

class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    member_role: Optional[str] = None  # current user's role: 'owner'|'editor'|'member'

    class Config:
        from_attributes = True

class WorkspaceMemberCreate(BaseModel):
    email: str
    role: str = "member"  # "editor" or "member"

class WorkspaceMemberResponse(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

class BoardBase(BaseModel):
    name: str

class BoardCreate(BoardBase):
    pass

class BoardUpdate(BoardBase):
    position: Optional[int] = None

class BoardResponse(BoardBase):
    id: int
    workspace_id: int
    position: int
    created_at: datetime

    class Config:
        from_attributes = True

class ListBase(BaseModel):
    name: str

class ListCreate(ListBase):
    pass

class ListUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None

class ListOrderUpdateItem(BaseModel):
    id: int
    position: int

class ListResponse(ListBase):
    id: int
    board_id: int
    position: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaskAttachmentResponse(BaseModel):
    id: int
    task_id: int
    file_path: str
    file_name: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class TaskLinkCreate(BaseModel):
    url: str
    title: Optional[str] = None

class TaskLinkResponse(TaskLinkCreate):
    id: int
    task_id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_completed: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    list_id: Optional[int] = None
    position: Optional[int] = None
    color: Optional[str] = None

class TaskOrderUpdateItem(BaseModel):
    id: int
    list_id: int
    position: int

class TaskResponse(TaskBase):
    id: int
    list_id: int
    position: int
    color: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    attachments: List[TaskAttachmentResponse] = []
    links: List[TaskLinkResponse] = []

    class Config:
        from_attributes = True
