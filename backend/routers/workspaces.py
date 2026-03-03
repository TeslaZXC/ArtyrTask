from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.get("/", response_model=List[schemas.WorkspaceResponse])
async def get_workspaces(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.Workspace).where(models.Workspace.owner_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/", response_model=schemas.WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace: schemas.WorkspaceCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_workspace = models.Workspace(name=workspace.name, owner_id=current_user.id)
    db.add(new_workspace)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace

@router.put("/{workspace_id}", response_model=schemas.WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace: schemas.WorkspaceUpdate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.Workspace).where(
        models.Workspace.id == workspace_id,
        models.Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    db_workspace = result.scalars().first()
    
    if not db_workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    db_workspace.name = workspace.name
    await db.commit()
    await db.refresh(db_workspace)
    return db_workspace

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    stmt = select(models.Workspace).where(
        models.Workspace.id == workspace_id,
        models.Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    db_workspace = result.scalars().first()
    
    if not db_workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    await db.delete(db_workspace)
    await db.commit()
    return None
