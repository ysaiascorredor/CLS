# Endpoints de Administración Sugeridos

## CREAR PANEL DE ADMIN

Agrega estos endpoints al backend para gestionar tu negocio:

```python
# Agregar a server.py

@api_router.get("/admin/stats")
async def get_admin_stats():
    """Estadísticas generales del negocio"""
    total_users = await db.users.count_documents({})
    active_subscribers = await db.users.count_documents({"subscription_plan": {"$ne": None}})
    total_revenue = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    monthly_audits = await db.audits.count_documents({
        "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
    })
    
    return {
        "total_users": total_users,
        "active_subscribers": active_subscribers,
        "total_revenue": total_revenue[0]["total"] if total_revenue else 0,
        "monthly_audits": monthly_audits
    }

@api_router.get("/admin/users")
async def get_all_users(skip: int = 0, limit: int = 100):
    """Lista de todos los usuarios"""
    users = await db.users.find().skip(skip).limit(limit).to_list(limit)
    return users

@api_router.get("/admin/revenue")
async def get_revenue_stats():
    """Ingresos por mes"""
    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
            "revenue": {"$sum": "$amount"},
            "transactions": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]
    return await db.payment_transactions.aggregate(pipeline).to_list(12)

@api_router.put("/admin/users/{user_id}/subscription")
async def update_user_subscription(user_id: str, plan: str):
    """Cambiar suscripción de usuario manualmente"""
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "subscription_plan": plan,
            "subscription_expires": expires,
            "audits_used_this_month": 0
        }}
    )
    return {"message": "Subscription updated"}
```

## FRONTEND ADMIN (React Component)

```jsx
function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [revenue, setRevenue] = useState([]);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    const [statsRes, usersRes, revenueRes] = await Promise.all([
      axios.get('/api/admin/stats'),
      axios.get('/api/admin/users'),
      axios.get('/api/admin/revenue')
    ]);
    
    setStats(statsRes.data);
    setUsers(usersRes.data);
    setRevenue(revenueRes.data);
  };

  return (
    <div className="admin-dashboard">
      <h1>CSA Admin Dashboard</h1>
      
      {/* Métricas Clave */}
      <div className="metrics-grid">
        <MetricCard title="Total Users" value={stats?.total_users} />
        <MetricCard title="Active Subscribers" value={stats?.active_subscribers} />
        <MetricCard title="Total Revenue" value={`$${stats?.total_revenue}`} />
        <MetricCard title="Monthly Audits" value={stats?.monthly_audits} />
      </div>
      
      {/* Tabla de Usuarios */}
      <UsersTable users={users} />
      
      {/* Gráfico de Ingresos */}
      <RevenueChart data={revenue} />
    </div>
  );
}