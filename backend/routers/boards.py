from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/workspaces/{workspace_id}/boards", tags=["boards"])


async def get_workspace_role(workspace_id: int, user_id: int, db: AsyncSession) -> str:
    """Returns 'owner', 'editor', or 'member'. Raises 403 if no access."""
    # Check if owner
    ws_stmt = select(models.Workspace).where(models.Workspace.id == workspace_id)
    ws_res = await db.execute(ws_stmt)
    workspace = ws_res.scalars().first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id == user_id:
        return "owner"

    # Check membership
    m_stmt = select(models.WorkspaceMember).where(
        models.WorkspaceMember.workspace_id == workspace_id,
        models.WorkspaceMember.user_id == user_id
    )
    m_res = await db.execute(m_stmt)
    member = m_res.scalars().first()
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")
    return member.role


async def require_editor(workspace_id: int, current_user: models.User, db: AsyncSession):
    role = await get_workspace_role(workspace_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")
    return role


@router.get("/", response_model=List[schemas.BoardResponse])
async def get_boards(
    workspace_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await get_workspace_role(workspace_id, current_user.id, db)  # any member can read
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
    await require_editor(workspace_id, current_user, db)

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


async def get_board_and_role(board_id: int, user_id: int, db: AsyncSession):
    stmt = select(models.Board).options(selectinload(models.Board.workspace)).where(models.Board.id == board_id)
    result = await db.execute(stmt)
    board = result.scalars().first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    role = await get_workspace_role(board.workspace_id, user_id, db)
    return board, role


@board_router.get("/{board_id}", response_model=schemas.BoardResponse)
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board, _ = await get_board_and_role(board_id, current_user.id, db)
    return board


@board_router.put("/{board_id}", response_model=schemas.BoardResponse)
async def update_board(
    board_id: int,
    board_update: schemas.BoardUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    board, role = await get_board_and_role(board_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Editor or owner role required")

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
    board, role = await get_board_and_role(board_id, current_user.id, db)
    if role not in ("owner", "editor"):
        raise HTTPException(status_code=403, detail="Only editors/owners can delete boards")
    await db.delete(board)
    await db.commit()
    return None
