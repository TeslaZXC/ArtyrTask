from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database
from routers.boards import get_workspace_role

router = APIRouter(prefix="/boards/{board_id}/lists", tags=["lists"])


async def get_board_role(board_id: int, user_id: int, db: AsyncSession):
    stmt = select(models.Board).options(selectinload(models.Board.workspace)).where(models.Board.id == board_id)
    result = await db.execute(stmt)
    board = result.scalars().first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    role = await get_workspace_role(board.workspace_id, user_id, db)
    return board, role


@router.get("/", response_model=List[schemas.ListResponse])
async def get_lists(
    board_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await get_board_role(board_id, current_user.id, db)
    stmt = select(models.List).where(models.List.board_id == board_id).order_by(models.List.position)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=schemas.ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    board_id: int,
    list_data: schemas.ListCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board, role = await get_board_role(board_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

    stmt = select(models.List).where(models.List.board_id == board_id).order_by(models.List.position.desc())
    result = await db.execute(stmt)
    last_list = result.scalars().first()
    new_position = (last_list.position + 1) if last_list else 0

    new_list = models.List(name=list_data.name, board_id=board_id, position=new_position)
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)

    # Broadcast real-time update
    from routers.websocket import broadcast_refresh
    await broadcast_refresh(board_id, "list")

    return new_list


list_router = APIRouter(prefix="/lists", tags=["lists"])


async def get_list_and_role(list_id: int, user_id: int, db: AsyncSession):
    stmt = select(models.List).options(
        selectinload(models.List.board).selectinload(models.Board.workspace)
    ).where(models.List.id == list_id)
    result = await db.execute(stmt)
    db_list = result.scalars().first()
    if not db_list:
        raise HTTPException(status_code=404, detail="List not found")
    role = await get_workspace_role(db_list.board.workspace_id, user_id, db)
    return db_list, role


@list_router.patch("/order", status_code=status.HTTP_200_OK)
async def update_lists_order(
    items: List[schemas.ListOrderUpdateItem],
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not items:
        return {"message": "No items provided"}

    for item in items:
        db_list, role = await get_list_and_role(item.id, current_user.id, db)
        if role not in ("owner", "editor"):
            raise HTTPException(status_code=403, detail="Editor or owner role required")
        db_list.position = item.position

    await db.commit()
    return {"message": "Order updated"}


@list_router.put("/{list_id}", response_model=schemas.ListResponse)
async def update_list(
    list_id: int,
    list_update: schemas.ListUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_list, role = await get_list_and_role(list_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

    if list_update.name is not None:
        db_list.name = list_update.name
    if list_update.position is not None:
        db_list.position = list_update.position

    await db.commit()
    await db.refresh(db_list)
    return db_list


@list_router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_list, role = await get_list_and_role(list_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")
    board_id = db_list.board_id
    await db.delete(db_list)
    await db.commit()

    from routers.websocket import broadcast_refresh
    await broadcast_refresh(board_id, "list")
    return None
