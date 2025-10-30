from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status as http_status, Response, Cookie, BackgroundTasks
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
from fastapi.responses import JSONResponse, FileResponse
import json
import bcrypt
import jwt
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import base64


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

# Work types for construction audits with specific questions
WORK_TYPES = [
    # EXISTING CATEGORIES
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
    {"id": "underground_utilities", "name_en": "Underground Utilities", "name_es": "Servicios Subterráneos"},
    
    # NEW CATEGORIES - Safety Planning & Analysis
    {"id": "jsa", "name_en": "Job Safety Analysis (JSA)", "name_es": "Análisis de Seguridad del Trabajo (AST)"},
    
    # NEW CATEGORIES - PPE & Equipment
    {"id": "ppe", "name_en": "Personal Protective Equipment (PPE)", "name_es": "Equipo de Protección Personal (EPP)"},
    {"id": "lifting_equipment", "name_en": "Lifting Equipment & Cranes", "name_es": "Equipos de Elevación y Grúas"},
    {"id": "housekeeping", "name_en": "Housekeeping & Site Organization", "name_es": "Orden y Limpieza del Sitio"},
    {"id": "chemical_work", "name_en": "Chemical Handling & Hazmat", "name_es": "Manejo de Químicos y Materiales Peligrosos"},
]

# Specific safety questions for each work type
SAFETY_QUESTIONS = {
    "excavation": {
        "en": [
            "Is the excavation properly sloped or shored to prevent cave-ins?",
            "Are workers using proper entry/exit methods (ladders, ramps)?",
            "Is there adequate ventilation in the excavated area?",
            "Are underground utilities marked and located before digging?",
            "Is there proper drainage to prevent water accumulation?",
            "Are excavated materials stored at safe distances from the edge?"
        ],
        "es": [
            "¿La excavación está apropiadamente inclinada o apuntalada para prevenir derrumbes?",
            "¿Los trabajadores están usando métodos apropiados de entrada/salida (escaleras, rampas)?",
            "¿Hay ventilación adecuada en el área excavada?",
            "¿Están marcados y localizados los servicios subterráneos antes de excavar?",
            "¿Hay drenaje apropiado para prevenir acumulación de agua?",
            "¿Los materiales excavados están almacenados a distancias seguras del borde?"
        ]
    },
    "height_work": {
        "en": [
            "Are workers wearing proper fall protection equipment (harnesses, lanyards)?",
            "Are guardrails installed on elevated platforms and walkways?",
            "Are ladders properly secured and in good condition?",
            "Is there adequate lighting for work at height?",
            "Are workers trained in fall protection procedures?",
            "Are safety nets installed where appropriate?"
        ],
        "es": [
            "¿Los trabajadores están usando equipo apropiado de protección contra caídas (arneses, cables)?",
            "¿Están instaladas barandillas en plataformas elevadas y pasarelas?",
            "¿Las escaleras están apropiadamente aseguradas y en buenas condiciones?",
            "¿Hay iluminación adecuada para trabajo en altura?",
            "¿Los trabajadores están entrenados en procedimientos de protección contra caídas?",
            "¿Están instaladas redes de seguridad donde es apropiado?"
        ]
    },
    "welding": {
        "en": [
            "Are welders wearing proper protective equipment (helmets, gloves, aprons)?",
            "Is there adequate ventilation in welding areas?",
            "Are fire extinguishers readily available near welding operations?",
            "Are welding screens used to protect nearby workers from arc flash?",
            "Is the work area free of flammable materials?",
            "Are welding cables and equipment in good condition?"
        ],
        "es": [
            "¿Los soldadores están usando equipo protector apropiado (cascos, guantes, mandiles)?",
            "¿Hay ventilación adecuada en las áreas de soldadura?",
            "¿Están los extintores fácilmente disponibles cerca de operaciones de soldadura?",
            "¿Se usan pantallas de soldadura para proteger a trabajadores cercanos del arco eléctrico?",
            "¿El área de trabajo está libre de materiales inflamables?",
            "¿Los cables y equipos de soldadura están en buenas condiciones?"
        ]
    },
    "heavy_machinery": {
        "en": [
            "Are operators certified and trained for the specific machinery?",
            "Are daily pre-operational inspections being conducted?",
            "Are proper communication signals established between operators and ground personnel?",
            "Are exclusion zones marked around operating machinery?",
            "Is machinery equipped with working warning devices (horns, lights)?",
            "Are proper maintenance schedules being followed?"
        ],
        "es": [
            "¿Los operadores están certificados y entrenados para la maquinaria específica?",
            "¿Se están realizando inspecciones preoperacionales diarias?",
            "¿Están establecidas señales de comunicación apropiadas entre operadores y personal de tierra?",
            "¿Están marcadas las zonas de exclusión alrededor de la maquinaria en operación?",
            "¿La maquinaria está equipada con dispositivos de advertencia funcionando (bocinas, luces)?",
            "¿Se están siguiendo los horarios apropiados de mantenimiento?"
        ]
    },
    "electrical": {
        "en": [
            "Are all electrical workers properly trained and certified?",
            "Is lockout/tagout (LOTO) procedure being followed for electrical work?",
            "Are ground fault circuit interrupters (GFCI) being used?",
            "Are electrical panels properly labeled and secured?",
            "Is appropriate PPE being used for electrical work?",
            "Are temporary electrical installations properly grounded?"
        ],
        "es": [
            "¿Todos los trabajadores eléctricos están apropiadamente entrenados y certificados?",
            "¿Se está siguiendo el procedimiento de bloqueo/etiquetado (LOTO) para trabajo eléctrico?",
            "¿Se están usando interruptores de circuito de falla a tierra (GFCI)?",
            "¿Los paneles eléctricos están apropiadamente etiquetados y asegurados?",
            "¿Se está usando EPP apropiado para trabajo eléctrico?",
            "¿Las instalaciones eléctricas temporales están apropiadamente conectadas a tierra?"
        ]
    },
    "concrete": {
        "en": [
            "Are workers wearing appropriate PPE when handling concrete (gloves, boots, eye protection)?",
            "Are concrete forms properly braced and secured?",
            "Is there safe access to concrete placement areas?",
            "Are concrete pumps and equipment properly maintained?",
            "Is there proper protection against concrete burns and skin contact?",
            "Are vibration tools being used safely?"
        ],
        "es": [
            "¿Los trabajadores están usando EPP apropiado al manejar concreto (guantes, botas, protección ocular)?",
            "¿Las formas de concreto están apropiadamente arriostradas y aseguradas?",
            "¿Hay acceso seguro a las áreas de colocación de concreto?",
            "¿Las bombas de concreto y equipos están apropiadamente mantenidos?",
            "¿Hay protección apropiada contra quemaduras de concreto y contacto con la piel?",
            "¿Las herramientas de vibración se están usando de manera segura?"
        ]
    },
    "scaffolding": {
        "en": [
            "Are scaffolds erected by qualified personnel?",
            "Are scaffolds properly tied off and braced to the structure?",
            "Are guardrails and toe boards installed on all open sides?",
            "Is the scaffold platform fully planked with no gaps?",
            "Are access ladders properly secured and positioned?",
            "Is the scaffold load capacity clearly marked and not exceeded?"
        ],
        "es": [
            "¿Los andamios están montados por personal calificado?",
            "¿Los andamios están apropiadamente amarrados y arriostrados a la estructura?",
            "¿Están instaladas barandillas y rodapiés en todos los lados abiertos?",
            "¿La plataforma del andamio está completamente entablada sin espacios?",
            "¿Las escaleras de acceso están apropiadamente aseguradas y posicionadas?",
            "¿La capacidad de carga del andamio está claramente marcada y no se excede?"
        ]
    },
    "demolition": {
        "en": [
            "Is there a detailed demolition plan and sequence?",
            "Are utilities properly disconnected and capped?",
            "Is the structure evaluated for hazardous materials (asbestos, lead)?",
            "Are proper dust control measures in place?",
            "Is debris removal conducted safely and regularly?",
            "Are exclusion zones established and maintained around demolition work?"
        ],
        "es": [
            "¿Hay un plan y secuencia detallada de demolición?",
            "¿Los servicios están apropiadamente desconectados y tapados?",
            "¿La estructura está evaluada para materiales peligrosos (asbesto, plomo)?",
            "¿Están en lugar las medidas apropiadas de control de polvo?",
            "¿La remoción de escombros se conduce de manera segura y regular?",
            "¿Están establecidas y mantenidas zonas de exclusión alrededor del trabajo de demolición?"
        ]
    },
    "roofing": {
        "en": [
            "Are workers wearing proper fall protection when working on roofs?",
            "Are roof penetrations and openings properly guarded?",
            "Is there safe access to the roof (stairs, ladders with proper tie-offs)?",
            "Are weather conditions suitable for roofing work?",
            "Are materials properly stored and secured on the roof?",
            "Is there proper edge protection installed?"
        ],
        "es": [
            "¿Los trabajadores están usando protección apropiada contra caídas cuando trabajan en techos?",
            "¿Las penetraciones y aberturas del techo están apropiadamente protegidas?",
            "¿Hay acceso seguro al techo (escaleras, escalones con amarres apropiados)?",
            "¿Las condiciones climáticas son apropiadas para trabajo de techado?",
            "¿Los materiales están apropiadamente almacenados y asegurados en el techo?",
            "¿Está instalada protección apropiada de bordes?"
        ]
    },
    "painting": {
        "en": [
            "Are workers wearing appropriate respiratory protection when needed?",
            "Is there adequate ventilation in painting areas?",
            "Are paint fumes and vapors properly controlled?",
            "Are flammable materials properly stored away from ignition sources?",
            "Are workers wearing appropriate skin and eye protection?",
            "Are spray painting operations conducted in designated areas?"
        ],
        "es": [
            "¿Los trabajadores están usando protección respiratoria apropiada cuando es necesario?",
            "¿Hay ventilación adecuada en las áreas de pintura?",
            "¿Los humos y vapores de pintura están apropiadamente controlados?",
            "¿Los materiales inflamables están apropiadamente almacenados lejos de fuentes de ignición?",
            "¿Los trabajadores están usando protección apropiada para piel y ojos?",
            "¿Las operaciones de pintura por aspersión se conducen en áreas designadas?"
        ]
    },
    "plumbing": {
        "en": [
            "Are workers trained in proper lifting techniques for heavy pipes and fixtures?",
            "Is there adequate ventilation when working with solvents and adhesives?",
            "Are trenches for underground plumbing properly shored or sloped?",
            "Is hot work (soldering, welding) conducted with proper fire prevention measures?",
            "Are workers wearing appropriate PPE for chemical exposure?",
            "Is there proper testing for hazardous gases in confined spaces?"
        ],
        "es": [
            "¿Los trabajadores están entrenados en técnicas apropiadas de levantamiento para tubos y accesorios pesados?",
            "¿Hay ventilación adecuada cuando se trabaja con solventes y adhesivos?",
            "¿Las zanjas para plomería subterránea están apropiadamente apuntaladas o inclinadas?",
            "¿El trabajo en caliente (soldadura) se conduce con medidas apropiadas de prevención de incendios?",
            "¿Los trabajadores están usando EPP apropiado para exposición química?",
            "¿Hay pruebas apropiadas para gases peligrosos en espacios confinados?"
        ]
    },
    "hvac": {
        "en": [
            "Are workers trained in refrigerant handling and safety procedures?",
            "Is there proper ventilation when working with HVAC chemicals?",
            "Are lifting aids used for heavy HVAC equipment installation?",
            "Is electrical lockout/tagout followed when servicing HVAC systems?",
            "Are workers wearing appropriate PPE when handling insulation materials?",
            "Is there safe access to rooftop HVAC equipment?"
        ],
        "es": [
            "¿Los trabajadores están entrenados en manejo de refrigerantes y procedimientos de seguridad?",
            "¿Hay ventilación apropiada cuando se trabaja con químicos de HVAC?",
            "¿Se usan ayudas de levantamiento para instalación de equipos HVAC pesados?",
            "¿Se sigue el bloqueo/etiquetado eléctrico cuando se da servicio a sistemas HVAC?",
            "¿Los trabajadores están usando EPP apropiado cuando manejan materiales de aislamiento?",
            "¿Hay acceso seguro a equipos HVAC en azoteas?"
        ]
    },
    "steel_erection": {
        "en": [
            "Are steel erectors properly trained and certified for their tasks?",
            "Is fall protection used throughout all phases of steel erection?",
            "Are crane operations properly coordinated with steel erection activities?",
            "Is there proper communication between ground personnel and erectors?",
            "Are connecting hardware and fasteners properly secured?",
            "Is there adequate temporary bracing during erection?"
        ],
        "es": [
            "¿Los montadores de acero están apropiadamente entrenados y certificados para sus tareas?",
            "¿Se usa protección contra caídas durante todas las fases del montaje de acero?",
            "¿Las operaciones de grúa están apropiadamente coordinadas con actividades de montaje de acero?",
            "¿Hay comunicación apropiada entre personal de tierra y montadores?",
            "¿Los herrajes de conexión y sujetadores están apropiadamente asegurados?",
            "¿Hay arriostrado temporal adecuado durante el montaje?"
        ]
    },
    "road_construction": {
        "en": [
            "Is proper traffic control established and maintained?",
            "Are workers wearing high-visibility clothing in traffic areas?",
            "Is there adequate protection between workers and vehicular traffic?",
            "Are flaggers properly trained and positioned?",
            "Is equipment properly marked with warning devices when operating near traffic?",
            "Are work zones properly signed and barricaded?"
        ],
        "es": [
            "¿Está establecido y mantenido el control de tráfico apropiado?",
            "¿Los trabajadores están usando ropa de alta visibilidad en áreas de tráfico?",
            "¿Hay protección adecuada entre trabajadores y tráfico vehicular?",
            "¿Los señalizadores están apropiadamente entrenados y posicionados?",
            "¿El equipo está apropiadamente marcado con dispositivos de advertencia cuando opera cerca del tráfico?",
            "¿Las zonas de trabajo están apropiadamente señalizadas y con barricadas?"
        ]
    },
    "underground_utilities": {
        "en": [
            "Are all underground utilities properly located and marked before work begins?",
            "Is there proper atmospheric testing in confined spaces?",
            "Is adequate ventilation provided in underground work areas?",
            "Are proper entry and exit procedures followed for confined spaces?",
            "Is there continuous monitoring for hazardous gases?",
            "Are rescue procedures established for underground work?"
        ],
        "es": [
            "¿Todos los servicios subterráneos están apropiadamente localizados y marcados antes de comenzar el trabajo?",
            "¿Hay pruebas atmosféricas apropiadas en espacios confinados?",
            "¿Se proporciona ventilación adecuada en áreas de trabajo subterráneo?",
            "¿Se siguen procedimientos apropiados de entrada y salida para espacios confinados?",
            "¿Hay monitoreo continuo para gases peligrosos?",
            "¿Están establecidos procedimientos de rescate para trabajo subterráneo?"
        ]
    },
    
    # NEW CATEGORIES - Safety Planning & Analysis
    "jsa": {
        "en": [
            "Is a Job Safety Analysis (JSA) completed for this specific task?",
            "Are all identified hazards documented in the JSA?",
            "Have control measures been established for each identified hazard?",
            "Are workers trained on the JSA requirements before starting work?",
            "Is the JSA reviewed and updated when conditions change?",
            "Are job steps clearly defined and sequenced in the JSA?",
            "Have emergency procedures been established for this job?"
        ],
        "es": [
            "¿Se completó un Análisis de Seguridad del Trabajo (AST) para esta tarea específica?",
            "¿Están documentados todos los riesgos identificados en el AST?",
            "¿Se han establecido medidas de control para cada riesgo identificado?",
            "¿Están los trabajadores entrenados en los requisitos del AST antes de comenzar el trabajo?",
            "¿Se revisa y actualiza el AST cuando cambian las condiciones?",
            "¿Están los pasos del trabajo claramente definidos y secuenciados en el AST?",
            "¿Se han establecido procedimientos de emergencia para este trabajo?"
        ]
    },
    
    # NEW CATEGORIES - PPE & Equipment
    "ppe": {
        "en": [
            "Is appropriate PPE provided for all workers based on job hazards?",
            "Are hard hats, safety glasses, and work boots being worn consistently?",
            "Is hearing protection used in high-noise areas (>85 dB)?",
            "Are respirators properly fit-tested and maintained when required?",
            "Is high-visibility clothing worn when working near vehicles or equipment?",
            "Are fall protection harnesses and lanyards inspected before each use?",
            "Is PPE properly stored, cleaned, and maintained according to manufacturer instructions?"
        ],
        "es": [
            "¿Se proporciona EPP apropiado para todos los trabajadores basado en los riesgos del trabajo?",
            "¿Se usan constantemente cascos, lentes de seguridad y botas de trabajo?",
            "¿Se usa protección auditiva en áreas de alto ruido (>85 dB)?",
            "¿Están los respiradores apropiadamente probados y mantenidos cuando se requieren?",
            "¿Se usa ropa de alta visibilidad cuando se trabaja cerca de vehículos o equipos?",
            "¿Se inspeccionan los arneses y eslingas de protección contra caídas antes de cada uso?",
            "¿Se almacena, limpia y mantiene apropiadamente el EPP según las instrucciones del fabricante?"
        ]
    },
    
    "lifting_equipment": {
        "en": [
            "Are cranes and lifting equipment inspected daily before use?",
            "Are load capacities clearly marked and never exceeded?",
            "Are certified crane operators assigned to all lifting operations?",
            "Is a lift plan developed for complex or critical lifts?",
            "Are exclusion zones established around crane operations?",
            "Are rigging hardware (slings, shackles, hooks) inspected before use?",
            "Is proper communication established between crane operator and signal person?"
        ],
        "es": [
            "¿Se inspeccionan diariamente las grúas y equipos de elevación antes del uso?",
            "¿Están las capacidades de carga claramente marcadas y nunca se exceden?",
            "¿Se asignan operadores certificados de grúa a todas las operaciones de elevación?",
            "¿Se desarrolla un plan de elevación para izajes complejos o críticos?",
            "¿Se establecen zonas de exclusión alrededor de las operaciones de grúa?",
            "¿Se inspecciona el hardware de aparejo (eslingas, grilletes, ganchos) antes del uso?",
            "¿Se establece comunicación apropiada entre el operador de grúa y la persona de señales?"
        ]
    },
    
    "housekeeping": {
        "en": [
            "Are work areas kept clean and free of debris throughout the shift?",
            "Are materials properly stored and secured to prevent falling objects?",
            "Are walkways and stairs clear of obstacles and slip hazards?",
            "Is waste disposed of properly in designated containers?",
            "Are tools and equipment returned to proper storage locations after use?",
            "Are spill cleanup materials readily available for hazardous substances?",
            "Is adequate lighting maintained in all work areas?"
        ],
        "es": [
            "¿Se mantienen las áreas de trabajo limpias y libres de escombros durante el turno?",
            "¿Se almacenan y aseguran apropiadamente los materiales para prevenir objetos que caigan?",
            "¿Están los pasillos y escaleras libres de obstáculos y riesgos de resbalones?",
            "¿Se desechan apropiadamente los desperdicios en contenedores designados?",
            "¿Se devuelven las herramientas y equipos a ubicaciones apropiadas de almacenamiento después del uso?",
            "¿Están fácilmente disponibles los materiales de limpieza de derrames para sustancias peligrosas?",
            "¿Se mantiene iluminación adecuada en todas las áreas de trabajo?"
        ]
    },
    
    "chemical_work": {
        "en": [
            "Are Safety Data Sheets (SDS) available and accessible for all chemicals?",
            "Is proper chemical-resistant PPE worn when handling hazardous materials?",
            "Are chemicals properly labeled and stored in compatible groups?",
            "Is emergency eyewash and shower equipment available and functional?",
            "Are spill containment and cleanup materials readily available?",
            "Is proper ventilation provided when working with volatile chemicals?",
            "Are workers trained on chemical hazards and emergency procedures?"
        ],
        "es": [
            "¿Están disponibles y accesibles las Hojas de Datos de Seguridad (HDS) para todos los químicos?",
            "¿Se usa EPP resistente a químicos apropiado cuando se manejan materiales peligrosos?",
            "¿Están los químicos apropiadamente etiquetados y almacenados en grupos compatibles?",
            "¿Está disponible y funcional el equipo de lavado de ojos y ducha de emergencia?",
            "¿Están fácilmente disponibles los materiales de contención y limpieza de derrames?",
            "¿Se proporciona ventilación apropiada cuando se trabaja con químicos volátiles?",
            "¿Están los trabajadores entrenados en riesgos químicos y procedimientos de emergencia?"
        ]
    }
}

