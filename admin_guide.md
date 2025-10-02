# Guía de Administración - CSA Construction Safety Audit

## PANEL DE ADMINISTRACIÓN SUGERIDO

### 1. MÉTRICAS DE NEGOCIO
- Total de usuarios registrados
- Suscriptores activos por plan
- Ingresos mensuales recurrentes (MRR)
- Tasa de conversión (free to paid)
- Retención de usuarios
- Auditorías realizadas por mes

### 2. GESTIÓN DE USUARIOS
```sql
-- Queries útiles para MongoDB

// Ver todos los usuarios
db.users.find().pretty()

// Usuarios por plan de suscripción
db.users.aggregate([
  { $group: { _id: "$subscription_plan", count: { $sum: 1 } } }
])

// Ingresos mensuales
db.payment_transactions.aggregate([
  { $match: { payment_status: "paid" } },
  { $group: { 
    _id: { $dateToString: { format: "%Y-%m", date: "$created_at" } },
    revenue: { $sum: "$amount" },
    transactions: { $sum: 1 }
  }}
])

// Usuarios más activos
db.audits.aggregate([
  { $group: { _id: "$user_id", audit_count: { $sum: 1 } } },
  { $sort: { audit_count: -1 } },
  { $limit: 10 }
])
```

### 3. SOPORTE AL CLIENTE

#### A. PROBLEMAS TÉCNICOS COMUNES:

**Problema: Usuario no puede iniciar sesión**
- Verificar en `db.users` si existe el email
- Revisar `db.user_sessions` para sesiones activas
- Logs del backend en `/var/log/supervisor/backend.out.log`

**Problema: Pagos no procesados**
- Verificar en `db.payment_transactions` el estado
- Revisar webhook de Stripe
- Consultar dashboard de Stripe

**Problema: Auditorías no se guardan**
- Verificar permisos de base de datos
- Revisar límites de suscripción del usuario
- Logs de errores en backend

#### B. COMANDOS DE SOPORTE:

```bash
# Ver usuarios recientes
mongosh --eval "
use('test_database');
db.users.find().sort({created_at: -1}).limit(10).pretty();
"

# Ver pagos recientes
mongosh --eval "
use('test_database');
db.payment_transactions.find().sort({created_at: -1}).limit(10).pretty();
"

# Ver auditorías por usuario
mongosh --eval "
use('test_database');
db.audits.find({user_id: 'USER_ID_HERE'}).pretty();
"

# Cambiar plan de usuario manualmente
mongosh --eval "
use('test_database');
db.users.updateOne(
  {email: 'user@email.com'},
  {\$set: {
    subscription_plan: 'professional',
    subscription_expires: new Date(Date.now() + 30*24*60*60*1000),
    audits_used_this_month: 0
  }}
);
"
```

## ESTRATEGIAS DE CRECIMIENTO

### 1. MARKETING DIGITAL
- Google Ads para "construction safety audit"
- LinkedIn para llegar a supervisores de construcción
- Webinars sobre seguridad en construcción
- Blog con contenido sobre normativas de seguridad

### 2. PARTNERSHIPS
- Empresas constructoras grandes
- Consultores de seguridad ocupacional
- Asociaciones de la industria de construcción
- Compañías de seguros

### 3. EXPANSIÓN DE MERCADO
- Agregar más tipos de industrias (minería, petróleo)
- Versión en otros idiomas
- Certificaciones internacionales
- Mobile app nativa

## ADMINISTRACIÓN DIARIA

### TAREAS SEMANALES:
1. Revisar métricas de ingresos
2. Responder tickets de soporte
3. Analizar usuarios más activos
4. Verificar pagos fallidos
5. Backup de base de datos

### TAREAS MENSUALES:
1. Análisis de retención
2. Optimización de conversión
3. Actualización de precios si necesario
4. Reporte financiero
5. Planificación de nuevas features

## ESCALABILIDAD

### CUANDO CRECER:
- +100 usuarios activos: Contratar soporte
- +500 usuarios: Implementar chat en vivo
- +1000 usuarios: Equipo de desarrollo
- +5000 usuarios: Infraestructura dedicada

### MÉTRICAS CLAVE:
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)
- Monthly Recurring Revenue (MRR)
- Churn Rate
- Net Promoter Score (NPS)