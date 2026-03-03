from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/boards/{board_id}/lists", tags=["lists"])

async def verify_board_access_for_list(board_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.Board).options(selectinload(models.Board.workspace)).where(models.Board.id == board_id)
    result = await db.execute(stmt)
    board = result.scalars().first()
    if not board or board.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Board not found or access denied")
    return board

@router.get("/", response_model=List[schemas.ListResponse])
async def get_lists(
    board_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_board_access_for_list(board_id, current_user, db)
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
    await verify_board_access_for_list(board_id, current_user, db)
    
    stmt = select(models.List).where(models.List.board_id == board_id).order_by(models.List.position.desc())
    result = await db.execute(stmt)
    last_list = result.scalars().first()
    new_position = (last_list.position + 1) if last_list else 0
    
    new_list = models.List(name=list_data.name, board_id=board_id, position=new_position)
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    return new_list

list_router = APIRouter(prefix="/lists", tags=["lists"])

async def verify_list_access(list_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.List).options(
        selectinload(models.List.board).selectinload(models.Board.workspace)
    ).where(models.List.id == list_id)
    result = await db.execute(stmt)
    db_list = result.scalars().first()
    
    if not db_list or db_list.board.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="List not found or access denied")
    return db_list

@list_router.patch("/order", status_code=status.HTTP_200_OK)
async def update_lists_order(
    items: List[schemas.ListOrderUpdateItem],
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not items:
        return {"message": "No items provided"}
        
    for item in items:
        db_list = await verify_list_access(item.id, current_user, db)
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
    db_list = await verify_list_access(list_id, current_user, db)
    
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
    db_list = await verify_list_access(list_id, current_user, db)
    await db.delete(db_list)
    await db.commit()
    return None