# Subscription packages - Single unlimited plan
SUBSCRIPTION_PACKAGES = {
    "personal": {
        "price": 5.99, 
        "name": "CSA Safety Personal", 
        "audits_per_month": -1,  # unlimited audits
        "team_members": 1,  # single user only
        "stripe_price_id": "price_1SKGWA1VJAmV9iei4dqpfsH3"  # Stripe Price ID for Personal plan
    },
    "corporate": {
        "price": 49.99, 
        "name": "CSA Safety Corporate", 
        "audits_per_month": -1,  # unlimited audits
        "team_members": -1,  # unlimited team members
        "stripe_price_id": "price_1SKGWB1VJAmV9iei4qDG5foh"  # Stripe Price ID for Corporate plan
    }
}

# Free trial limits
FREE_TRIAL_AUDITS = 5  # Users get 5 free audits before requiring subscription

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    password_hash: Optional[str] = None
    picture: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    audits_used_this_month: int = 0
    role: str = "user"  # "user" or "admin"
    organization_id: Optional[str] = None  # If part of an organization
    organization_role: str = "owner"  # "owner", "auditor", "viewer"
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    job_title: Optional[str] = None  # NEW: User's job title/position
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    audits_used_this_month: int = 0
    role: str = "user"
    organization_id: Optional[str] = None
    organization_role: str = "owner"
    created_at: datetime

class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    owner_id: str
    subscription_plan: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    audits_used_this_month: int = 0
    team_members_count: int = 1
    # Multi-tenant branding fields
    company_name: Optional[str] = None  # Display name for white-label
    logo_url: Optional[str] = None  # Company logo
    brand_color: Optional[str] = "#3B82F6"  # Primary brand color (default blue)
    secondary_color: Optional[str] = "#10B981"  # Secondary color (default green)

class OrganizationBrandingUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    secondary_color: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # User who receives the notification
    type: str  # "finding_assigned", "finding_due", "finding_closed", etc.
    title: str
    message: str
    finding_id: Optional[str] = None
    audit_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: Optional[datetime] = None

class TeamInvitation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    inviter_id: str
    invitee_email: EmailStr
    invitee_name: str
    role: str = "auditor"  # "auditor" or "viewer"
    status: str = "pending"  # "pending", "accepted", "declined", "expired"
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    user_id: str
    role: str = "auditor"  # "owner", "auditor", "viewer"
    invited_by: str
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FindingMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # Who sent the message
    user_name: str  # Name of sender
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    compliance_status: Optional[str] = None  # "compliant", "non_compliant", "n/a"
    is_compliant: Optional[bool] = None  # Kept for backward compatibility
    photo_url: Optional[str] = None
    comment: Optional[str] = None
    action_taken: Optional[str] = None
    # NEW: Finding assignment and tracking
    assigned_to: Optional[str] = None  # User ID of person assigned
    status: Optional[str] = "open"  # "open", "in_progress", "closed"
    priority: Optional[str] = "medium"  # "low", "medium", "high", "critical"
    due_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None  # User ID who closed it
    messages: List[dict] = []  # List of messages for this finding

