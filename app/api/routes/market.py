import datetime
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user, get_db
from app.db.models import MarketProduct, User
from app.schemas.market import (
    MarketProductCreate,
    MarketProductListResponse,
    MarketProductResponse,
    MarketProductUpdate,
)


router = APIRouter(tags=["market"])

UPLOAD_ROOT = "uploads"
MARKET_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, "market")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_MARKET_STATUS = {"on_sale", "sold", "off_shelf"}
MAX_PAGE_SIZE = 100


def _safe_remove_market_upload(path_or_url: str | None) -> bool:
    if not path_or_url:
        return False

    raw = path_or_url.strip()
    if not raw:
        return False

    normalized = raw.replace("\\", "/")
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return False

    relative = normalized.lstrip("/")
    if relative.startswith("uploads/"):
        relative = relative[len("uploads/") :]
    if not relative.startswith("market/"):
        return False

    candidate = os.path.abspath(os.path.join(UPLOAD_ROOT, relative))
    allowed_root = os.path.abspath(MARKET_UPLOAD_DIR)
    if not (candidate == allowed_root or candidate.startswith(allowed_root + os.sep)):
        return False
    if not os.path.isfile(candidate):
        return False

    try:
        os.remove(candidate)
        return True
    except OSError:
        return False


def _serialize_market_product(product: MarketProduct, current_user: User) -> MarketProductResponse:
    seller = getattr(product, "seller", None)
    seller_name = (seller.real_name or seller.username) if seller else None
    can_manage = current_user.role == "admin" or product.seller_id == current_user.id

    return MarketProductResponse(
        id=product.id,
        title=product.title,
        description=product.description,
        price=product.price,
        location=product.location,
        contact_info=product.contact_info,
        image_url=product.image_url,
        seller_id=product.seller_id,
        seller_name=seller_name,
        status=product.status,
        view_count=product.view_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
        can_edit=can_manage,
        can_delete=can_manage,
    )


@router.get("/api/market/products", response_model=MarketProductListResponse)
async def get_market_products(
    search: Optional[str] = None,
    status: Optional[str] = None,
    mine: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于等于 1")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size 必须在 1 到 {MAX_PAGE_SIZE} 之间")

    query = db.query(MarketProduct).options(joinedload(MarketProduct.seller))

    if mine:
        query = query.filter(MarketProduct.seller_id == current_user.id)
    else:
        if status:
            if status not in ALLOWED_MARKET_STATUS:
                raise HTTPException(status_code=400, detail="无效的商品状态")
            query = query.filter(MarketProduct.status == status)
        else:
            query = query.filter(MarketProduct.status == "on_sale")

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (MarketProduct.title.like(pattern))
            | (MarketProduct.description.like(pattern))
            | (MarketProduct.location.like(pattern))
        )

    total = query.count()
    items = (
        query.order_by(desc(MarketProduct.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [_serialize_market_product(item, current_user) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/api/market/products/{product_id}", response_model=MarketProductResponse)
async def get_market_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(MarketProduct)
        .options(joinedload(MarketProduct.seller))
        .filter(MarketProduct.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if product.status != "on_sale" and current_user.role != "admin" and product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看该商品")

    product.view_count = (product.view_count or 0) + 1
    db.commit()
    db.refresh(product)
    return _serialize_market_product(product, current_user)


@router.post("/api/market/products", response_model=MarketProductResponse)
async def create_market_product(
    payload: MarketProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in ALLOWED_MARKET_STATUS:
        raise HTTPException(status_code=400, detail="无效的商品状态")

    product = MarketProduct(
        **payload.model_dump(),
        seller_id=current_user.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return _serialize_market_product(product, current_user)


@router.put("/api/market/products/{product_id}", response_model=MarketProductResponse)
async def update_market_product(
    product_id: int,
    payload: MarketProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if current_user.role != "admin" and product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己发布的商品")

    update_data = payload.model_dump(exclude_unset=True)
    status = update_data.get("status")
    if status and status not in ALLOWED_MARKET_STATUS:
        raise HTTPException(status_code=400, detail="无效的商品状态")

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return _serialize_market_product(product, current_user)


@router.delete("/api/market/products/{product_id}")
async def delete_market_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(MarketProduct).filter(MarketProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if current_user.role != "admin" and product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己发布的商品")

    removed_image = _safe_remove_market_upload(product.image_url)
    db.delete(product)
    db.commit()
    return {"message": "商品已删除", "removed_image": removed_image}


@router.post("/api/market/upload-image")
async def upload_market_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持上传图片文件")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="图片格式仅支持 jpg/jpeg/png/webp/gif")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="上传文件为空")
    if len(payload) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小超出限制（最大 10MB）")

    os.makedirs(MARKET_UPLOAD_DIR, exist_ok=True)
    filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(MARKET_UPLOAD_DIR, filename)
    with open(save_path, "wb") as fw:
        fw.write(payload)

    return {"url": f"/uploads/market/{filename}", "filename": file.filename, "size": len(payload)}
