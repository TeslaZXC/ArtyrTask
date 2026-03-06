from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
import models, schemas, auth, database

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["members"])

async def require_owner(workspace_id: int, current_user: models.User, db: AsyncSession):
    """Only the workspace owner can manage members."""
    stmt = select(models.Workspace).where(models.Workspace.id == workspace_id)
    result = await db.execute(stmt)
    workspace = result.scalars().first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can manage members")
    return workspace

@router.get("/", response_model=List[schemas.WorkspaceMemberResponse])
async def get_members(
    workspace_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Allow any member (including owner) to see the member list
    stmt = select(models.WorkspaceMember).options(
        selectinload(models.WorkspaceMember.user)
    ).where(models.WorkspaceMember.workspace_id == workspace_id)
    result = await db.execute(stmt)
    members = result.scalars().all()

    # Check that requester has access
    is_owner_stmt = select(models.Workspace).where(
        models.Workspace.id == workspace_id,
        models.Workspace.owner_id == current_user.id
    )
    is_owner_res = await db.execute(is_owner_stmt)
    is_owner = is_owner_res.scalars().first() is not None
    is_member = any(m.user_id == current_user.id for m in members)

    if not is_owner and not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    return [
        schemas.WorkspaceMemberResponse(
            user_id=m.user_id,
            email=m.user.email,
            full_name=m.user.full_name,
            role=m.role
        )
        for m in members
    ]

@router.post("/", response_model=schemas.WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    workspace_id: int,
    data: schemas.WorkspaceMemberCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await require_owner(workspace_id, current_user, db)

    if data.role not in ("editor", "member"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'member'")

    # Find target user by email
    user_stmt = select(models.User).where(models.User.email == data.email)
    user_res = await db.execute(user_stmt)
    target_user = user_res.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User with this email not found")
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as member")

    # Check duplicate
    dup_stmt = select(models.WorkspaceMember).where(
        models.WorkspaceMember.workspace_id == workspace_id,
        models.WorkspaceMember.user_id == target_user.id
    )
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalars().first():
        raise HTTPException(status_code=400, detail="User is already a member")

    member = models.WorkspaceMember(workspace_id=workspace_id, user_id=target_user.id, role=data.role)
    db.add(member)
    
    ret_user_id = target_user.id
    ret_email = target_user.email
    ret_full_name = target_user.full_name
    ret_role = data.role
    
    await db.commit()

    return schemas.WorkspaceMemberResponse(
        user_id=ret_user_id,
        email=ret_email,
        full_name=ret_full_name,
        role=ret_role
    )

@router.put("/{user_id}", response_model=schemas.WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: int,
    user_id: int,
    data: schemas.WorkspaceMemberCreate,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await require_owner(workspace_id, current_user, db)

    if data.role not in ("editor", "member"):
        raise HTTPException(status_code=400, detail="Role must be 'editor' or 'member'")

    stmt = select(models.WorkspaceMember).options(
        selectinload(models.WorkspaceMember.user)
    ).where(
        models.WorkspaceMember.workspace_id == workspace_id,
        models.WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = data.role
    
    ret_user_id = member.user.id
    ret_email = member.user.email
    ret_full_name = member.user.full_name
    ret_role = member.role
    
    await db.commit()

    return schemas.WorkspaceMemberResponse(
        user_id=ret_user_id,
        email=ret_email,
        full_name=ret_full_name,
        role=ret_role
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: int,
    user_id: int,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    await require_owner(workspace_id, current_user, db)

    stmt = select(models.WorkspaceMember).where(
        models.WorkspaceMember.workspace_id == workspace_id,
        models.WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    await db.commit()
    return None
