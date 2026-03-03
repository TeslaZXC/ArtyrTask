from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/workspaces/{workspace_id}/boards", tags=["boards"])

async def verify_workspace_access(workspace_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.Workspace).where(models.Workspace.id == workspace_id, models.Workspace.owner_id == current_user.id)
    result = await db.execute(stmt)
    workspace = result.scalars().first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    return workspace

@router.get("/", response_model=List[schemas.BoardResponse])
async def get_boards(
    workspace_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_workspace_access(workspace_id, current_user, db)
    stmt = select(models.Board).where(models.Board.workspace_id == workspace_id).order_by(models.Board.position)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=schemas.BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    workspace_id: int,
    board: schemas.BoardCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await verify_workspace_access(workspace_id, current_user, db)
    
    # Get max position
    stmt = select(models.Board).where(models.Board.workspace_id == workspace_id).order_by(models.Board.position.desc())
    result = await db.execute(stmt)
    last_board = result.scalars().first()
    new_position = (last_board.position + 1) if last_board else 0
    
    new_board = models.Board(name=board.name, workspace_id=workspace_id, position=new_position)
    db.add(new_board)
    await db.commit()
    await db.refresh(new_board)
    return new_board

board_router = APIRouter(prefix="/boards", tags=["boards"])

async def verify_board_access(board_id: int, current_user: models.User, db: AsyncSession):
    stmt = select(models.Board).options(selectinload(models.Board.workspace)).where(models.Board.id == board_id)
    result = await db.execute(stmt)
    board = result.scalars().first()
    if not board or board.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Board not found or access denied")
    return board

@board_router.get("/{board_id}", response_model=schemas.BoardResponse)
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = await verify_board_access(board_id, current_user, db)
    return board

@board_router.put("/{board_id}", response_model=schemas.BoardResponse)
async def update_board(
    board_id: int,
    board_update: schemas.BoardUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = await verify_board_access(board_id, current_user, db)
    
    if board_update.name is not None:
        board.name = board_update.name
    if board_update.position is not None:
        board.position = board_update.position
        
    await db.commit()
    await db.refresh(board)
    return board

@board_router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board = await verify_board_access(board_id, current_user, db)
    await db.delete(board)
    await db.commit()
    return None
