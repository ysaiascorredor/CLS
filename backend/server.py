from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status, Response, Cookie, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import requests
from fastapi.responses import JSONResponse
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="CSA Construction Safety Audit API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Stripe setup
stripe_api_key = os.environ.get('STRIPE_API_KEY')

# Work types for construction audits
WORK_TYPES = [
    {"id": "excavation", "name_en": "Excavation Work", "name_es": "Trabajo de Excavación"},
    {"id": "height_work", "name_en": "Height Work", "name_es": "Trabajo en Altura"},
    {"id": "welding", "name_en": "Welding Operations", "name_es": "Operaciones de Soldadura"},
    {"id": "heavy_machinery", "name_en": "Heavy Machinery Operation", "name_es": "Operación de Maquinaria Pesada"},
    {"id": "electrical", "name_en": "Electrical Work", "name_es": "Trabajo Eléctrico"},
    {"id": "concrete", "name_en": "Concrete Work", "name_es": "Trabajo de Concreto"},
    {"id": "scaffolding", "name_en": "Scaffolding", "name_es": "Andamiaje"},
    {"id": "demolition", "name_en": "Demolition", "name_es": "Demolición"},
    {"id": "roofing", "name_en": "Roofing Work", "name_es": "Trabajo de Techado"},
    {"id": "painting", "name_en": "Painting/Coating", "name_es": "Pintura/Recubrimiento"},
    {"id": "plumbing", "name_en": "Plumbing", "name_es": "Plomería"},
    {"id": "hvac", "name_en": "HVAC Installation", "name_es": "Instalación HVAC"},
    {"id": "steel_erection", "name_en": "Steel Erection", "name_es": "Montaje de Acero"},
    {"id": "road_construction", "name_en": "Road Construction", "name_es": "Construcción de Carreteras"},
    {"id": "underground_utilities", "name_en": "Underground Utilities", "name_es": "Servicios Subterráneos"}
]

# Subscription packages
SUBSCRIPTION_PACKAGES = {
    "basic": {"price": 29.99, "name": "Basic Plan", "audits_per_month": 50},
    "professional": {"price": 79.99, "name": "Professional Plan", "audits_per_month": 200},
    "enterprise": {"price": 199.99, "name": "Enterprise Plan", "audits_per_month": -1}  # unlimited
}

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    picture: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    audits_used_this_month: int = 0
    role: str = "user"  # "user" or "admin"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    is_compliant: bool
    photo_url: Optional[str] = None
    comment: Optional[str] = None
    action_taken: Optional[str] = None

class Audit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    site_name: str
    auditor_name: str
    selected_work_types: List[str]  # 3 work type IDs
    findings: List[Finding] = []
    overall_compliance_score: Optional[float] = None
    status: str = "in_progress"  # in_progress, completed
    language: str = "en"  # en or es
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class AuditCreate(BaseModel):
    site_name: str
    auditor_name: str
    selected_work_types: List[str]
    language: str = "en"

class FindingCreate(BaseModel):
    question: str
    is_compliant: bool
    photo_url: Optional[str] = None
    comment: Optional[str] = None
    action_taken: Optional[str] = None

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: str
    amount: float
    currency: str
    package_type: str
    payment_status: str = "pending"
    stripe_status: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Statistics(BaseModel):
    total_audits: int
    compliant_audits: int
    non_compliant_audits: int
    average_compliance_score: float
    most_common_findings: List[Dict[str, Any]]
    work_type_statistics: List[Dict[str, Any]]

