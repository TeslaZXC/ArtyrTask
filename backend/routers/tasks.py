from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import os, shutil, uuid
import models, schemas, auth, database
from routers.boards import get_workspace_role

router = APIRouter(prefix="/lists/{list_id}/tasks", tags=["tasks"])


async def get_list_with_workspace(list_id: int, db: AsyncSession):
    stmt = select(models.List).options(
        selectinload(models.List.board).selectinload(models.Board.workspace)
    ).where(models.List.id == list_id)
    result = await db.execute(stmt)
    db_list = result.scalars().first()
    if not db_list:
        raise HTTPException(status_code=404, detail="List not found")
    return db_list


@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(
    list_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_list = await get_list_with_workspace(list_id, db)
    await get_workspace_role(db_list.board.workspace_id, current_user.id, db)
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
    db_list = await get_list_with_workspace(list_id, db)
    role = await get_workspace_role(db_list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

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
    
    board_id = db_list.board_id
    
    await db.commit()
    await db.refresh(new_task)

    from routers.websocket import broadcast_refresh
    await broadcast_refresh(board_id, "task")

    return new_task


task_router = APIRouter(prefix="/tasks", tags=["tasks"])


async def get_task_with_workspace(task_id: int, db: AsyncSession):
    stmt = select(models.Task).options(
        selectinload(models.Task.list).selectinload(models.List.board).selectinload(models.Board.workspace),
        selectinload(models.Task.attachments),
        selectinload(models.Task.links)
    ).where(models.Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@task_router.patch("/order", status_code=status.HTTP_200_OK)
async def update_tasks_order(
    items: List[schemas.TaskOrderUpdateItem],
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not items:
        return {"message": "No items provided"}

    board_ids = set()
    for item in items:
        task = await get_task_with_workspace(item.id, db)
        role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
        if role not in ("owner", "editor"):
            raise HTTPException(status_code=403, detail="Editor or owner role required")
        task.position = item.position
        task.list_id = item.list_id
        board_ids.add(task.list.board_id)

    await db.commit()

    from routers.websocket import broadcast_refresh
    for board_id in board_ids:
        await broadcast_refresh(board_id, "task")

    return {"message": "Order updated"}


@task_router.get("/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await get_task_with_workspace(task_id, db)
    await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    return task


@task_router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await get_task_with_workspace(task_id, db)
    workspace_id = task.list.board.workspace_id
    board_id = task.list.board_id
    role = await get_workspace_role(workspace_id, current_user.id, db)

    # Members can only toggle is_completed
    if role == "member":
        allowed_fields = {k for k, v in task_update.model_dump(exclude_none=True).items()}
        # Only is_completed is allowed for members
        if allowed_fields - {"is_completed"}:
            raise HTTPException(status_code=403, detail="Members can only change task completion status")

    if task_update.title is not None:
        task.title = task_update.title
    if task_update.description is not None:
        task.description = task_update.description
    if task_update.is_completed is not None:
        task.is_completed = task_update.is_completed
    if task_update.color is not None:
        task.color = task_update.color if task_update.color else None
    if task_update.list_id is not None:
        task.list_id = task_update.list_id
    if task_update.position is not None:
        task.position = task_update.position

    await db.commit()
    await db.refresh(task)

    # Reload with relations
    stmt = select(models.Task).options(
        selectinload(models.Task.attachments),
        selectinload(models.Task.links)
    ).where(models.Task.id == task_id)
    result = await db.execute(stmt)
    updated = result.scalars().first()

    from routers.websocket import broadcast_refresh
    await broadcast_refresh(board_id, "task")

    return updated


@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await get_task_with_workspace(task_id, db)
    role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")
    board_id = task.list.board_id
    await db.delete(task)
    await db.commit()

    from routers.websocket import broadcast_refresh
    await broadcast_refresh(board_id, "task")
    return None


@task_router.post("/{task_id}/attachments", response_model=schemas.TaskAttachmentResponse)
async def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    task = await get_task_with_workspace(task_id, db)
    role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

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
    task = await get_task_with_workspace(task_id, db)
    role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

    new_link = models.TaskLink(task_id=task_id, url=link.url, title=link.title)
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

    task = await get_task_with_workspace(attachment.task_id, db)
    role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

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

    task = await get_task_with_workspace(link.task_id, db)
    role = await get_workspace_role(task.list.board.workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

    await db.delete(link)
    await db.commit()
    return None
