from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.database import get_db
from backend.app.models.models import User, Vendor
from backend.app.schemas.schemas import UserLogin, UserRegister, Token, UserResponse
from backend.app.utils.security import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class DemoLoginRequest(BaseModel):
    role: str = "Procurement Officer"  # "Procurement Officer", "Company / Vendor", or "Admin"

from typing import Optional

def resolve_vendor_id(db: Session, user: User) -> Optional[int]:
    if user.role != "Company / Vendor" and not user.company_name:
        return None
    # 1. Match by contact email
    v = db.query(Vendor).filter(Vendor.contact_email == user.email).first()
    if v:
        return v.id
    # 2. Match by company_name
    if user.company_name:
        v = db.query(Vendor).filter(Vendor.name.ilike(f"%{user.company_name.strip()}%")).first()
        if v:
            return v.id
    # 3. Default to first vendor for demo
    first_v = db.query(Vendor).first()
    return first_v.id if first_v else None

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Normalize role
    role = "Company / Vendor" if ("company" in user_in.role.lower() or "vendor" in user_in.role.lower()) else "Procurement Officer"
    company_name = user_in.company_name if role == "Company / Vendor" else None

    # If registering as a company/vendor and company_name is provided, ensure a Vendor profile exists
    if role == "Company / Vendor" and company_name:
        existing_vendor = db.query(Vendor).filter(Vendor.name.ilike(company_name.strip())).first()
        if not existing_vendor:
            pan_val = user_in.pan or (user_in.gstin[2:12] if user_in.gstin and len(user_in.gstin) >= 12 else None)
            new_vendor = Vendor(
                name=company_name.strip(),
                legal_name=company_name.strip(),
                gstin=user_in.gstin,
                pan=pan_val,
                contact_email=user_in.email.strip().lower(),
                verification_status="Pending"
            )
            db.add(new_vendor)
            db.commit()

    user = User(
        email=user_in.email.strip().lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=role,
        company_name=company_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    v_id = resolve_vendor_id(db, user)
    token = create_access_token(data={"sub": user.email, "role": user.role, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "company_name": user.company_name,
        "vendor_id": v_id
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.strip().lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    v_id = resolve_vendor_id(db, user)
    token = create_access_token(data={"sub": user.email, "role": user.role, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "company_name": user.company_name,
        "vendor_id": v_id
    }

@router.post("/demo-login", response_model=Token)
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    req_role = req.role.lower()
    if "company" in req_role or "vendor" in req_role:
        target_role = "Company / Vendor"
    elif "admin" in req_role:
        target_role = "Admin"
    else:
        target_role = "Procurement Officer"

    user = db.query(User).filter(User.role == target_role).first()
    if not user:
        # Create on demand if not present
        if target_role == "Company / Vendor":
            user = User(
                email="vendor@alphalogix.com",
                hashed_password=get_password_hash("vendor123"),
                full_name="Vikram Mehta",
                role="Company / Vendor",
                company_name="Alpha Logix Solutions Private Limited"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user = db.query(User).first()
            if not user:
                raise HTTPException(status_code=404, detail="No demo users available.")

    v_id = resolve_vendor_id(db, user)
    token = create_access_token(data={"sub": user.email, "role": user.role, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "company_name": user.company_name,
        "vendor_id": v_id
    }

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    v_id = resolve_vendor_id(db, current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company_name": current_user.company_name,
        "vendor_id": v_id,
        "created_at": current_user.created_at
    }
