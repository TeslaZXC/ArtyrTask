from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=List[schemas.WorkspaceResponse])
async def get_workspaces(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Get workspaces where user is owner
    owned_stmt = select(models.Workspace).where(models.Workspace.owner_id == current_user.id)
    owned_result = await db.execute(owned_stmt)
    owned = owned_result.scalars().all()

    # Get workspaces where user is a member
    member_stmt = select(models.WorkspaceMember).options(
        selectinload(models.WorkspaceMember.workspace)
    ).where(models.WorkspaceMember.user_id == current_user.id)
    member_result = await db.execute(member_stmt)
    memberships = member_result.scalars().all()

    # Build unified list with role info
    result_list = []
    for ws in owned:
        r = schemas.WorkspaceResponse(
            id=ws.id, name=ws.name, owner_id=ws.owner_id,
            created_at=ws.created_at, member_role="owner"
        )
        result_list.append(r)

    for m in memberships:
        ws = m.workspace
        r = schemas.WorkspaceResponse(
            id=ws.id, name=ws.name, owner_id=ws.owner_id,
            created_at=ws.created_at, member_role=m.role
        )
        result_list.append(r)

    return result_list


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
    r = schemas.WorkspaceResponse(
        id=new_workspace.id, name=new_workspace.name, owner_id=new_workspace.owner_id,
        created_at=new_workspace.created_at, member_role="owner"
    )
    return r


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
    return schemas.WorkspaceResponse(
        id=db_workspace.id, name=db_workspace.name, owner_id=db_workspace.owner_id,
        created_at=db_workspace.created_at, member_role="owner"
    )


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
