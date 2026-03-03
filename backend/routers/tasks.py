from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os
import shutil
import uuid
import models, schemas, auth, database

router = APIRouter(prefix="/lists/{list_id}/tasks", tags=["tasks"])

async def verify_list_access_for_task(list_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.List).options(
        selectinload(models.List.board).selectinload(models.Board.workspace)
    ).where(models.List.id == list_id)
    result = await db.execute(stmt)
    db_list = result.scalars().first()
    
    if not db_list or db_list.board.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="List not found or access denied")
    return db_list

@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(
    list_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_list_access_for_task(list_id, current_user, db)
    stmt = select(models.Task).options(
        selectinload(models.Task.attachments),
        selectinload(models.Task.links)
    ).where(models.Task.list_id == list_id).order_by(models.Task.position)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    list_id: int,
    task_data: schemas.TaskCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_list_access_for_task(list_id, current_user, db)
    
    stmt = select(models.Task).where(models.Task.list_id == list_id).order_by(models.Task.position.desc())
    result = await db.execute(stmt)
    last_task = result.scalars().first()
    new_position = (last_task.position + 1) if last_task else 0
    
    new_task = models.Task(
        title=task_data.title, 
        description=task_data.description,
        is_completed=task_data.is_completed,
        list_id=list_id, 
        position=new_position
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

task_router = APIRouter(prefix="/tasks", tags=["tasks"])

async def verify_task_access(task_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.Task).options(
        selectinload(models.Task.list).selectinload(models.List.board).selectinload(models.Board.workspace)
    ).where(models.Task.id == task_id)
    result = await db.execute(stmt)
    db_task = result.scalars().first()
    
    if not db_task or db_task.list.board.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found or access denied")
    return db_task

@task_router.patch("/order", status_code=status.HTTP_200_OK)
async def update_tasks_order(
    items: List[schemas.TaskOrderUpdateItem],
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not items:
        return {"message": "No items provided"}
        
    for item in items:
        db_task = await verify_task_access(item.id, current_user, db)
        await verify_list_access_for_task(item.list_id, current_user, db)
        db_task.position = item.position
        db_task.list_id = item.list_id
        
    await db.commit()
    return {"message": "Order updated"}

@task_router.get("/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.Task).options(
        selectinload(models.Task.attachments),
        selectinload(models.Task.links)
    ).where(models.Task.id == task_id)
    result = await db.execute(stmt)
    db_task = result.scalars().first()
    
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await verify_task_access(task_id, current_user, db)
    return db_task

@task_router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = await verify_task_access(task_id, current_user, db)
    
    if task_update.title is not None:
        db_task.title = task_update.title
    if task_update.description is not None:
        db_task.description = task_update.description
    if task_update.is_completed is not None:
        db_task.is_completed = task_update.is_completed
    if task_update.list_id is not None:
        await verify_list_access_for_task(task_update.list_id, current_user, db)
        db_task.list_id = task_update.list_id
    if task_update.position is not None:
        db_task.position = task_update.position
        
    await db.commit()
    await db.refresh(db_task)
    
    stmt = select(models.Task).options(
        selectinload(models.Task.attachments),
        selectinload(models.Task.links)
    ).where(models.Task.id == task_id)
    result = await db.execute(stmt)
    return result.scalars().first()

@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_task = await verify_task_access(task_id, current_user, db)
    await db.delete(db_task)
    await db.commit()
    return None

@task_router.post("/{task_id}/attachments", response_model=schemas.TaskAttachmentResponse)
async def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_task_access(task_id, current_user, db)
    
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"uploads/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    attachment = models.TaskAttachment(
        task_id=task_id,
        file_path=f"/{file_path}",
        file_name=file.filename
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment

@task_router.post("/{task_id}/links", response_model=schemas.TaskLinkResponse)
async def add_link(
    task_id: int,
    link: schemas.TaskLinkCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_task_access(task_id, current_user, db)
    
    new_link = models.TaskLink(
        task_id=task_id,
        url=link.url,
        title=link.title
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link
    
@task_router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.TaskAttachment).where(models.TaskAttachment.id == attachment_id)
    result = await db.execute(stmt)
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    await verify_task_access(attachment.task_id, current_user, db)
    
    try:
        os.remove(attachment.file_path.lstrip("/"))
    except OSError:
        pass
        
    await db.delete(attachment)
    await db.commit()
    return None

@task_router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.TaskLink).where(models.TaskLink.id == link_id)
    result = await db.execute(stmt)
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
        
    await verify_task_access(link.task_id, current_user, db)
        
    await db.delete(link)
    await db.commit()
    return None
