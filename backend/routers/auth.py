from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models, schemas, auth, database, email_utils
import random
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["auth"])

def generate_code():
    return str(random.randint(100000, 999999))

@router.post("/request-register-code")
async def request_register_code(request: schemas.RequestCode, db: AsyncSession = Depends(database.get_db)):
    stmt = select(models.User).where(models.User.email == request.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    verification_code = models.VerificationCode(
        email=request.email,
        code=code,
        expires_at=expires_at,
        purpose="register"
    )
    db.add(verification_code)
    await db.commit()
    
    email_utils.send_verification_email(request.email, code, "register")
    return {"message": "Verification code sent if email is valid."}

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.VerifyRegisterCode, db: AsyncSession = Depends(database.get_db)):
    stmt = select(models.VerificationCode).where(
        models.VerificationCode.email == user.email,
        models.VerificationCode.purpose == "register",
        models.VerificationCode.code == user.code,
        models.VerificationCode.expires_at > datetime.now(timezone.utc)
    ).order_by(models.VerificationCode.created_at.desc())
    
    result = await db.execute(stmt)
    code_record = result.scalars().first()
    
    if not code_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
    stmt_user = select(models.User).where(models.User.email == user.email)
    res_user = await db.execute(stmt_user)
    if res_user.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(new_user)
    
    await db.delete(code_record)
    
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(database.get_db)):
    stmt = select(models.User).where(models.User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    refresh_token = auth.create_refresh_token(data={"sub": user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/request-reset-code")
async def request_reset_code(request: schemas.RequestCode, db: AsyncSession = Depends(database.get_db)):
    stmt = select(models.User).where(models.User.email == request.email)
    result = await db.execute(stmt)
    if not result.scalars().first():
        return {"message": "If the email is registered, a reset code was sent."}
        
    code = generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    verification_code = models.VerificationCode(
        email=request.email,
        code=code,
        expires_at=expires_at,
        purpose="reset"
    )
    db.add(verification_code)
    await db.commit()
    
    email_utils.send_verification_email(request.email, code, "reset")
    return {"message": "If the email is registered, a reset code was sent."}

@router.post("/reset-password")
async def reset_password(request: schemas.ResetPassword, db: AsyncSession = Depends(database.get_db)):
    stmt = select(models.VerificationCode).where(
        models.VerificationCode.email == request.email,
        models.VerificationCode.purpose == "reset",
        models.VerificationCode.code == request.code,
        models.VerificationCode.expires_at > datetime.now(timezone.utc)
    ).order_by(models.VerificationCode.created_at.desc())
    
    result = await db.execute(stmt)
    code_record = result.scalars().first()
    
    if not code_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        
    stmt_user = select(models.User).where(models.User.email == request.email)
    res_user = await db.execute(stmt_user)
    user = res_user.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = auth.get_password_hash(request.new_password)
    await db.delete(code_record)
    
    await db.commit()
    return {"message": "Password updated successfully."}

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(token: str, db: AsyncSession = Depends(database.get_db)):
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except auth.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    stmt = select(models.User).where(models.User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    access_token = auth.create_access_token(data={"sub": user.email})
    new_refresh_token = auth.create_refresh_token(data={"sub": user.email})
    
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