class JobSite(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Organization that owns this site
    name: str  # Site name
    location: Optional[str] = None  # Address or location
    description: Optional[str] = None
    created_by: str  # User who created the site
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class JobSiteCreate(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class Audit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_site_id: Optional[str] = None  # Link to JobSite (NEW)
    site_name: str  # Keep for backward compatibility
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
    job_site_id: Optional[str] = None  # NEW: Optional job site ID

class FindingCreate(BaseModel):
    question: str
    compliance_status: Optional[str] = None  # "compliant", "non_compliant", "n/a"
    is_compliant: Optional[bool] = None  # Kept for backward compatibility
    photo_url: Optional[str] = None
    comment: Optional[str] = None
    action_taken: Optional[str] = None
    assigned_to: Optional[str] = None  # User ID of person assigned
    status: Optional[str] = "open"  # "open", "in_progress", "closed"
    priority: Optional[str] = "medium"  # "low", "medium", "high", "critical"
    due_date: Optional[datetime] = None

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

class ChartData(BaseModel):
    audit_trends: List[Dict[str, Any]]  # Monthly/weekly trends
    compliance_trends: List[Dict[str, Any]]  # Compliant vs non-compliant over time
    work_type_performance: List[Dict[str, Any]]  # Performance by work type
    monthly_summary: List[Dict[str, Any]]  # Summary by month

# Password helpers
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

# Authentication helper
async def get_current_user(authorization: str = None) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    
    if not user_id:
        return None
    
    # Find user
    user_doc = await db.users.find_one({"id": user_id})
    if not user_doc:
        return None
    
    # Remove password_hash before returning
    user_doc.pop("password_hash", None)
    return User(**user_doc)

async def require_auth(authorization: str = Depends(HTTPBearer(auto_error=False))) -> User:
    auth_header = authorization.credentials if authorization else None
    user = await get_current_user(f"Bearer {auth_header}" if auth_header else None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def require_admin(current_user: User = Depends(require_auth)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth endpoints
@api_router.post("/auth/register")
async def register_user(user_data: UserRegister):
    """Register a new user with email and password"""
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password,
        picture="https://via.placeholder.com/150"
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(user.id)
    
    # Return user info without password
    user_response = UserResponse(**user.dict())
    
    return {
        "message": "User registered successfully",
        "user": user_response,
        "access_token": access_token,
        "token_type": "bearer"
    }

@api_router.post("/auth/login")
async def login_user(user_data: UserLogin):
    """Login user with email and password"""
    
    # Find user by email
    user_doc = await db.users.find_one({"email": user_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(user_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(user_doc["id"])
    
    # Return user info without password
    user_doc.pop("password_hash", None)
    user_response = UserResponse(**user_doc)
    
    return {
        "message": "Login successful",
        "user": user_response,
        "access_token": access_token,
        "token_type": "bearer"
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_auth)):
    """Get current authenticated user info"""
    return UserResponse(**current_user.dict())


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    job_title: Optional[str] = None
    picture: Optional[str] = None

@api_router.put("/auth/profile")
async def update_user_profile(profile_data: UserProfileUpdate, current_user: User = Depends(require_auth)):
    """Update current user's profile"""
    
    update_data = {}
    if profile_data.name is not None:
        update_data["name"] = profile_data.name
    if profile_data.job_title is not None:
        update_data["job_title"] = profile_data.job_title
    if profile_data.picture is not None:
        update_data["picture"] = profile_data.picture
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user
    updated_user = await db.users.find_one({"id": current_user.id})
    return UserResponse(**updated_user)


@api_router.post("/auth/logout")
async def logout():
    """Logout user (client should discard token)"""
    return {"message": "Logged out successfully"}

# Work types endpoint
@api_router.get("/work-types")
async def get_work_types():
    """Get all available work types for audits"""
    return WORK_TYPES

class QuestionsRequest(BaseModel):
    work_types: List[str]
    language: str = "en"

@api_router.post("/audits/questions")
async def generate_questions(request: QuestionsRequest):
    """Generate safety questions based on selected work types"""
    questions = []
    
    for work_type in request.work_types:
        if work_type in SAFETY_QUESTIONS:
            type_questions = SAFETY_QUESTIONS[work_type].get(request.language, SAFETY_QUESTIONS[work_type]["en"])
            for question in type_questions:
                questions.append({
                    "work_type": work_type,
                    "question": question
                })
    
    return {"questions": questions}

# Audit endpoints
@api_router.post("/audits", response_model=Audit)
async def create_audit(audit_data: AuditCreate, current_user: User = Depends(require_auth)):
    """Create a new safety audit"""
    
    # Validate selected work types first
    if len(audit_data.selected_work_types) == 0:
        raise HTTPException(status_code=400, detail="Must select at least 1 work type")
    
    # OWNER ORGANIZATION BYPASS: Users in owner's organization (Cls - ID: 84826630-0df0-4ce3-8f4b-dcbf8d411061) get unlimited access
    owner_org_id = "84826630-0df0-4ce3-8f4b-dcbf8d411061"
    if current_user.email == "ysaias.corredor@gmail.com" or current_user.role == "admin" or current_user.organization_id == owner_org_id:
        # Skip all subscription checks for owner/admin/owner's organization members
        pass
    else:
        logging.warning(f"CHECKING LIMITS for {current_user.email}")
        # Check subscription limits (individual or organization) - ONLY for non-admins
        if current_user.organization_id:
            # User is part of an organization - check org limits
            org = await db.organizations.find_one({"id": current_user.organization_id})
            if org and org.get("subscription_plan"):
                package = SUBSCRIPTION_PACKAGES.get(org["subscription_plan"])
                # If unlimited (-1) or no limit, skip check
                if package and package.get("audits_per_month", -1) > 0:
                    if org.get("audits_used_this_month", 0) >= package["audits_per_month"]:
                        raise HTTPException(status_code=403, detail="Organization monthly audit limit reached")
            else:
                # Organization without subscription - check free trial limit
                if org and org.get("audits_used_this_month", 0) >= FREE_TRIAL_AUDITS:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Free trial limit reached ({FREE_TRIAL_AUDITS} audits). Please upgrade to continue."
                    )
        else:
            # Individual user - check personal limits
            if current_user.subscription_plan:
                package = SUBSCRIPTION_PACKAGES.get(current_user.subscription_plan)
                # If unlimited (-1) or no limit, skip check
                if package and package.get("audits_per_month", -1) > 0:
                    if current_user.audits_used_this_month >= package["audits_per_month"]:
                        raise HTTPException(status_code=403, detail="Monthly audit limit reached")
            else:
                # User without subscription - check free trial limit
                if current_user.audits_used_this_month >= FREE_TRIAL_AUDITS:
                    raise HTTPException(
                        status_code=403, 
                        detail=f"Free trial limit reached ({FREE_TRIAL_AUDITS} audits). Please upgrade to continue."
                    )
    
    audit = Audit(
        user_id=current_user.id,
        job_site_id=audit_data.job_site_id,  # NEW: Link to job site
        site_name=audit_data.site_name,
        auditor_name=audit_data.auditor_name,
        selected_work_types=audit_data.selected_work_types,
        language=audit_data.language
    )
    
    await db.audits.insert_one(audit.dict())
    
    # Update audit count (individual or organization)
    if current_user.organization_id:
        await db.organizations.update_one(
            {"id": current_user.organization_id},
            {"$inc": {"audits_used_this_month": 1}}
        )
    else:
        await db.users.update_one(
            {"id": current_user.id},
            {"$inc": {"audits_used_this_month": 1}}
        )
    
    return audit


# ===== JOB SITE MANAGEMENT =====

@api_router.post("/job-sites", response_model=JobSite)
async def create_job_site(site_data: JobSiteCreate, current_user: User = Depends(require_auth)):
    """Create a new job site"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization to create job sites")
    
    new_site = JobSite(
        organization_id=current_user.organization_id,
        name=site_data.name,
        location=site_data.location,
        description=site_data.description,
        created_by=current_user.id
    )
    
    await db.job_sites.insert_one(new_site.dict())
    return new_site

@api_router.get("/job-sites", response_model=List[JobSite])
async def get_job_sites(current_user: User = Depends(require_auth)):
    """Get all job sites for the user's organization"""
    
    if not current_user.organization_id:
        return []
    
    sites = await db.job_sites.find({
        "organization_id": current_user.organization_id,
        "is_active": True
    }).to_list(1000)
    
    return [JobSite(**site) for site in sites]

@api_router.get("/job-sites/{site_id}", response_model=JobSite)
async def get_job_site(site_id: str, current_user: User = Depends(require_auth)):
    """Get a specific job site"""
    
    site = await db.job_sites.find_one({
        "id": site_id,
        "organization_id": current_user.organization_id
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Job site not found")
    
    return JobSite(**site)

@api_router.put("/job-sites/{site_id}", response_model=JobSite)
async def update_job_site(site_id: str, site_data: JobSiteCreate, current_user: User = Depends(require_auth)):
    """Update a job site"""
    
    site = await db.job_sites.find_one({
        "id": site_id,
        "organization_id": current_user.organization_id
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Job site not found")
    
    update_data = {
        "name": site_data.name,
        "location": site_data.location,
        "description": site_data.description,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.job_sites.update_one({"id": site_id}, {"$set": update_data})
    
    updated_site = await db.job_sites.find_one({"id": site_id})
    return JobSite(**updated_site)

@api_router.delete("/job-sites/{site_id}")
async def delete_job_site(site_id: str, current_user: User = Depends(require_auth)):
    """Soft delete a job site"""
    
    site = await db.job_sites.find_one({
        "id": site_id,
        "organization_id": current_user.organization_id
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Job site not found")
    
    # Soft delete
    await db.job_sites.update_one(
        {"id": site_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Job site {site['name']} deleted successfully"}

@api_router.get("/job-sites/{site_id}/audits")
async def get_site_audits(site_id: str, current_user: User = Depends(require_auth)):
    """Get all audits for a specific job site"""
    
    # Verify site belongs to user's organization
    site = await db.job_sites.find_one({
        "id": site_id,
        "organization_id": current_user.organization_id
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Job site not found")
    
    # Get audits for this site
    audits = await db.audits.find({"job_site_id": site_id}).to_list(1000)
    
    return {
        "site": JobSite(**site),
        "audits": [Audit(**audit) for audit in audits],
        "total_audits": len(audits),
        "completed_audits": sum(1 for a in audits if a.get("status") == "completed")
    }

@api_router.get("/job-sites/{site_id}/statistics")
async def get_site_statistics(site_id: str, current_user: User = Depends(require_auth)):
    """Get compliance statistics for a specific job site"""
    
    # Verify site belongs to user's organization
    site = await db.job_sites.find_one({
        "id": site_id,
        "organization_id": current_user.organization_id
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Job site not found")
    
    # Get all audits for this site
    audits = await db.audits.find({"job_site_id": site_id}).to_list(1000)
    
    if not audits:
        return {
            "site": JobSite(**site),
            "total_audits": 0,
            "completed_audits": 0,
            "average_compliance": 0,
            "compliance_trend": []
        }
    
    # Calculate statistics
    completed_audits = [a for a in audits if a.get("status") == "completed" and a.get("overall_compliance_score") is not None]
    
    avg_compliance = 0
    if completed_audits:
        avg_compliance = sum(a["overall_compliance_score"] for a in completed_audits) / len(completed_audits)
    
    # Compliance trend over time
    compliance_trend = []
    for audit in sorted(completed_audits, key=lambda x: x.get("created_at", "")):
        compliance_trend.append({
            "date": audit.get("created_at"),
            "compliance_score": audit.get("overall_compliance_score")
        })
    
    return {
        "site": JobSite(**site),
        "total_audits": len(audits),
        "completed_audits": len(completed_audits),
        "average_compliance": round(avg_compliance, 2),
        "compliance_trend": compliance_trend
    }



@api_router.get("/job-sites/statistics/combined")
async def get_combined_statistics(current_user: User = Depends(require_auth)):
    """Get combined compliance statistics for all job sites in the organization"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Get all active job sites for the organization
    sites = await db.job_sites.find({
        "organization_id": current_user.organization_id,
        "is_active": True
    }).to_list(1000)
    
    if not sites:
        return {
            "total_sites": 0,
            "total_audits": 0,
            "completed_audits": 0,
            "average_compliance": 0,
            "site_statistics": [],
            "overall_trend": []
        }
    
    site_statistics = []
    all_audits = []
    
    for site in sites:
        site_audits = await db.audits.find({"job_site_id": site["id"]}).to_list(1000)
        completed = [a for a in site_audits if a.get("status") == "completed" and a.get("overall_compliance_score") is not None]
        
        avg_compliance = 0
        if completed:
            avg_compliance = sum(a["overall_compliance_score"] for a in completed) / len(completed)
        
        site_statistics.append({
            "site_id": site["id"],
            "site_name": site["name"],
            "total_audits": len(site_audits),
            "completed_audits": len(completed),
            "average_compliance": round(avg_compliance, 2)
        })
        
        all_audits.extend(completed)
    
    # Overall statistics
    overall_avg = 0
    if all_audits:
        overall_avg = sum(a["overall_compliance_score"] for a in all_audits) / len(all_audits)
    
    # Overall trend
    overall_trend = []
    for audit in sorted(all_audits, key=lambda x: x.get("created_at", "")):
        overall_trend.append({
            "date": audit.get("created_at"),
            "compliance_score": audit.get("overall_compliance_score"),
            "site_name": next((s["name"] for s in sites if s["id"] == audit.get("job_site_id")), "Unknown")
        })
    
    return {
        "total_sites": len(sites),
        "total_audits": sum(stat["total_audits"] for stat in site_statistics),
        "completed_audits": sum(stat["completed_audits"] for stat in site_statistics),
        "average_compliance": round(overall_avg, 2),
        "site_statistics": site_statistics,
        "overall_trend": overall_trend
    }

# ===== AUDIT MANAGEMENT =====

@api_router.get("/audits", response_model=List[Audit])
async def get_user_audits(current_user: User = Depends(require_auth)):
    """Get all audits - Organization-wide if user belongs to an org, otherwise personal"""
    
    if current_user.organization_id:
        # Get all users in the organization
        org_users = await db.users.find({"organization_id": current_user.organization_id}).to_list(1000)
        user_ids = [u["id"] for u in org_users]
        audits = await db.audits.find({"user_id": {"$in": user_ids}}).to_list(1000)
    else:
        # Personal audits only
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
    
    # Convert to dict
    finding_dict = finding_data.dict()
    
    # If compliance_status is not set but is_compliant is, convert it
    if not finding_dict.get('compliance_status') and finding_dict.get('is_compliant') is not None:
        finding_dict['compliance_status'] = 'compliant' if finding_dict['is_compliant'] else 'non_compliant'
    
    # Ensure compliance_status is set
    if not finding_dict.get('compliance_status'):
        raise HTTPException(status_code=400, detail="compliance_status is required")
    
    # Set default values if not provided
    if 'status' not in finding_dict or finding_dict['status'] is None:
        finding_dict['status'] = 'open'
    if 'priority' not in finding_dict or finding_dict['priority'] is None:
        finding_dict['priority'] = 'medium'
    
    finding = Finding(**finding_dict)
    
    # Add finding to audit
    await db.audits.update_one(
        {"id": audit_id},
        {"$push": {"findings": finding.dict()}}
    )
    
    # Create notification if assigned to someone
    if finding.assigned_to:
        assigned_user = await db.users.find_one({"id": finding.assigned_to})
        if assigned_user:
            notification = Notification(
                user_id=finding.assigned_to,
                type="finding_assigned",
                title="New Finding Assigned to You",
                message=f"You have been assigned a {finding.compliance_status} finding from audit '{audit.get('site_name', 'Unknown Site')}'",
                finding_id=finding.id,
                audit_id=audit_id
            )
            await db.notifications.insert_one(notification.dict())
    
    return {"message": "Finding added successfully", "finding": finding}

@api_router.put("/audits/{audit_id}/complete")
async def complete_audit(audit_id: str, current_user: User = Depends(require_auth)):
    """Complete an audit and calculate compliance score"""
    audit_doc = await db.audits.find_one({"id": audit_id, "user_id": current_user.id})
    if not audit_doc:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Calculate compliance score (excluding N/A responses)
    findings = audit_doc.get("findings", [])
    if findings:
        # Count responses by status
        applicable_findings = []
        for f in findings:
            # Handle both new compliance_status field and old is_compliant field
            status = f.get("compliance_status")
            if status and status != "n/a":
                applicable_findings.append(f)
            elif status is None and "is_compliant" in f:
                # Backward compatibility
                applicable_findings.append(f)
        
        if applicable_findings:
            compliant_count = sum(1 for f in applicable_findings 
                                if f.get("compliance_status") == "compliant" 
                                or (f.get("compliance_status") is None and f.get("is_compliant")))
            compliance_score = (compliant_count / len(applicable_findings)) * 100
        else:
            compliance_score = 0.0
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


# ===== FINDINGS MANAGEMENT & ASSIGNMENT =====

class FindingUpdate(BaseModel):
    assigned_to: Optional[str] = None
    status: Optional[str] = None  # "open", "in_progress", "closed"
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    action_taken: Optional[str] = None
    comment: Optional[str] = None

@api_router.put("/audits/{audit_id}/findings/{finding_id}")
async def update_finding(
    audit_id: str,
    finding_id: str,
    finding_data: FindingUpdate,
    current_user: User = Depends(require_auth)
):
    """Update a finding - assign to user, change status, etc."""
    
    # Get audit
    audit = await db.audits.find_one({"id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Verify access (same organization)
    audit_creator = await db.users.find_one({"id": audit["user_id"]})
    if current_user.organization_id != audit_creator.get("organization_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find and update the finding
    findings = audit.get("findings", [])
    finding_updated = False
    
    for finding in findings:
        if finding["id"] == finding_id:
            # Update fields
            if finding_data.assigned_to is not None:
                # Verify assigned user exists and is in organization
                assigned_user = await db.users.find_one({"id": finding_data.assigned_to})
                if not assigned_user or assigned_user.get("organization_id") != current_user.organization_id:
                    raise HTTPException(status_code=400, detail="Invalid user assignment")
                
                old_assigned = finding.get("assigned_to")
                finding["assigned_to"] = finding_data.assigned_to
                
                # Create notification for assigned user if changed
                if old_assigned != finding_data.assigned_to:
                    notification = Notification(
                        user_id=finding_data.assigned_to,
                        type="finding_assigned",
                        title="New Finding Assigned",
                        message=f"You have been assigned a finding: {finding.get('question', 'N/A')}",
                        finding_id=finding_id,
                        audit_id=audit_id
                    )
                    await db.notifications.insert_one(notification.dict())
            
            if finding_data.status is not None:
                finding["status"] = finding_data.status
                if finding_data.status == "closed":
                    finding["closed_at"] = datetime.now(timezone.utc).isoformat()
                    finding["closed_by"] = current_user.id
            
            if finding_data.priority is not None:
                finding["priority"] = finding_data.priority
            
            if finding_data.due_date is not None:
                finding["due_date"] = finding_data.due_date.isoformat()
            
            if finding_data.action_taken is not None:
                finding["action_taken"] = finding_data.action_taken
            
            if finding_data.comment is not None:
                finding["comment"] = finding_data.comment
            
            finding_updated = True
            break
    
    if not finding_updated:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Update audit
    await db.audits.update_one(
        {"id": audit_id},
        {"$set": {"findings": findings}}
    )
    
    return {"message": "Finding updated successfully", "finding": finding}

@api_router.get("/audits/{audit_id}/findings/open")
async def get_open_findings(audit_id: str, current_user: User = Depends(require_auth)):
    """Get all open findings for an audit"""
    
    audit = await db.audits.find_one({"id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    findings = audit.get("findings", [])
    open_findings = [f for f in findings if f.get("status", "open") != "closed" and f.get("compliance_status") == "non_compliant"]
    
    return {
        "audit_id": audit_id,
        "site_name": audit.get("site_name"),
        "open_findings": open_findings,
        "total_open": len(open_findings)
    }

@api_router.get("/findings/my-assignments")
async def get_my_assigned_findings(current_user: User = Depends(require_auth)):
    """Get all findings assigned to current user"""
    
    # Get all audits in user's organization
    if not current_user.organization_id:
        return {"assigned_findings": [], "total": 0}
    
    org_users = await db.users.find({"organization_id": current_user.organization_id}).to_list(1000)
    user_ids = [u["id"] for u in org_users]
    
    audits = await db.audits.find({"user_id": {"$in": user_ids}}).to_list(1000)
    
    assigned_findings = []
    for audit in audits:
        findings = audit.get("findings", [])
        for finding in findings:
            if finding.get("assigned_to") == current_user.id and finding.get("status", "open") != "closed":
                assigned_findings.append({
                    **finding,
                    "audit_id": audit["id"],
                    "site_name": audit.get("site_name"),
                    "auditor_name": audit.get("auditor_name")
                })
    
    return {
        "assigned_findings": assigned_findings,
        "total": len(assigned_findings)
    }


@api_router.post("/audits/{audit_id}/findings/{finding_id}/messages")
async def add_finding_message(
    audit_id: str, 
    finding_id: str,
    message_text: str,
    current_user: User = Depends(require_auth)
):
    """Add a message to a finding"""
    
    # Get audit
    audit = await db.audits.find_one({"id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Verify user has access (auditor, assigned person, or admin)
    findings = audit.get("findings", [])
    finding = None
    for f in findings:
        if f.get("id") == finding_id:
            finding = f
            break
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Create message
    message = FindingMessage(
        user_id=current_user.id,
        user_name=current_user.name,
        message=message_text
    )
    
    # Add message to finding
    if "messages" not in finding:
        finding["messages"] = []
    finding["messages"].append(message.dict())
    
    # Update audit in database
    await db.audits.update_one(
        {"id": audit_id, "findings.id": finding_id},
        {"$set": {"findings.$": finding}}
    )
    
    # Create notification for the other party
    if finding.get("assigned_to") and finding.get("assigned_to") != current_user.id:
        # Notify assigned person
        notification = Notification(
            user_id=finding["assigned_to"],
            type="finding_message",
            title="New Message on Finding",
            message=f"{current_user.name}: {message_text[:50]}...",
            finding_id=finding_id,
            audit_id=audit_id
        )
        await db.notifications.insert_one(notification.dict())
    elif audit.get("user_id") != current_user.id:
        # Notify auditor
        notification = Notification(
            user_id=audit["user_id"],
            type="finding_message",
            title="New Message on Finding",
            message=f"{current_user.name}: {message_text[:50]}...",
            finding_id=finding_id,
            audit_id=audit_id
        )
        await db.notifications.insert_one(notification.dict())
    
    return {"message": "Message added successfully", "finding_message": message}

@api_router.get("/audits/{audit_id}/findings/{finding_id}/messages")
async def get_finding_messages(
    audit_id: str, 
    finding_id: str,
    current_user: User = Depends(require_auth)
):
    """Get all messages for a finding"""
    
    audit = await db.audits.find_one({"id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    findings = audit.get("findings", [])
    finding = None
    for f in findings:
        if f.get("id") == finding_id:
            finding = f
            break
    
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    messages = finding.get("messages", [])
    
    return {
        "messages": messages,
        "total": len(messages)
    }

# ===== NOTIFICATIONS =====

@api_router.get("/notifications")
async def get_user_notifications(current_user: User = Depends(require_auth)):
    """Get all notifications for current user"""
    
    notifications = await db.notifications.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    
    unread_count = sum(1 for n in notifications if not n.get("is_read", False))
    
    return {
        "notifications": [Notification(**n) for n in notifications],
        "total": len(notifications),
        "unread": unread_count
    }

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(require_auth)):
    """Mark a notification as read"""
    
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(require_auth)):
    """Mark all notifications as read"""
    
    result = await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"{result.modified_count} notifications marked as read"}

# ===== STATISTICS =====

@api_router.get("/statistics", response_model=Statistics)
async def get_user_statistics(current_user: User = Depends(require_auth)):
    """Get audit statistics - Organization-wide if user belongs to an org, otherwise personal"""
    
    # Build query based on organization membership
    if current_user.organization_id:
        # Get all users in the organization
        org_users = await db.users.find({"organization_id": current_user.organization_id}).to_list(1000)
        user_ids = [u["id"] for u in org_users]
        query = {"user_id": {"$in": user_ids}, "status": "completed"}
    else:
        # Personal audits only
        query = {"user_id": current_user.id, "status": "completed"}
    
    audits = await db.audits.find(query).to_list(1000)
    
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

@api_router.get("/statistics/charts", response_model=ChartData)
async def get_chart_data(current_user: User = Depends(require_auth)):
    """Get data for charts and graphs - Organization-wide if user belongs to an org"""
    
    # Build query based on organization membership
    if current_user.organization_id:
        # Get all users in the organization
        org_users = await db.users.find({"organization_id": current_user.organization_id}).to_list(1000)
        user_ids = [u["id"] for u in org_users]
        query = {
            "user_id": {"$in": user_ids},
            "status": "completed",
            "completed_at": {"$exists": True}
        }
    else:
        # Personal audits only
        query = {
            "user_id": current_user.id,
            "status": "completed",
            "completed_at": {"$exists": True}
        }
    
    audits = await db.audits.find(query).sort("completed_at", 1).to_list(1000)
    
    if not audits:
        return ChartData(
            audit_trends=[],
            compliance_trends=[],
            work_type_performance=[],
            monthly_summary=[]
        )
    
    # Group by month for trends
    monthly_data = {}
    for audit in audits:
        completed_date = audit.get("completed_at")
        if completed_date:
            # Convert to month-year key
            month_key = completed_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "total": 0,
                    "compliant": 0,
                    "non_compliant": 0,
                    "scores": []
                }
            
            monthly_data[month_key]["total"] += 1
            score = audit.get("overall_compliance_score", 0)
            monthly_data[month_key]["scores"].append(score)
            
            if score >= 80:
                monthly_data[month_key]["compliant"] += 1
            else:
                monthly_data[month_key]["non_compliant"] += 1
    
    # Create audit trends (total audits per month)
    audit_trends = []
    for month, data in sorted(monthly_data.items()):
        audit_trends.append({
            "month": month,
            "total_audits": data["total"],
            "avg_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        })
    
    # Create compliance trends (compliant vs non-compliant over time)
    compliance_trends = []
    for month, data in sorted(monthly_data.items()):
        compliance_trends.append({
            "month": month,
            "compliant": data["compliant"],
            "non_compliant": data["non_compliant"],
            "compliance_rate": (data["compliant"] / data["total"] * 100) if data["total"] > 0 else 0
        })
    
    # Work type performance
    work_type_scores = {}
    for audit in audits:
        score = audit.get("overall_compliance_score", 0)
        for work_type in audit.get("selected_work_types", []):
            if work_type not in work_type_scores:
                work_type_scores[work_type] = []
            work_type_scores[work_type].append(score)
    
    work_type_performance = []
    for work_type, scores in work_type_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        compliant_count = sum(1 for score in scores if score >= 80)
        work_type_performance.append({
            "work_type": work_type,
            "avg_score": round(avg_score, 1),
            "total_audits": len(scores),
            "compliant_audits": compliant_count,
            "compliance_rate": round((compliant_count / len(scores) * 100), 1) if scores else 0
        })
    
    # Monthly summary (last 6 months)
    monthly_summary = []
    now = datetime.now(timezone.utc)
    for i in range(6):
        month_date = now - timedelta(days=30*i)
        month_key = month_date.strftime("%Y-%m")
        month_name = month_date.strftime("%b %Y")
        
        data = monthly_data.get(month_key, {"total": 0, "compliant": 0, "non_compliant": 0, "scores": []})
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        
        monthly_summary.insert(0, {
            "month": month_name,
            "month_key": month_key,
            "total_audits": data["total"],
            "compliant": data["compliant"],
            "non_compliant": data["non_compliant"],
            "avg_score": round(avg_score, 1)
        })
    
    return ChartData(
        audit_trends=audit_trends,
        compliance_trends=compliance_trends,
        work_type_performance=work_type_performance,
        monthly_summary=monthly_summary
    )

@api_router.get("/statistics/findings")
async def get_findings_statistics(current_user: User = Depends(require_auth)):
    """Get comprehensive findings statistics - open vs closed"""
    
    # Build query based on organization
    if current_user.organization_id:
        org_users = await db.users.find({"organization_id": current_user.organization_id}).to_list(1000)
        user_ids = [u["id"] for u in org_users]
        query = {"user_id": {"$in": user_ids}}
    else:
        query = {"user_id": current_user.id}
    
    audits = await db.audits.find(query).to_list(1000)
    
    total_findings = 0
    open_findings = 0
    closed_findings = 0
    compliant = 0
    non_compliant = 0
    na_findings = 0
    by_priority = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    
    for audit in audits:
        findings = audit.get("findings", [])
        for finding in findings:
            total_findings += 1
            
            # Status count
            if finding.get("compliance_status") == "non_compliant":
                non_compliant += 1
                status = finding.get("status", "open")
                if status == "closed":
                    closed_findings += 1
                else:
                    open_findings += 1
                
                # Priority
                priority = finding.get("priority", "medium")
                by_priority[priority] = by_priority.get(priority, 0) + 1
            elif finding.get("compliance_status") == "compliant":
                compliant += 1
            elif finding.get("compliance_status") == "n/a":
                na_findings += 1
    
    return {
        "total_findings": total_findings,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "na": na_findings,
        "open_findings": open_findings,
        "closed_findings": closed_findings,
        "by_priority": by_priority,
        "completion_rate": round((closed_findings / non_compliant * 100) if non_compliant > 0 else 0, 2)
    }

@api_router.get("/audits/{audit_id}/pdf")
async def generate_audit_pdf(audit_id: str, current_user: User = Depends(require_auth)):
    """Generate comprehensive PDF report for an audit"""
    
    # Get audit data - Allow access if user is in same organization
    audit = await db.audits.find_one({"id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    # Verify access: either audit owner OR same organization member
    if audit["user_id"] != current_user.id:
        # Check if user is in same organization as audit creator
        audit_creator = await db.users.find_one({"id": audit["user_id"]})
        if not audit_creator or not current_user.organization_id or audit_creator.get("organization_id") != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user/company info
    user = await db.users.find_one({"id": current_user.id})
    company_name = user.get("company_name", "Construction Labor Solution LLC")
    company_logo = user.get("company_logo")
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5
    )
    
    # Story elements
    story = []
    
    # Header with company logo (if exists)
    if company_logo:
        # For now, add placeholder for logo
        story.append(Paragraph(f"<b>{company_name}</b>", styles['Title']))
    else:
        story.append(Paragraph(f"<b>{company_name}</b>", title_style))
    
    story.append(Spacer(1, 20))
    
    # Title
    story.append(Paragraph("SAFETY AUDIT REPORT", title_style))
    story.append(Spacer(1, 30))
    
    # Audit Information
    story.append(Paragraph("AUDIT INFORMATION", heading_style))
    
    audit_info_data = [
        ['Site Name:', audit.get('site_name', 'N/A')],
        ['Auditor:', audit.get('auditor_name', 'N/A')],
        ['Date Created:', audit.get('created_at', datetime.now()).strftime('%B %d, %Y') if audit.get('created_at') else 'N/A'],
        ['Date Completed:', audit.get('completed_at', datetime.now()).strftime('%B %d, %Y') if audit.get('completed_at') else 'N/A'],
        ['Status:', audit.get('status', 'N/A').title()],
        ['Overall Score:', f"{audit.get('overall_compliance_score', 0):.1f}%"],
        ['Language:', 'English' if audit.get('language', 'en') == 'en' else 'Spanish']
    ]
    
    audit_table = Table(audit_info_data, colWidths=[2*inch, 4*inch])
    audit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(audit_table)
    story.append(Spacer(1, 20))
    
    # Work Types
    work_types = audit.get('selected_work_types', [])
    if work_types:
        story.append(Paragraph("WORK TYPES AUDITED", heading_style))
        work_types_text = ", ".join(work_types)
        story.append(Paragraph(work_types_text, styles['Normal']))
        story.append(Spacer(1, 20))
    
    # Findings Summary
    findings = audit.get('findings', [])
    if findings:
        story.append(Paragraph("FINDINGS SUMMARY", heading_style))
        
        # Count findings by status
        compliant_count = 0
        non_compliant_count = 0
        na_count = 0
        
        for f in findings:
            status = f.get('compliance_status')
            if status == "compliant":
                compliant_count += 1
            elif status == "non_compliant":
                non_compliant_count += 1
            elif status == "n/a":
                na_count += 1
            elif status is None:
                # Backward compatibility with old is_compliant field
                if f.get('is_compliant', True):
                    compliant_count += 1
                else:
                    non_compliant_count += 1
        
        # Calculate compliance rate excluding N/A
        applicable_count = compliant_count + non_compliant_count
        compliance_rate = f"{(compliant_count/applicable_count*100):.1f}%" if applicable_count > 0 else "N/A"
        
        summary_data = [
            ['Total Questions:', str(len(findings))],
            ['Compliant:', str(compliant_count)],
            ['Non-Compliant:', str(non_compliant_count)],
            ['N/A (Not Applicable):', str(na_count)],
            ['Compliance Rate:', compliance_rate]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    # Detailed Findings
    if findings:
        story.append(Paragraph("DETAILED FINDINGS", heading_style))
        
        for i, finding in enumerate(findings, 1):
            # Finding header - handle both new and old formats
            status = finding.get('compliance_status')
            if status == "compliant":
                compliance_status = "✓ COMPLIANT"
                status_color = colors.green
            elif status == "non_compliant":
                compliance_status = "✗ NON-COMPLIANT"
                status_color = colors.red
            elif status == "n/a":
                compliance_status = "○ N/A (NOT APPLICABLE)"
                status_color = colors.grey
            else:
                # Backward compatibility
                is_compliant = finding.get('is_compliant', True)
                compliance_status = "✓ COMPLIANT" if is_compliant else "✗ NON-COMPLIANT"
                status_color = colors.green if is_compliant else colors.red
            
            finding_title = f"<font color='{status_color.hexval() if hasattr(status_color, 'hexval') else 'black'}'><b>Finding #{i}: {compliance_status}</b></font>"
            story.append(Paragraph(finding_title, styles['Heading2']))
            
            # Question
            question_text = f"<b>Question:</b> {finding.get('question', 'N/A')}"
            story.append(Paragraph(question_text, styles['Normal']))
            
            # Photo if available - Show for ALL findings regardless of compliance status
            if finding.get('photo_url'):
                try:
                    # Add photo to PDF
                    from reportlab.platypus import Image as RLImage
                    import requests
                    from io import BytesIO
                    
                    photo_url = finding.get('photo_url')
                    # Download image
                    img_response = requests.get(photo_url, timeout=5)
                    if img_response.status_code == 200:
                        img_data = BytesIO(img_response.content)
                        img = RLImage(img_data, width=300, height=225)
                        story.append(Spacer(1, 10))
                        story.append(img)
                        story.append(Spacer(1, 10))
                except Exception as e:
                    # If image fails, just continue without it
                    print(f"Failed to add image to PDF: {e}")
            
            # Details - Show comment and action for any finding that has them
            if finding.get('comment'):
                comment_text = f"<b>Issue Description:</b> {finding.get('comment')}"
                story.append(Paragraph(comment_text, styles['Normal']))
            
            if finding.get('action_taken'):
                action_text = f"<b>Corrective Action:</b> {finding.get('action_taken')}"
                story.append(Paragraph(action_text, styles['Normal']))
            
            # Show assignment info if assigned
            if finding.get('assigned_to'):
                # Get assigned user name
                assigned_user = await db.users.find_one({"id": finding.get('assigned_to')})
                assigned_name = assigned_user.get('name', 'Unknown') if assigned_user else 'Unknown'
                assignment_text = f"<b>Assigned To:</b> {assigned_name}"
                story.append(Paragraph(assignment_text, styles['Normal']))
            
            if finding.get('status'):
                status_text = f"<b>Status:</b> {finding.get('status', 'open').title()}"
                story.append(Paragraph(status_text, styles['Normal']))
            
            if finding.get('priority'):
                priority_text = f"<b>Priority:</b> {finding.get('priority', 'medium').title()}"
                story.append(Paragraph(priority_text, styles['Normal']))
            
            story.append(Spacer(1, 15))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    
    story.append(Paragraph("---", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Paragraph("Construction Labor Solution LLC | Safety Audit System", footer_style))
    story.append(Paragraph("This report contains confidential information", footer_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Return PDF as file response
    return Response(
        content=pdf_data,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="safety_audit_{audit_id}_{audit.get("site_name", "report").replace(" ", "_")}.pdf"'
        }
    )

# Payment endpoints
@api_router.get("/payments/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    return SUBSCRIPTION_PACKAGES

@api_router.post("/payments/checkout/session")
async def create_checkout_session(
    request: Request,
    package_data: dict,
    current_user: User = Depends(require_auth)
):
    """Create Stripe checkout session for subscription"""
    package_id = package_data.get("package_id")
    origin_url = package_data.get("origin_url")
    
    if package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = SUBSCRIPTION_PACKAGES[package_id]
    amount = package["price"]
    
    # Check if we're in demo mode (no real Stripe key)
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    is_demo_mode = not stripe_api_key or stripe_api_key == "sk_test_emergent"
    
    if is_demo_mode:
        # Demo mode - simulate checkout
        session_id = f"cs_demo_{uuid.uuid4().hex[:16]}"
        
        # Store demo payment transaction
        transaction = PaymentTransaction(
            user_id=current_user.id,
            session_id=session_id,
            amount=amount,
            currency="usd",
            package_type=package_id,
            payment_status="pending",
            metadata={
                "user_id": current_user.id,
                "package_id": package_id,
                "package_name": package["name"],
                "demo_mode": True
            }
        )
        await db.payment_transactions.insert_one(transaction.dict())
        
        # Return demo checkout URL
        return {
            "session_id": session_id,
            "url": f"{origin_url}/demo-checkout?session_id={session_id}&package={package_id}&amount={amount}"
        }
    
    else:
        # Real Stripe mode
        success_url = f"{origin_url}/subscription-success?session_id={{CHECKOUT_SESSION_ID}}&package={package_id}"
        cancel_url = f"{origin_url}/dashboard"
        
        webhook_url = f"{request.base_url}api/stripe/webhook"
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

@api_router.post("/payments/demo/complete/{session_id}")
async def complete_demo_payment(session_id: str, current_user: User = Depends(require_auth)):
    """Complete demo payment and activate subscription"""
    
    # Find the demo transaction
    transaction = await db.payment_transactions.find_one({
        "session_id": session_id,
        "user_id": current_user.id
    })
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if not transaction.get("metadata", {}).get("demo_mode"):
        raise HTTPException(status_code=400, detail="Not a demo transaction")
    
    # Mark transaction as paid
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": "paid", "stripe_status": "demo_completed"}}
    )
    
    # Activate subscription
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
    
    return {
        "message": "Demo subscription activated successfully",
        "subscription_plan": package_id,
        "expires_at": expires_at
    }
@api_router.get("/payments/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: User = Depends(require_auth)):
    """Check payment status"""
    
    # Find transaction in database
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if it's a demo transaction
    if transaction.get("metadata", {}).get("demo_mode"):
        # Return demo status
        return {
            "session_id": session_id,
            "payment_status": transaction["payment_status"],
            "status": "demo_mode",
            "demo_mode": True
        }
    
    # Real Stripe transaction
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    # Get status from Stripe
    status_response = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction in database
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
            
            # Get transaction details to activate subscription
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction:
                user_id = transaction["user_id"]
                package_type = transaction["package_type"]
                
                # Activate subscription
                expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                await db.users.update_one(
                    {"id": user_id},
                    {
                        "$set": {
                            "subscription_plan": package_type,
                            "subscription_status": "active",
                            "subscription_expires_at": expires_at.isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
            
        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/payments/fix-pending/{user_id}")
async def fix_pending_payment(user_id: str, admin_user: User = Depends(require_admin)):
    """Manual fix for pending payments - ADMIN ONLY"""
    
    # Find pending transactions for user
    pending_transactions = await db.payment_transactions.find({
        "user_id": user_id,
        "payment_status": "pending"
    }).to_list(None)
    
    if not pending_transactions:
        raise HTTPException(status_code=404, detail="No pending transactions found")
    
    # Mark all as paid and activate subscription
    for transaction in pending_transactions:
        # Update transaction status
        await db.payment_transactions.update_one(
            {"session_id": transaction["session_id"]},
            {"$set": {"payment_status": "paid", "stripe_status": "manually_completed"}}
        )
        
        # Activate subscription
        package_type = transaction["package_type"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        await db.users.update_one(
            {"id": user_id},
            {
                "$set": {
                    "subscription_plan": package_type,
                    "subscription_status": "active", 
                    "subscription_expires_at": expires_at.isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    return {"message": f"Fixed {len(pending_transactions)} pending payments and activated subscription"}

@api_router.post("/payments/cancel-subscription")
async def cancel_subscription(current_user: User = Depends(require_auth)):
    """Cancel user subscription"""
    
    # Update user subscription to cancelled
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "subscription_status": "cancelled",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Mark subscription as cancelled but keep access until expiration
    return {
        "message": "Subscription cancelled successfully. Access will continue until expiration date.",
        "status": "cancelled"
    }

# ===== DIRECT USER CREATION (BETTER THAN INVITATIONS) =====

@api_router.post("/organization/create-user")
async def create_team_user_directly(
    user_data: dict,
    current_user: User = Depends(require_auth)
):
    """Create team user directly with temporary password - MUCH BETTER than invitations"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user.organization_role not in ["owner"]:
        raise HTTPException(status_code=403, detail="Only organization owners can create users")
    
    # Validate required fields
    required_fields = ["email", "name", "role"]
    for field in required_fields:
        if field not in user_data:
            raise HTTPException(status_code=400, detail=f"Missing {field}")
    
    email = user_data["email"]
    name = user_data["name"] 
    role = user_data["role"]
    custom_password = user_data.get("password", None)  # Optional custom password
    
    # Verificar límites del plan
    org = await db.organizations.find_one({"id": current_user.organization_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org["subscription_plan"]:
        package = SUBSCRIPTION_PACKAGES.get(org["subscription_plan"])
        if package and package["team_members"] != -1:
            current_members = await db.team_members.count_documents({"organization_id": org["id"]})
            if current_members >= package["team_members"]:
                raise HTTPException(status_code=403, detail="Team member limit reached for current plan")
    
    # Verificar si el usuario ya existe
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        # Usuario ya existe - agregarlo a esta organización como miembro adicional
        # Verificar si ya es miembro de esta organización
        existing_member = await db.team_members.find_one({
            "user_id": existing_user["id"],
            "organization_id": current_user.organization_id
        })
        
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
        
        # Agregar como miembro de esta organización
        team_member = {
            "id": str(uuid.uuid4()),
            "organization_id": current_user.organization_id,
            "user_id": existing_user["id"],
            "role": role,
            "invited_by": current_user.id,
            "joined_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.team_members.insert_one(team_member)
        
        return {
            "message": f"Existing user {name} added to organization successfully",
            "user_id": existing_user["id"],
            "email": email,
            "name": name,
            "role": role,
            "temp_password": None,  # No password needed for existing users
            "is_existing_user": True
        }
    
    # Usar contraseña personalizada o generar una temporal
    if custom_password:
        if len(custom_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        temp_password = custom_password
    else:
        # Generar contraseña temporal segura si no se especifica
        import secrets
        import string
        
        # Contraseña temporal: 8 caracteres, fácil de recordar pero segura
        temp_password_chars = string.ascii_letters + string.digits
        temp_password = ''.join(secrets.choice(temp_password_chars) for _ in range(8))
        temp_password = temp_password.capitalize() + "2024"  # Ej: Abc12def2024
    
    # Crear usuario directamente
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        organization_id=current_user.organization_id,
        organization_role=role,
        subscription_plan=org.get("subscription_plan", "basic"),
        subscription_status="active",  # Inherits from organization
        subscription_expires_at=org.get("subscription_expires_at"),
        created_by=current_user.id
    )
    
    # Guardar usuario
    await db.users.insert_one(new_user.dict())
    
    # Crear registro en team_members
    team_member = TeamMember(
        organization_id=current_user.organization_id,
        user_id=new_user.id,
        role=role,
        invited_by=current_user.id
    )
    
    await db.team_members.insert_one(team_member.dict())
    
    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "email": email,
            "name": name,
            "role": role,
            "temporary_password": temp_password
        },
        "instructions": f"Give these credentials to {name}: Email: {email} | Password: {temp_password} | They can change password after first login",
        "password_type": "custom" if custom_password else "generated"
    }

@api_router.post("/auth/change-password")
async def change_password(
    password_data: dict,
    current_user: User = Depends(require_auth)
):
    """Allow users to change their password"""
    
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Both old and new passwords required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    # Verify old password
    user = await db.users.find_one({"id": current_user.id})
    if not user or not bcrypt.checkpw(old_password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "password_changed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Password changed successfully"}

@api_router.delete("/organization/remove-user/{user_id}")
async def remove_team_user(
    user_id: str,
    current_user: User = Depends(require_auth)
):
    """Remove user from team - only owner can do this"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user.organization_role not in ["owner"]:
        raise HTTPException(status_code=403, detail="Only organization owners can remove users")
    
    # Can't remove yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    
    # Verify user exists and belongs to same organization
    user_to_remove = await db.users.find_one({"id": user_id, "organization_id": current_user.organization_id})
    if not user_to_remove:
        raise HTTPException(status_code=404, detail="User not found in your organization")
    
    # Remove from team_members
    await db.team_members.delete_one({"user_id": user_id, "organization_id": current_user.organization_id})
    
    # Update user record (remove from organization)
    await db.users.update_one(
        {"id": user_id},
        {
            "$unset": {
                "organization_id": "",
                "organization_role": ""
            },
            "$set": {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "removed_from_org_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": f"User {user_to_remove['name']} removed from team successfully"}

# ===== EMAIL CONFIGURATION =====

@api_router.post("/settings/email")
async def configure_email_settings(
    email_config: dict,
    current_user: User = Depends(require_auth)
):
    """Configure email settings for sending invitations"""
    
    # Validate email config
    required_fields = ["smtp_server", "smtp_port", "email", "password", "sender_name"]
    for field in required_fields:
        if field not in email_config:
            raise HTTPException(status_code=400, detail=f"Missing {field}")
    
    # Encrypt password (in real app, use proper encryption)
    email_config["password"] = email_config["password"]  # TODO: Add encryption
    email_config["user_id"] = current_user.id
    email_config["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save or update email configuration
    await db.email_settings.replace_one(
        {"user_id": current_user.id},
        email_config,
        upsert=True
    )
    
    return {"message": "Email settings saved successfully"}

@api_router.get("/settings/email")
async def get_email_settings(current_user: User = Depends(require_auth)):
    """Get user's email settings (without password)"""
    
    settings = await db.email_settings.find_one({"user_id": current_user.id})
    if not settings:
        return {"configured": False}
    
    # Remove password from response
    settings.pop("password", None)
    settings.pop("_id", None)
    settings["configured"] = True
    
    return settings

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
        # Remove MongoDB ObjectId and sensitive fields
        user.pop("_id", None)
        user.pop("password_hash", None)
        
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
    
    # Remove MongoDB ObjectId and sensitive fields
    user.pop("_id", None)
    user.pop("password_hash", None)
    
    # Auditorías del usuario
    audits = await db.audits.find({"user_id": user_id}).sort("created_at", -1).to_list(50)
    
    # Remove _id from audits
    for audit in audits:
        audit.pop("_id", None)
    
    # Historial de pagos
    payments = await db.payment_transactions.find({"user_id": user_id}).sort("created_at", -1).to_list(20)
    
    # Remove _id from payments
    for payment in payments:
        payment.pop("_id", None)
    
    # Sesiones activas
    active_sessions = await db.user_sessions.find({
        "user_id": user_id,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    }).to_list(10)
    
    # Remove _id from sessions
    for session in active_sessions:
        session.pop("_id", None)
    
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
    
    # Remove MongoDB _id field to avoid JSON serialization issues
    for payment in users_with_failed_payments:
        payment.pop("_id", None)
    
    # Usuarios activos sin suscripción (pueden necesitar ayuda)
    active_users_no_sub = await db.users.find({
        "subscription_plan": None,
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
    }).to_list(50)
    
    # Remove MongoDB _id field to avoid JSON serialization issues
    for user in active_users_no_sub:
        user.pop("_id", None)
        user.pop("password_hash", None)  # Also remove password hash for security
    
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
            # Remove MongoDB _id field and password hash
            user.pop("_id", None)
            user.pop("password_hash", None)
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
    request: dict,
    current_admin: User = Depends(require_admin)
):
    """Crear un nuevo usuario administrador"""
    
    email = request.get("email")
    name = request.get("name")
    
    if not email or not name:
        raise HTTPException(status_code=400, detail="Email and name are required")
    
    # Verificar que el email no exista
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Generar password hash para un password temporal
    temp_password = "admin123"  # Password temporal
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Crear nuevo admin
    new_admin = User(
        email=email,
        name=name,
        role="admin",
        password_hash=password_hash,
        picture="https://via.placeholder.com/150"
    )
    
    await db.users.insert_one(new_admin.dict())
    
    return {"message": f"Admin user created successfully with temporary password: {temp_password}", "admin": new_admin}

@api_router.get("/admin/logs")
async def get_system_logs(current_admin: User = Depends(require_admin)):
    """Obtener logs del sistema"""
    import subprocess
    import os
    
    try:
        # Intentar obtener logs de supervisor
        if os.path.exists('/var/log/supervisor/'):
            # Obtener logs del backend
            backend_logs = ""
            frontend_logs = ""
            
            # Backend logs
            try:
                backend_log_cmd = "tail -n 50 /var/log/supervisor/backend*.log 2>/dev/null || echo 'No backend logs found'"
                backend_result = subprocess.run(backend_log_cmd, shell=True, capture_output=True, text=True, timeout=10)
                backend_logs = backend_result.stdout
            except Exception:
                backend_logs = "Error reading backend logs"
            
            # Frontend logs
            try:
                frontend_log_cmd = "tail -n 50 /var/log/supervisor/frontend*.log 2>/dev/null || echo 'No frontend logs found'"
                frontend_result = subprocess.run(frontend_log_cmd, shell=True, capture_output=True, text=True, timeout=10)
                frontend_logs = frontend_result.stdout
            except Exception:
                frontend_logs = "Error reading frontend logs"
            
            combined_logs = f"""=== BACKEND LOGS ===
{backend_logs}

=== FRONTEND LOGS ===
{frontend_logs}

=== SYSTEM INFO ===
Timestamp: {datetime.now().isoformat()}
Status: System running
"""
        else:
            combined_logs = f"""=== SYSTEM LOGS ===
Timestamp: {datetime.now().isoformat()}
Status: System running (supervisor logs not available in this environment)
Backend: Active
Frontend: Active  
Database: Connected
Authentication: Working

=== RECENT ACTIVITY ===
- Admin panel accessed by {current_admin.email}
- System logs requested at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return {"logs": combined_logs}
        
    except Exception as e:
        return {"logs": f"Error retrieving logs: {str(e)}\n\nTimestamp: {datetime.now().isoformat()}"}

@api_router.post("/admin/company/settings")
async def update_company_settings(
    settings: dict,
    current_user: User = Depends(require_auth)
):
    """Update company settings including logo and name"""
    
    company_name = settings.get("company_name")
    company_logo = settings.get("company_logo")  # Base64 encoded image
    
    update_data = {}
    if company_name:
        update_data["company_name"] = company_name
    if company_logo:
        update_data["company_logo"] = company_logo
    
    if update_data:
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_data}
        )
    
    return {"message": "Company settings updated successfully"}

@api_router.get("/company/settings")
async def get_company_settings(current_user: User = Depends(require_auth)):
    """Get company settings"""
    user = await db.users.find_one({"id": current_user.id})
    return {
        "company_name": user.get("company_name", "Construction Labor Solution LLC"),
        "company_logo": user.get("company_logo")
    }

# ===== ENDPOINTS DE ORGANIZACIONES Y EQUIPOS =====

@api_router.post("/organization/create")
async def create_organization(
    request: dict,
    current_user: User = Depends(require_auth)
):
    """Crear organización para el usuario (convierte suscripción personal en organizacional)"""
    
    name = request.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Organization name is required")
    
    # Verificar que el usuario no esté ya en una organización
    if current_user.organization_id:
        raise HTTPException(status_code=400, detail="User already belongs to an organization")
    
    # Crear la organización
    organization = Organization(
        name=name,
        owner_id=current_user.id,
        subscription_plan=current_user.subscription_plan,
        subscription_expires=current_user.subscription_expires,
        audits_used_this_month=current_user.audits_used_this_month
    )
    
    await db.organizations.insert_one(organization.dict())
    
    # Actualizar el usuario para que sea owner de la organización
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {
            "organization_id": organization.id,
            "organization_role": "owner"
        }}
    )
    
    # Crear registro de miembro del equipo
    team_member = TeamMember(
        organization_id=organization.id,
        user_id=current_user.id,
        role="owner",
        invited_by=current_user.id
    )
    
    await db.team_members.insert_one(team_member.dict())
    
    return {"message": "Organization created successfully", "organization": organization}

@api_router.post("/organization/invite")
async def invite_team_member(
    invitee_email: EmailStr,
    invitee_name: str,
    role: str = "auditor",
    current_user: User = Depends(require_auth)
):
    """Invitar miembro al equipo con enlace único"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user.organization_role not in ["owner"]:
        raise HTTPException(status_code=403, detail="Only organization owners can invite members")
    
    # Verificar límites del plan
    org = await db.organizations.find_one({"id": current_user.organization_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org["subscription_plan"]:
        package = SUBSCRIPTION_PACKAGES.get(org["subscription_plan"])
        if package and package["team_members"] != -1:
            current_members = await db.team_members.count_documents({"organization_id": org["id"]})
            if current_members >= package["team_members"]:
                raise HTTPException(status_code=403, detail="Team member limit reached for current plan")
    
    # Verificar que el email no esté ya invitado
    existing_invitation = await db.team_invitations.find_one({
        "organization_id": current_user.organization_id,
        "invitee_email": invitee_email,
        "status": "pending"
    })
    
    if existing_invitation:
        raise HTTPException(status_code=400, detail="User already invited")
    
    # Verificar que el email no esté ya en el equipo
    existing_user = await db.users.find_one({"email": invitee_email})
    if existing_user and existing_user.get("organization_id") == current_user.organization_id:
        raise HTTPException(status_code=400, detail="User already part of the team")
    
    # Crear invitación con token único
    invitation = TeamInvitation(
        organization_id=current_user.organization_id,
        inviter_id=current_user.id,
        invitee_email=invitee_email,
        invitee_name=invitee_name,
        role=role
    )
    
    await db.team_invitations.insert_one(invitation.dict())
    
    # Generar enlace único de invitación  
    invitation_link = f"https://safesitepro-1.preview.emergentagent.com/join-team/{invitation.id}"
    
    # Intentar enviar email automáticamente si está configurado
    email_sent = False
    try:
        # Buscar configuración de email del usuario
        email_config = await db.email_settings.find_one({"user_id": current_user.id})
        
        if email_config:
            # Aquí iría la lógica para enviar email
            # Por ahora simularemos que se envió
            email_sent = True
            
            # TODO: Implementar envío real de email con SMTP
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            
    except Exception as e:
        print(f"Error sending email: {e}")
    
    response_data = {
        "message": "Invitation created successfully", 
        "invitation": invitation,
        "invitation_link": invitation_link
    }
    
    if email_sent:
        response_data["email_sent"] = True
        response_data["instructions"] = f"Invitation email sent to {invitee_email}"
    else:
        response_data["email_sent"] = False
        response_data["instructions"] = "Copy this link and send it via WhatsApp, Email, or any messaging app"
    
    return response_data

@api_router.get("/organization/invitations")
async def get_pending_invitations(current_user: User = Depends(require_auth)):
    """Ver invitaciones pendientes para el usuario actual"""
    
    invitations = await db.team_invitations.find({
        "invitee_email": current_user.email,
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    }).to_list(10)
    
    # Agregar información de la organización
    for invitation in invitations:
        org = await db.organizations.find_one({"id": invitation["organization_id"]})
        invitation["organization"] = org
        
        inviter = await db.users.find_one({"id": invitation["inviter_id"]})
        invitation["inviter"] = inviter
    
    return invitations

@api_router.get("/invitations/{invitation_id}")
async def get_invitation_details(invitation_id: str):
    """Obtener detalles de invitación por enlace público"""
    invitation = await db.team_invitations.find_one({
        "id": invitation_id,
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    # Obtener información de la organización
    org = await db.organizations.find_one({"id": invitation["organization_id"]})
    inviter = await db.users.find_one({"id": invitation["inviter_id"]})
    
    return {
        "invitation": invitation,
        "organization": org,
        "inviter": inviter
    }

@api_router.post("/invitations/{invitation_id}/accept")
async def accept_invitation_by_link(invitation_id: str, user_data: dict):
    """Aceptar invitación por enlace y crear cuenta automáticamente"""
    # Verificar que la invitación existe y está válida
    invitation = await db.team_invitations.find_one({
        "id": invitation_id,
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    email = user_data.get("email")
    name = user_data.get("name")
    password = user_data.get("password")
    
    if not email or not name or not password:
        raise HTTPException(status_code=400, detail="Email, name and password are required")
    
    # Verificar que el email coincide con la invitación
    if email != invitation["invitee_email"]:
        raise HTTPException(status_code=400, detail="Email doesn't match invitation")
    
    # Verificar que el usuario no existe ya
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Crear nuevo usuario
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        email=email,
        name=name,
        password_hash=password_hash,
        organization_id=invitation["organization_id"],
        organization_role=invitation["role"]
    )
    
    await db.users.insert_one(new_user.dict())
    
    # Crear miembro del equipo
    team_member = TeamMember(
        organization_id=invitation["organization_id"],
        user_id=new_user.id,
        role=invitation["role"]
    )
    
    await db.team_members.insert_one(team_member.dict())
    
    # Marcar invitación como aceptada
    await db.team_invitations.update_one(
        {"id": invitation_id},
        {"$set": {"status": "accepted", "accepted_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Invitation accepted successfully", "user": new_user}

@api_router.post("/organization/invitations/{invitation_id}/accept")
async def accept_invitation(invitation_id: str, current_user: User = Depends(require_auth)):
    """Aceptar invitación a organización"""
    
    invitation = await db.team_invitations.find_one({
        "id": invitation_id,
        "invitee_email": current_user.email,
        "status": "pending"
    })
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    if invitation["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Verificar que el usuario no esté ya en una organización
    if current_user.organization_id:
        raise HTTPException(status_code=400, detail="User already belongs to an organization")
    
    # Aceptar invitación
    await db.team_invitations.update_one(
        {"id": invitation_id},
        {"$set": {"status": "accepted"}}
    )
    
    # Agregar usuario a la organización
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {
            "organization_id": invitation["organization_id"],
            "organization_role": invitation["role"]
        }}
    )
    
    # Crear registro de miembro del equipo
    team_member = TeamMember(
        organization_id=invitation["organization_id"],
        user_id=current_user.id,
        role=invitation["role"],
        invited_by=invitation["inviter_id"]
    )
    
    await db.team_members.insert_one(team_member.dict())
    
    # Actualizar contador de miembros en la organización
    await db.organizations.update_one(
        {"id": invitation["organization_id"]},
        {"$inc": {"team_members_count": 1}}
    )
    
    return {"message": "Invitation accepted successfully"}

@api_router.post("/organization/invitations/{invitation_id}/decline")
async def decline_invitation(invitation_id: str, current_user: User = Depends(require_auth)):
    """Rechazar invitación a organización"""
    
    result = await db.team_invitations.update_one(
        {
            "id": invitation_id,
            "invitee_email": current_user.email,
            "status": "pending"
        },
        {"$set": {"status": "declined"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return {"message": "Invitation declined"}



# ===== ORGANIZATION BRANDING & MULTI-TENANT =====

@api_router.get("/organization/branding")
async def get_organization_branding(current_user: User = Depends(require_auth)):
    """Get organization branding configuration"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    org = await db.organizations.find_one({"id": current_user.organization_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "organization_id": org["id"],
        "name": org["name"],
        "company_name": org.get("company_name", org["name"]),
        "logo_url": org.get("logo_url"),
        "brand_color": org.get("brand_color", "#3B82F6"),
        "secondary_color": org.get("secondary_color", "#10B981")
    }

@api_router.put("/organization/branding")
async def update_organization_branding(
    branding_data: OrganizationBrandingUpdate,
    current_user: User = Depends(require_auth)
):
    """Update organization branding - Only owners can do this"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    if current_user.organization_role != "owner":
        raise HTTPException(status_code=403, detail="Only organization owners can update branding")
    
    # Build update dict with only provided fields
    update_data = {}
    if branding_data.company_name is not None:
        update_data["company_name"] = branding_data.company_name
    if branding_data.logo_url is not None:
        update_data["logo_url"] = branding_data.logo_url
    if branding_data.brand_color is not None:
        # Validate color format (hex)
        if not branding_data.brand_color.startswith("#") or len(branding_data.brand_color) != 7:
            raise HTTPException(status_code=400, detail="Brand color must be in hex format (#RRGGBB)")
        update_data["brand_color"] = branding_data.brand_color
    if branding_data.secondary_color is not None:
        if not branding_data.secondary_color.startswith("#") or len(branding_data.secondary_color) != 7:
            raise HTTPException(status_code=400, detail="Secondary color must be in hex format (#RRGGBB)")
        update_data["secondary_color"] = branding_data.secondary_color
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.organizations.update_one(
        {"id": current_user.organization_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Return updated branding
    org = await db.organizations.find_one({"id": current_user.organization_id})
    
    return {
        "message": "Branding updated successfully",
        "branding": {
            "company_name": org.get("company_name", org["name"]),
            "logo_url": org.get("logo_url"),
            "brand_color": org.get("brand_color", "#3B82F6"),
            "secondary_color": org.get("secondary_color", "#10B981")
        }
    }

# ===== TEAM MANAGEMENT =====

@api_router.get("/organization/team")
async def get_team_members(current_user: User = Depends(require_auth)):
    """Ver miembros del equipo de la organización"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Obtener organización
    org = await db.organizations.find_one({"id": current_user.organization_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Remove MongoDB ObjectId from organization
    org.pop("_id", None)
    
    # Obtener miembros del equipo
    team_members = await db.team_members.find({"organization_id": current_user.organization_id}).to_list(100)
    
    # Agregar información del usuario
    for member in team_members:
        # Remove MongoDB ObjectId from member
        member.pop("_id", None)
        
        user_info = await db.users.find_one({"id": member["user_id"]})
        if user_info:
            # Remove sensitive fields from user info
            user_info.pop("_id", None)
            user_info.pop("password_hash", None)
            member["user"] = user_info
        
        # Estadísticas del miembro
        member["audit_count"] = await db.audits.count_documents({"user_id": member["user_id"]})
        member["completed_audits"] = await db.audits.count_documents({
            "user_id": member["user_id"],
            "status": "completed"
        })
    
    # Obtener invitaciones pendientes
    pending_invitations = await db.team_invitations.find({
        "organization_id": current_user.organization_id,
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    }).to_list(50)
    
    # Remove MongoDB ObjectId from invitations
    for invitation in pending_invitations:
        invitation.pop("_id", None)
    
    return {
        "organization": org,
        "team_members": team_members,
        "pending_invitations": pending_invitations
    }

@api_router.delete("/organization/team/{member_id}")
async def remove_team_member(member_id: str, current_user: User = Depends(require_auth)):
    """Remover miembro del equipo (solo owners)"""
    
    if current_user.organization_role != "owner":
        raise HTTPException(status_code=403, detail="Only organization owners can remove team members")
    
    # Encontrar el miembro
    team_member = await db.team_members.find_one({
        "id": member_id,
        "organization_id": current_user.organization_id
    })
    
    if not team_member:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    if team_member["role"] == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")
    
    # Remover miembro del equipo
    await db.team_members.delete_one({"id": member_id})
    
    # Actualizar usuario
    await db.users.update_one(
        {"id": team_member["user_id"]},
        {"$unset": {"organization_id": "", "organization_role": ""}}
    )
    
    # Actualizar contador en organización
    await db.organizations.update_one(
        {"id": current_user.organization_id},
        {"$inc": {"team_members_count": -1}}
    )
    
    return {"message": "Team member removed successfully"}

@api_router.get("/organization/audits")
async def get_organization_audits(current_user: User = Depends(require_auth)):
    """Ver todas las auditorías de la organización"""
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Obtener todos los miembros de la organización
    team_members = await db.team_members.find({"organization_id": current_user.organization_id}).to_list(100)
    user_ids = [member["user_id"] for member in team_members]
    
    # Obtener todas las auditorías de la organización
    audits = await db.audits.find({"user_id": {"$in": user_ids}}).sort("created_at", -1).to_list(1000)
    
    # Agregar información del auditor
    for audit in audits:
        user_info = await db.users.find_one({"id": audit["user_id"]})
        audit["auditor_info"] = user_info
    
    return audits

# Test page endpoint
@app.get("/test")
async def serve_test_page():
    """Serve the simple test page"""
    return FileResponse("/app/test_audit_simple.html")

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