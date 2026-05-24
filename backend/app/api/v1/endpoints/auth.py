"""用户认证端点：注册、登录、获取当前用户、验证码、报价历史、修改密码"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.captcha import check_rate_limit, generate_captcha, verify_captcha
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import QuoteRecord, User
from app.models.auth import (
    CaptchaResponse,
    ChangePasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.models.quote import QuoteRecordDetail, QuoteRecordItem, QuoteRecordListResponse

router = APIRouter()


@router.get("/auth/captcha", response_model=CaptchaResponse)
async def get_captcha():
    """获取图片验证码"""
    captcha_id, captcha_image = generate_captcha()
    return CaptchaResponse(captcha_id=captcha_id, captcha_image=captcha_image)


@router.post("/auth/register", response_model=TokenResponse)
async def register(body: UserRegister, request: Request, db: Session = Depends(get_db)):
    """注册新用户，返回 JWT"""
    # IP 频率限制
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    # 验证码校验
    verify_captcha(body.captcha_id, body.captcha_code)

    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致",
        )

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被占用",
        )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=_user_response(user),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: UserLogin, db: Session = Depends(get_db)):
    """用户名+密码登录，返回 JWT"""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    token = create_access_token(data={"sub": user.username, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=_user_response(user),
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前认证用户信息"""
    return _user_response(current_user)


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _record_to_item(record: QuoteRecord) -> QuoteRecordItem:
    return QuoteRecordItem(
        id=record.id,
        filename=record.filename,
        process=record.process,
        material=record.material,
        quantity=record.quantity,
        status=record.status,
        unit_price=record.unit_price,
        total_price=record.total_price,
        created_at=record.created_at,
    )


# ==================== 报价历史 ====================

@router.get("/auth/quotes", response_model=QuoteRecordListResponse)
async def list_quote_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的报价记录（管理员可查看所有）"""
    query = db.query(QuoteRecord)
    if current_user.role != "admin":
        query = query.filter(QuoteRecord.user_id == current_user.id)

    total = query.count()
    records = (
        query.order_by(QuoteRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return QuoteRecordListResponse(
        total=total,
        page=page,
        page_size=page_size,
        records=[_record_to_item(r) for r in records],
    )


@router.get("/auth/quotes/{record_id}", response_model=QuoteRecordDetail)
async def get_quote_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取报价记录详情"""
    record = db.query(QuoteRecord).filter(QuoteRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报价记录不存在")
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此记录")

    return QuoteRecordDetail(
        id=record.id,
        filename=record.filename,
        process=record.process,
        material=record.material,
        quantity=record.quantity,
        status=record.status,
        unit_price=record.unit_price,
        total_price=record.total_price,
        created_at=record.created_at,
        quality=record.quality,
        delivery=record.delivery,
        post_processing=record.post_processing,
        material_cost=record.material_cost,
        time_cost=record.time_cost,
        post_process_cost=record.post_process_cost,
        delivery_surcharge=record.delivery_surcharge,
        difficulty_surcharge=record.difficulty_surcharge,
        support_cost=record.support_cost,
        quantity_discount=record.quantity_discount,
        volume_mm3=record.volume_mm3,
        surface_area_mm2=record.surface_area_mm2,
        bounding_box=record.bounding_box,
        file_size_bytes=record.file_size_bytes,
        print_time_seconds=record.print_time_seconds,
        filament_used_grams=record.filament_used_grams,
        processing_time_seconds=record.processing_time_seconds,
    )


@router.delete("/auth/quotes/{record_id}")
async def delete_quote_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除报价记录"""
    record = db.query(QuoteRecord).filter(QuoteRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="报价记录不存在")
    if current_user.role != "admin" and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此记录")

    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


# ==================== 修改密码 ====================

@router.put("/auth/password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户密码"""
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的新密码不一致",
        )

    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "密码修改成功"}
