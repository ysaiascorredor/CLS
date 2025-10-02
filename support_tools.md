# Herramientas de Soporte CSA

## COMANDOS DE DIAGNÓSTICO

### 1. VERIFICAR USUARIO
```bash
# Buscar usuario por email
mongosh --eval "
use('test_database');
db.users.findOne({email: 'usuario@email.com'});
"

# Ver historial de pagos del usuario
mongosh --eval "
use('test_database');
var user = db.users.findOne({email: 'usuario@email.com'});
if (user) {
  db.payment_transactions.find({user_id: user.id}).sort({created_at: -1});
}
"
```

### 2. SOLUCIÓN DE PROBLEMAS COMUNES

**Problema: "No puedo crear auditorías"**
```bash
# Verificar límites de suscripción
mongosh --eval "
use('test_database');
var user = db.users.findOne({email: 'usuario@email.com'});
print('Plan:', user.subscription_plan);
print('Auditorías usadas:', user.audits_used_this_month);
print('Expira:', user.subscription_expires);
"
```

**Problema: "Mi pago no se procesó"**
```bash
# Ver transacciones fallidas
mongosh --eval "
use('test_database');
db.payment_transactions.find({
  user_id: 'USER_ID',
  payment_status: {\$in: ['failed', 'pending']}
}).sort({created_at: -1});
"
```

### 3. ACCIONES DE SOPORTE

**Extender suscripción gratis (por problemas técnicos):**
```bash
mongosh --eval "
use('test_database');
db.users.updateOne(
  {email: 'usuario@email.com'},
  {\$set: {
    subscription_expires: new Date(Date.now() + 7*24*60*60*1000)
  }}
);
print('Suscripción extendida 7 días');
"
```

**Resetear contador de auditorías:**
```bash
mongosh --eval "
use('test_database');
db.users.updateOne(
  {email: 'usuario@email.com'},
  {\$set: {audits_used_this_month: 0}}
);
print('Contador de auditorías reseteado');
"
```

**Cambiar plan manualmente:**
```bash
mongosh --eval "
use('test_database');
db.users.updateOne(
  {email: 'usuario@email.com'},
  {\$set: {
    subscription_plan: 'professional',
    subscription_expires: new Date(Date.now() + 30*24*60*60*1000)
  }}
);
print('Plan cambiado a Professional');
"
```

## PLANTILLAS DE EMAIL DE SOPORTE

### Respuesta Automática
```
Asunto: Hemos recibido tu consulta - CSA Support

Hola [NOMBRE],

Gracias por contactar el soporte de CSA Construction Safety Audit.

Hemos recibido tu consulta y la estamos revisando. Te responderemos dentro de las próximas 24 horas.

Mientras tanto, puedes consultar nuestra base de conocimientos:
- Preguntas frecuentes: [URL]
- Tutoriales: [URL] 
- Guías de usuario: [URL]

Saludos,
Equipo CSA Support
```

### Problema Resuelto
```
Asunto: Problema resuelto - CSA Support

Hola [NOMBRE],

Hemos solucionado el problema que reportaste:

[DESCRIPCIÓN DE LA SOLUCIÓN]

Tu cuenta ya debería estar funcionando normalmente. Si continúas teniendo problemas, por favor responde a este email.

¡Gracias por usar CSA Construction Safety Audit!

Saludos,
Equipo CSA Support
```

## ESCALACIÓN DE PROBLEMAS

### Nivel 1: Soporte Básico
- Problemas de login
- Preguntas sobre planes
- Errores básicos de usuario

### Nivel 2: Soporte Técnico  
- Problemas de pagos
- Errores de aplicación
- Problemas de rendimiento

### Nivel 3: Desarrollo
- Bugs críticos
- Nuevas funcionalidades
- Integraciones personalizadas