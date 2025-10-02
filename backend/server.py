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