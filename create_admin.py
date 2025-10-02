#!/usr/bin/env python3
"""
Script para crear el primer usuario administrador de CSA Construction Safety Audit
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timezone
import uuid

# Configurar la conexión a MongoDB
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

async def create_admin_user():
    # Conectar a MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🔧 Configurando usuario administrador para CSA Construction Safety Audit")
    print("=" * 60)
    
    # Solicitar datos del administrador
    admin_email = input("📧 Email del administrador: ").strip()
    admin_name = input("👤 Nombre del administrador: ").strip()
    
    if not admin_email or not admin_name:
        print("❌ Email y nombre son requeridos")
        return
    
    # Verificar si el usuario ya existe
    existing_user = await db.users.find_one({"email": admin_email})
    
    if existing_user:
        # Actualizar usuario existente a admin
        result = await db.users.update_one(
            {"email": admin_email},
            {"$set": {"role": "admin"}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Usuario {admin_email} actualizado a administrador")
        else:
            print(f"ℹ️  Usuario {admin_email} ya es administrador")
    else:
        # Crear nuevo usuario administrador
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "name": admin_name,
            "picture": "https://via.placeholder.com/150",
            "subscription_plan": "enterprise",  # Admin gets enterprise plan
            "subscription_expires": None,  # Never expires for admin
            "audits_used_this_month": 0,
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.users.insert_one(admin_user)
        print(f"✅ Administrador {admin_email} creado exitosamente")
    
    # Mostrar información de acceso
    print("\n📋 INFORMACIÓN DE ACCESO:")
    print("=" * 40)
    print(f"🌐 URL de la aplicación: https://constr-safety.preview.emergentagent.com")
    print(f"👤 Email: {admin_email}")
    print(f"🔐 Tipo de usuario: Administrador")
    print("\n🎯 FUNCIONES DISPONIBLES:")
    print("• Ver todas las métricas del negocio")
    print("• Gestionar usuarios y suscripciones")  
    print("• Panel de soporte al cliente")
    print("• Crear otros administradores")
    print("• Acceso a estadísticas completas")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Inicia sesión en la aplicación")
    print("2. Ve al tab 'Admin' para ver el dashboard")
    print("3. Revisa el tab 'Support' para herramientas de soporte")
    print("4. Configura tu estrategia de precios si es necesario")
    
    # Cerrar conexión
    client.close()
    print("\n✨ Configuración completada!")

if __name__ == "__main__":
    asyncio.run(create_admin_user())