# Authentication helper
async def get_current_user(session_token: str = None, authorization: str = None) -> Optional[User]:
    # Check session token from cookie first
    if session_token:
        token = session_token
    # Then check Authorization header
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    else:
        return None
    
    # Find session in database
    session_doc = await db.user_sessions.find_one({"session_token": token})
    if not session_doc:
        return None
    
    # Check if session is expired
    if session_doc["expires_at"] < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": token})
        return None
    
    # Find user
    user_doc = await db.users.find_one({"id": session_doc["user_id"]})
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(
    session_token: Optional[str] = Cookie(None),
    authorization: str = Depends(HTTPBearer(auto_error=False))
) -> User:
    auth_header = authorization.credentials if authorization else None
    user = await get_current_user(session_token, f"Bearer {auth_header}" if auth_header else None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(current_user: User = Depends(require_auth)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth endpoints
@api_router.get("/auth/session")
async def get_session_data(session_id: str):
    """Get user data from session ID after OAuth"""
    url = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
    headers = {"X-Session-ID": session_id}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    user_data = response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    
    if existing_user:
        user = User(**existing_user)
    else:
        # Create new user
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture")
        )
        await db.users.insert_one(user.dict())
    
    # Create session
    session = UserSession(
        user_id=user.id,
        session_token=user_data["session_token"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    await db.user_sessions.insert_one(session.dict())
    
    return {"user": user, "session_token": user_data["session_token"]}

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current authenticated user info"""
    return current_user

@api_router.post("/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None),
    authorization: str = Depends(HTTPBearer(auto_error=False))
):
    """Logout user"""
    auth_header = authorization.credentials if authorization else None
    token = session_token or (auth_header if auth_header else None)
    
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

# Work types endpoint
@api_router.get("/work-types")
async def get_work_types():
    """Get all available work types for audits"""
    return WORK_TYPES

# Audit endpoints
@api_router.post("/audits", response_model=Audit)
async def create_audit(audit_data: AuditCreate, current_user: User = Depends(require_auth)):
    """Create a new safety audit"""
    # Check subscription limits
    if current_user.subscription_plan:
        package = SUBSCRIPTION_PACKAGES.get(current_user.subscription_plan)
        if package and package["audits_per_month"] != -1:
            if current_user.audits_used_this_month >= package["audits_per_month"]:
                raise HTTPException(status_code=403, detail="Monthly audit limit reached")
    
    # Validate selected work types
    if len(audit_data.selected_work_types) != 3:
        raise HTTPException(status_code=400, detail="Must select exactly 3 work types")
    
    audit = Audit(
        user_id=current_user.id,
        site_name=audit_data.site_name,
        auditor_name=audit_data.auditor_name,
        selected_work_types=audit_data.selected_work_types,
        language=audit_data.language
    )
    
    await db.audits.insert_one(audit.dict())
    
    # Update user audit count
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"audits_used_this_month": 1}}
    )
    
    return audit

@api_router.get("/audits", response_model=List[Audit])
async def get_user_audits(current_user: User = Depends(require_auth)):
    """Get all audits for the current user"""
    audits = await db.audits.find({"user_id": current_user.id}).to_list(1000)
    return [Audit(**audit) for audit in audits]

@api_router.get("/audits/{audit_id}", response_model=Audit)
async def get_audit(audit_id: str, current_user: User = Depends(require_auth)):
    """Get a specific audit"""
    audit = await db.audits.find_one({"id": audit_id, "user_id": current_user.id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return Audit(**audit)

@api_router.post("/audits/{audit_id}/findings")
async def add_finding(audit_id: str, finding_data: FindingCreate, current_user: User = Depends(require_auth)):
    """Add a finding to an audit"""
    audit = await db.audits.find_one({"id": audit_id, "user_id": current_user.id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    finding = Finding(**finding_data.dict())
    
    # Add finding to audit
    await db.audits.update_one(
        {"id": audit_id},
        {"$push": {"findings": finding.dict()}}
    )
    
    return {"message": "Finding added successfully", "finding": finding}

@api_router.put("/audits/{audit_id}/complete")
async def complete_audit(audit_id: str, current_user: User = Depends(require_auth)):
    """Complete an audit and calculate compliance score"""
    audit_doc = await db.audits.find_one({"id": audit_id, "user_id": current_user.id})
    if not audit_doc:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Calculate compliance score
    findings = audit_doc.get("findings", [])
    if findings:
        compliant_count = sum(1 for f in findings if f["is_compliant"])
        compliance_score = (compliant_count / len(findings)) * 100
    else:
        compliance_score = 0.0
    
    # Update audit
    await db.audits.update_one(
        {"id": audit_id},
        {
            "$set": {
                "status": "completed",
                "overall_compliance_score": compliance_score,
                "completed_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Audit completed", "compliance_score": compliance_score}

# Statistics endpoints
@api_router.get("/statistics", response_model=Statistics)
async def get_user_statistics(current_user: User = Depends(require_auth)):
    """Get audit statistics for the current user"""
    # Get all completed audits
    audits = await db.audits.find({"user_id": current_user.id, "status": "completed"}).to_list(1000)
    
    if not audits:
        return Statistics(
            total_audits=0,
            compliant_audits=0,
            non_compliant_audits=0,
            average_compliance_score=0.0,
            most_common_findings=[],
            work_type_statistics=[]
        )
    
    total_audits = len(audits)
    compliant_audits = sum(1 for audit in audits if (audit.get("overall_compliance_score", 0) >= 80))
    non_compliant_audits = total_audits - compliant_audits
    
    # Calculate average compliance score
    scores = [audit.get("overall_compliance_score", 0) for audit in audits]
    average_score = sum(scores) / len(scores) if scores else 0.0
    
    # Work type statistics
    work_type_counts = {}
    for audit in audits:
        for work_type in audit.get("selected_work_types", []):
            work_type_counts[work_type] = work_type_counts.get(work_type, 0) + 1
    
    work_type_stats = [
        {"work_type": wt, "count": count} 
        for wt, count in work_type_counts.items()
    ]
    
    return Statistics(
        total_audits=total_audits,
        compliant_audits=compliant_audits,
        non_compliant_audits=non_compliant_audits,
        average_compliance_score=average_score,
        most_common_findings=[],  # Could be expanded
        work_type_statistics=work_type_stats
    )

# Payment endpoints
@api_router.get("/payments/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    return SUBSCRIPTION_PACKAGES

@api_router.post("/payments/checkout/session")
async def create_checkout_session(
    request: Request,
    package_id: str,
    origin_url: str,
    current_user: User = Depends(require_auth)
):
    """Create Stripe checkout session for subscription"""
    if package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = SUBSCRIPTION_PACKAGES[package_id]
    amount = package["price"]
    
    # Create success and cancel URLs
    success_url = f"{origin_url}/subscription-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    
    # Initialize Stripe
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/payments/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user.id,
            "package_id": package_id,
            "package_name": package["name"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Store payment transaction
    transaction = PaymentTransaction(
        user_id=current_user.id,
        session_id=session.session_id,
        amount=amount,
        currency="usd",
        package_type=package_id,
        payment_status="pending",
        metadata=checkout_request.metadata
    )
    await db.payment_transactions.insert_one(transaction.dict())
    
    return session

@api_router.get("/payments/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: User = Depends(require_auth)):
    """Check payment status"""
    # Initialize Stripe
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    # Get status from Stripe
    status_response = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction in database
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if transaction:
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "payment_status": "paid" if status_response.payment_status == "paid" else "failed",
                    "stripe_status": status_response.status
                }
            }
        )
        
        # If payment successful, update user subscription
        if status_response.payment_status == "paid" and transaction["payment_status"] != "paid":
            package_id = transaction["package_type"]
            expires_at = datetime.now(timezone.utc) + timedelta(days=30)
            
            await db.users.update_one(
                {"id": current_user.id},
                {
                    "$set": {
                        "subscription_plan": package_id,
                        "subscription_expires": expires_at,
                        "audits_used_this_month": 0
                    }
                }
            )
    
    return status_response

@api_router.post("/payments/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Process webhook event
        if webhook_response.event_type == "checkout.session.completed":
            session_id = webhook_response.session_id
            
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "paid", "stripe_status": "completed"}}
            )
            
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== ENDPOINTS DE ADMINISTRACIÓN =====

@api_router.get("/admin/dashboard")
async def get_admin_dashboard(admin_user: User = Depends(require_admin)):
    """Dashboard completo de administración con todas las métricas"""
    
    # Métricas básicas
    total_users = await db.users.count_documents({})
    total_admins = await db.users.count_documents({"role": "admin"})
    active_subscribers = await db.users.count_documents({"subscription_plan": {"$ne": None}})
    
    # Usuarios por plan
    users_by_plan = await db.users.aggregate([
        {"$group": {"_id": "$subscription_plan", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    # Revenue total
    total_revenue_result = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_revenue = total_revenue_result[0]["total"] if total_revenue_result else 0
    
    # Revenue mensual
    monthly_revenue = await db.payment_transactions.aggregate([
        {"$match": {
            "payment_status": "paid",
            "created_at": {"$gte": datetime.now(timezone.utc).replace(day=1)}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    current_month_revenue = monthly_revenue[0]["total"] if monthly_revenue else 0
    
    # Auditorías totales y mensuales
    total_audits = await db.audits.count_documents({})
    monthly_audits = await db.audits.count_documents({
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
    })
    
    # Auditorías completadas
    completed_audits = await db.audits.count_documents({"status": "completed"})
    
    # Usuarios nuevos esta semana
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_week = await db.users.count_documents({"created_at": {"$gte": week_ago}})
    
    # Revenue por mes (últimos 12 meses)
    revenue_by_month = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "revenue": {"$sum": "$amount"},
            "transactions": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 12}
    ]).to_list(12)
    
    # Top usuarios por auditorías
    top_users = await db.audits.aggregate([
        {"$group": {"_id": "$user_id", "audit_count": {"$sum": 1}}},
        {"$sort": {"audit_count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Obtener información de los top users
    top_users_info = []
    for user_data in top_users:
        user_info = await db.users.find_one({"id": user_data["_id"]})
        if user_info:
            top_users_info.append({
                "name": user_info["name"],
                "email": user_info["email"],
                "audit_count": user_data["audit_count"],
                "plan": user_info.get("subscription_plan", "free")
            })
    
    return {
        "metrics": {
            "total_users": total_users,
            "total_admins": total_admins,
            "active_subscribers": active_subscribers,
            "total_revenue": total_revenue,
            "current_month_revenue": current_month_revenue,
            "total_audits": total_audits,
            "monthly_audits": monthly_audits,
            "completed_audits": completed_audits,
            "new_users_week": new_users_week,
            "conversion_rate": (active_subscribers / total_users * 100) if total_users > 0 else 0
        },
        "users_by_plan": users_by_plan,
        "revenue_by_month": revenue_by_month,
        "top_users": top_users_info
    }

@api_router.get("/admin/users")
async def get_all_users(
    skip: int = 0, 
    limit: int = 100,
    search: str = None,
    plan: str = None,
    admin_user: User = Depends(require_admin)
):
    """Lista todos los usuarios con filtros"""
    
    filter_criteria = {}
    
    if search:
        filter_criteria["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    if plan and plan != "all":
        if plan == "free":
            filter_criteria["subscription_plan"] = None
        else:
            filter_criteria["subscription_plan"] = plan
    
    total_count = await db.users.count_documents(filter_criteria)
    users = await db.users.find(filter_criteria).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    
    # Agregar información adicional de cada usuario
    for user in users:
        # Número de auditorías
        user["total_audits"] = await db.audits.count_documents({"user_id": user["id"]})
        
        # Último pago
        last_payment = await db.payment_transactions.find_one(
            {"user_id": user["id"], "payment_status": "paid"},
            sort=[("created_at", -1)]
        )
        user["last_payment"] = last_payment["created_at"] if last_payment else None
        user["total_paid"] = 0
        
        if last_payment:
            # Total pagado por el usuario
            total_paid_result = await db.payment_transactions.aggregate([
                {"$match": {"user_id": user["id"], "payment_status": "paid"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            user["total_paid"] = total_paid_result[0]["total"] if total_paid_result else 0
    
    return {
        "users": users,
        "total_count": total_count,
        "page": skip // limit + 1,
        "per_page": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@api_router.get("/admin/user/{user_id}")
async def get_user_details(user_id: str, admin_user: User = Depends(require_admin)):
    """Detalles completos de un usuario específico"""
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Auditorías del usuario
    audits = await db.audits.find({"user_id": user_id}).sort("created_at", -1).to_list(50)
    
    # Historial de pagos
    payments = await db.payment_transactions.find({"user_id": user_id}).sort("created_at", -1).to_list(20)
    
    # Sesiones activas
    active_sessions = await db.user_sessions.find({
        "user_id": user_id,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    }).to_list(10)
    
    return {
        "user": user,
        "audits": audits,
        "payments": payments,
        "active_sessions": active_sessions,
        "stats": {
            "total_audits": len(audits),
            "completed_audits": len([a for a in audits if a.get("status") == "completed"]),
            "total_paid": sum(p["amount"] for p in payments if p["payment_status"] == "paid"),
            "active_sessions_count": len(active_sessions)
        }
    }

@api_router.put("/admin/user/{user_id}")
async def update_user(
    user_id: str, 
    update_data: dict,
    admin_user: User = Depends(require_admin)
):
    """Actualizar información de usuario (plan, rol, etc.)"""
    
    allowed_fields = ["subscription_plan", "subscription_expires", "audits_used_this_month", "role"]
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if "subscription_expires" in update_fields and isinstance(update_fields["subscription_expires"], str):
        update_fields["subscription_expires"] = datetime.fromisoformat(update_fields["subscription_expires"])
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully", "updated_fields": list(update_fields.keys())}

@api_router.get("/admin/revenue")
async def get_revenue_stats(admin_user: User = Depends(require_admin)):
    """Estadísticas detalladas de ingresos"""
    
    # Revenue por mes (últimos 12 meses)
    revenue_by_month = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "revenue": {"$sum": "$amount"},
            "transactions": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}},
        {"$limit": 12}
    ]).to_list(12)
    
    # Revenue por plan
    revenue_by_plan = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {
            "_id": "$package_type",
            "revenue": {"$sum": "$amount"},
            "transactions": {"$sum": 1}
        }}
    ]).to_list(10)
    
    # Transacciones recientes
    recent_transactions = await db.payment_transactions.find({}).sort("created_at", -1).limit(20).to_list(20)
    
    # MRR (Monthly Recurring Revenue)
    current_month = datetime.now(timezone.utc).replace(day=1)
    mrr_result = await db.payment_transactions.aggregate([
        {"$match": {
            "payment_status": "paid",
            "created_at": {"$gte": current_month}
        }},
        {"$group": {"_id": None, "mrr": {"$sum": "$amount"}}}
    ]).to_list(1)
    mrr = mrr_result[0]["mrr"] if mrr_result else 0
    
    return {
        "revenue_by_month": revenue_by_month,
        "revenue_by_plan": revenue_by_plan,
        "recent_transactions": recent_transactions,
        "mrr": mrr
    }

@api_router.get("/admin/support-tickets")
async def get_support_info(admin_user: User = Depends(require_admin)):
    """Información para soporte al cliente"""
    
    # Usuarios con problemas potenciales
    users_with_failed_payments = await db.payment_transactions.find({
        "payment_status": "failed"
    }).sort("created_at", -1).to_list(20)
    
    # Usuarios activos sin suscripción (pueden necesitar ayuda)
    active_users_no_sub = await db.users.find({
        "subscription_plan": None,
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
    }).to_list(50)
    
    # Usuarios con muchas auditorías pero sin upgrade
    heavy_users_no_upgrade = await db.audits.aggregate([
        {"$group": {"_id": "$user_id", "audit_count": {"$sum": 1}}},
        {"$match": {"audit_count": {"$gte": 10}}},
        {"$sort": {"audit_count": -1}}
    ]).to_list(20)
    
    # Obtener info de usuarios heavy
    heavy_users_info = []
    for user_data in heavy_users_no_upgrade:
        user = await db.users.find_one({"id": user_data["_id"]})
        if user and not user.get("subscription_plan"):
            heavy_users_info.append({
                "user": user,
                "audit_count": user_data["audit_count"]
            })
    
    return {
        "failed_payments": users_with_failed_payments,
        "active_users_no_subscription": active_users_no_sub,
        "heavy_users_no_upgrade": heavy_users_info[:10]
    }

@api_router.post("/admin/create-admin")
async def create_admin_user(
    email: str,
    name: str,
    current_admin: User = Depends(require_admin)
):
    """Crear un nuevo usuario administrador"""
    
    # Verificar que el email no exista
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Crear nuevo admin
    new_admin = User(
        email=email,
        name=name,
        role="admin",
        picture="https://via.placeholder.com/150"
    )
    
    await db.users.insert_one(new_admin.dict())
    
    return {"message": f"Admin user created successfully", "admin": new_admin}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()