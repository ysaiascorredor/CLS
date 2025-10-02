import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import TestLogin from './TestLogin';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/sonner';
import { CheckCircle, XCircle, BarChart3, FileText, Settings, LogOut, Camera, Shield, Building, Users, TrendingUp } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Subscription packages reference (should match backend)
const SUBSCRIPTION_PACKAGES = {
  "basic": {"price": 29.99, "name": "Basic Plan", "audits_per_month": 50, "team_members": 3},
  "professional": {"price": 79.99, "name": "Professional Plan", "audits_per_month": 200, "team_members": 10},
  "enterprise": {"price": 199.99, "name": "Enterprise Plan", "audits_per_month": -1, "team_members": -1}
};

// Language context
const LanguageContext = React.createContext();

const translations = {
  en: {
    appName: "CSA Construction Safety Audit",
    login: "Login with Google",
    welcome: "Welcome to CSA",
    subtitle: "Professional Construction Safety Auditing Platform",
    features: "Features",
    pricing: "Pricing",
    dashboard: "Dashboard",
    newAudit: "New Audit",
    statistics: "Statistics", 
    settings: "Settings",
    logout: "Logout",
    createAudit: "Create New Audit",
    siteName: "Site Name",
    auditorName: "Auditor Name",
    selectWorkTypes: "Select Work Types (minimum 1)",
    startAudit: "Start Audit",
    auditProgress: "Audit Progress",
    question: "Question",
    compliant: "Compliant",
    nonCompliant: "Non-Compliant",
    addPhoto: "Add Photo",
    comment: "Comment (Required for Non-Compliant)",
    actionTaken: "Action Taken (Required for Non-Compliant)",
    nextQuestion: "Next Question",
    completeAudit: "Complete Audit",
    overallScore: "Overall Compliance Score",
    totalAudits: "Total Audits",
    compliantAudits: "Compliant Audits",
    nonCompliantAudits: "Non-Compliant Audits",
    averageScore: "Average Score",
    workTypeStats: "Work Type Statistics",
    basicPlan: "Basic Plan",
    professionalPlan: "Professional Plan",
    enterprisePlan: "Enterprise Plan",
    auditsPerMonth: "audits/month",
    choosePlan: "Choose Plan",
    currentPlan: "Current Plan",
    upgradeNow: "Upgrade Now",
    recentAudits: "Recent Audits",
    viewAudit: "View Audit",
    adminDashboard: "Admin Dashboard",
    supportPanel: "Support Panel",
    totalUsers: "Total Users",
    activeSubscribers: "Active Subscribers",
    totalRevenue: "Total Revenue",
    userManagement: "User Management",
    changePlan: "Change Plan",
    team: "Team",
    teamManagement: "Team Management",
    inviteMember: "Invite Member",
    createOrganization: "Create Organization",
    acceptInvitation: "Accept Invitation"
  },
  es: {
    appName: "CSA Auditoría de Seguridad en Construcción",
    login: "Iniciar sesión con Google",
    welcome: "Bienvenido a CSA",
    subtitle: "Plataforma Profesional de Auditoría de Seguridad en Construcción",
    features: "Características",
    pricing: "Precios",
    dashboard: "Panel",
    newAudit: "Nueva Auditoría",
    statistics: "Estadísticas",
    settings: "Configuración",
    logout: "Cerrar Sesión",
    createAudit: "Crear Nueva Auditoría",
    siteName: "Nombre del Sitio",
    auditorName: "Nombre del Auditor",
    selectWorkTypes: "Seleccionar Tipos de Trabajo (mínimo 1)",
    startAudit: "Iniciar Auditoría",
    auditProgress: "Progreso de Auditoría",
    question: "Pregunta",
    compliant: "Cumple",
    nonCompliant: "No Cumple",
    addPhoto: "Agregar Foto",
    comment: "Comentario (Requerido para No Cumple)",
    actionTaken: "Acción Tomada (Requerido para No Cumple)",
    nextQuestion: "Siguiente Pregunta",
    completeAudit: "Completar Auditoría",
    overallScore: "Puntaje General de Cumplimiento",
    totalAudits: "Total de Auditorías",
    compliantAudits: "Auditorías Conformes",
    nonCompliantAudits: "Auditorías No Conformes",
    averageScore: "Puntaje Promedio",
    workTypeStats: "Estadísticas por Tipo de Trabajo",
    basicPlan: "Plan Básico",
    professionalPlan: "Plan Profesional",
    enterprisePlan: "Plan Empresarial",
    auditsPerMonth: "auditorías/mes",
    choosePlan: "Elegir Plan",
    currentPlan: "Plan Actual",
    upgradeNow: "Actualizar Ahora",
    recentAudits: "Auditorías Recientes",
    viewAudit: "Ver Auditoría",
    adminDashboard: "Panel de Administración",
    supportPanel: "Panel de Soporte",
    totalUsers: "Usuarios Totales",
    activeSubscribers: "Suscriptores Activos", 
    totalRevenue: "Ingresos Totales", 
    userManagement: "Gestión de Usuarios",
    changePlan: "Cambiar Plan",
    team: "Equipo",
    teamManagement: "Gestión de Equipo",
    inviteMember: "Invitar Miembro",
    createOrganization: "Crear Organización",
    acceptInvitation: "Aceptar Invitación"
  }
};

// Auth Context
const AuthContext = React.createContext();

function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
      }
    } catch (error) {
      console.log('Not authenticated');
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, name, password) => {
    try {
      const response = await axios.post(`${API}/auth/register`, {
        email,
        name,
        password
      });
      
      const { user, access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      
      // Force navigation to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 500);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password
      });
      
      const { user, access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(user);
      
      // Force navigation to dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 500);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, setUser, register, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// Auth Component
function AuthForm() {
  const { register, login } = useAuth();
  const [language, setLanguage] = useState('en');
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', name: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    let result;
    if (isLogin) {
      result = await login(formData.email, formData.password);
    } else {
      result = await register(formData.email, formData.name, formData.password);
    }
    
    if (result.success) {
      toast({ title: isLogin ? "¡Bienvenido!" : "¡Cuenta creada exitosamente!" });
    } else {
      toast({ title: result.error, variant: "destructive" });
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center px-6">
      <div className="max-w-md w-full">
        <Card className="bg-white/10 backdrop-blur-md border-white/20">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">CSA Safety Audit</h1>
            </div>
            
            <div className="flex items-center justify-center space-x-4 mb-4">
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-20 bg-white/10 border-white/20 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">EN</SelectItem>
                  <SelectItem value="es">ES</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <CardTitle className="text-white">
              {isLogin ? (language === 'en' ? 'Login' : 'Iniciar Sesión') : (language === 'en' ? 'Register' : 'Registrarse')}
            </CardTitle>
            <CardDescription className="text-blue-200">
              {isLogin 
                ? (language === 'en' ? 'Enter your credentials to access' : 'Ingresa tus credenciales para acceder')
                : (language === 'en' ? 'Create your account to get started' : 'Crea tu cuenta para comenzar')
              }
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email" className="text-white">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="usuario@empresa.com"
                  required
                  className="bg-white/10 border-white/20 text-white placeholder-white/60"
                  data-testid="email-input"
                />
              </div>
              
              {!isLogin && (
                <div>
                  <Label htmlFor="name" className="text-white">
                    {language === 'en' ? 'Full Name' : 'Nombre Completo'}
                  </Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder={language === 'en' ? 'Your full name' : 'Tu nombre completo'}
                    required
                    className="bg-white/10 border-white/20 text-white placeholder-white/60"
                    data-testid="name-input"
                  />
                </div>
              )}
              
              <div>
                <Label htmlFor="password" className="text-white">
                  {language === 'en' ? 'Password' : 'Contraseña'}
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder={language === 'en' ? 'Your password' : 'Tu contraseña'}
                  required
                  minLength={6}
                  className="bg-white/10 border-white/20 text-white placeholder-white/60"
                  data-testid="password-input"
                />
              </div>
              
              <Button 
                type="submit" 
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="submit-button"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : null}
                {isLogin 
                  ? (language === 'en' ? 'Login' : 'Iniciar Sesión')
                  : (language === 'en' ? 'Register' : 'Registrarse')
                }
              </Button>
              
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsLogin(!isLogin)}
                className="w-full text-blue-200 hover:text-white hover:bg-white/10"
              >
                {isLogin 
                  ? (language === 'en' ? "Don't have an account? Register" : '¿No tienes cuenta? Regístrate')
                  : (language === 'en' ? 'Already have an account? Login' : '¿Ya tienes cuenta? Inicia sesión')
                }
              </Button>
            </form>
          </CardContent>
        </Card>
        
        {/* Demo Users */}
        <Card className="mt-4 bg-white/5 backdrop-blur-md border-white/10">
          <CardHeader>
            <CardTitle className="text-white text-sm">
              {language === 'en' ? 'Demo Accounts' : 'Cuentas Demo'}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-blue-200 space-y-2">
            <div>
              <strong>{language === 'en' ? 'Admin:' : 'Administrador:'}</strong> admin@csaaudit.com / admin123
            </div>
            <div>
              <strong>{language === 'en' ? 'User:' : 'Usuario:'}</strong> demo@csaaudit.com / demo123
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Landing Page Component (temporarily using TestLogin)
function LandingPage() {
  return <TestLogin />;
}

// Main Dashboard Component  
function Dashboard() {
  const { user, logout } = useAuth();
  const [language, setLanguage] = useState('en');
  const t = translations[language];
  const [activeTab, setActiveTab] = useState('dashboard');
  const [workTypes, setWorkTypes] = useState([]);
  const [audits, setAudits] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [currentAudit, setCurrentAudit] = useState(null);
  const { toast } = useToast();

  useEffect(() => {
    loadWorkTypes();
    loadAudits();
    loadStatistics();
  }, []);

  const loadWorkTypes = async () => {
    try {
      const response = await axios.get(`${API}/work-types`);
      setWorkTypes(response.data);
    } catch (error) {
      toast({ title: "Error loading work types", variant: "destructive" });
    }
  };

  const loadAudits = async () => {
    try {
      const response = await axios.get(`${API}/audits`);
      setAudits(response.data);
    } catch (error) {
      toast({ title: "Error loading audits", variant: "destructive" });
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`);
      setStatistics(response.data);
    } catch (error) {
      toast({ title: "Error loading statistics", variant: "destructive" });
    }
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-slate-800">{t.appName}</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">EN</SelectItem>
                  <SelectItem value="es">ES</SelectItem>
                </SelectContent>
              </Select>
              
              <div className="flex items-center space-x-2">
                <img 
                  src={user?.picture || 'https://via.placeholder.com/32'} 
                  alt="Profile"
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm font-medium text-slate-700">{user?.name}</span>
              </div>
              
              <Button variant="outline" onClick={logout} size="sm">
                <LogOut className="w-4 h-4 mr-2" />
                {t.logout}
              </Button>
            </div>
          </div>
        </header>

        <div className="container mx-auto px-6 py-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className={`grid w-full ${user?.role === 'admin' ? 'grid-cols-7' : 'grid-cols-5'} mb-8`}>
              <TabsTrigger value="dashboard" className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4" />
                <span>{t.dashboard}</span>
              </TabsTrigger>
              <TabsTrigger value="new-audit" className="flex items-center space-x-2">
                <FileText className="w-4 h-4" />
                <span>{t.newAudit}</span>
              </TabsTrigger>
              <TabsTrigger value="statistics" className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4" />
                <span>{t.statistics}</span>
              </TabsTrigger>
              <TabsTrigger value="team" className="flex items-center space-x-2">
                <Users className="w-4 h-4" />
                <span>{t.team || "Team"}</span>
              </TabsTrigger>
              <TabsTrigger value="settings" className="flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>{t.settings}</span>
              </TabsTrigger>
              {user?.role === 'admin' && (
                <>
                  <TabsTrigger value="admin" className="flex items-center space-x-2">
                    <Shield className="w-4 h-4" />
                    <span>Admin</span>
                  </TabsTrigger>
                  <TabsTrigger value="support" className="flex items-center space-x-2">
                    <Building className="w-4 h-4" />
                    <span>Support</span>
                  </TabsTrigger>
                </>
              )}
            </TabsList>

            {/* Dashboard Tab */}
            <TabsContent value="dashboard" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{t.totalAudits}</CardTitle>
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{statistics?.total_audits || 0}</div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{t.compliantAudits}</CardTitle>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">{statistics?.compliant_audits || 0}</div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{t.averageScore}</CardTitle>
                    <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{statistics?.average_compliance_score?.toFixed(1) || 0}%</div>
                  </CardContent>
                </Card>
              </div>
              
              {/* Recent Audits */}
              <Card>
                <CardHeader>
                  <CardTitle>{t.recentAudits}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {audits.slice(0, 5).map((audit) => (
                      <div key={audit.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium">{audit.site_name}</h4>
                          <p className="text-sm text-muted-foreground">{audit.auditor_name}</p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant={audit.status === 'completed' ? 'default' : 'secondary'}>
                            {audit.status}
                          </Badge>
                          <Button variant="outline" size="sm">
                            {t.viewAudit}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* New Audit Tab */}
            <TabsContent value="new-audit">
              <NewAuditForm 
                workTypes={workTypes} 
                language={language}
                onAuditCreated={loadAudits}
                currentAudit={currentAudit}
                setCurrentAudit={setCurrentAudit}
              />
            </TabsContent>

            {/* Statistics Tab */}
            <TabsContent value="statistics" className="space-y-6">
              {statistics && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>{t.overallScore}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-4xl font-bold mb-2">{statistics.average_compliance_score.toFixed(1)}%</div>
                      <Progress value={statistics.average_compliance_score} className="h-2" />
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle>{t.workTypeStats}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {statistics.work_type_statistics.map((stat) => (
                          <div key={stat.work_type} className="flex justify-between">
                            <span className="text-sm">{stat.work_type}</span>
                            <Badge variant="secondary">{stat.count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabsContent>

            {/* Team Tab */}
            <TabsContent value="team">
              <TeamManagement />
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings">
              <SubscriptionSettings />
            </TabsContent>

            {/* Admin Tab */}
            {user?.role === 'admin' && (
              <TabsContent value="admin">
                <AdminDashboard />
              </TabsContent>
            )}

            {/* Support Tab */}
            {user?.role === 'admin' && (
              <TabsContent value="support">
                <SupportDashboard />
              </TabsContent>
            )}
          </Tabs>
        </div>
      </div>
    </LanguageContext.Provider>
  );
}

// New Audit Form Component
function NewAuditForm({ workTypes, language, onAuditCreated, currentAudit, setCurrentAudit }) {
  const { t } = React.useContext(LanguageContext);
  const [formData, setFormData] = useState({
    siteName: '',
    auditorName: '',
    selectedWorkTypes: []
  });
  const [auditQuestions, setAuditQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [findings, setFindings] = useState([]);
  const { toast } = useToast();

  const questions = {
    en: [
      "Are all workers wearing appropriate PPE (hard hats, safety vests, steel-toed boots)?",
      "Are safety barriers and warning signs properly placed around work areas?",
      "Are emergency exits clearly marked and unobstructed?",
      "Are fire extinguishers accessible and properly maintained?",
      "Are electrical panels and equipment properly labeled and secured?",
      "Are scaffolds properly erected and inspected?",
      "Are excavations properly shored or sloped?",
      "Are material storage areas organized and safe?",
      "Are workers following proper lifting techniques?",
      "Are tools and equipment in good working condition?"
    ],
    es: [
      "¿Todos los trabajadores están usando EPP apropiado (cascos, chalecos, botas de seguridad)?",
      "¿Las barreras de seguridad y señales de advertencia están colocadas correctamente?",
      "¿Las salidas de emergencia están claramente marcadas y sin obstrucciones?",
      "¿Los extintores de incendios están accesibles y mantenidos adecuadamente?",
      "¿Los paneles eléctricos y equipos están etiquetados y asegurados correctamente?",
      "¿Los andamios están montados e inspeccionados correctamente?",
      "¿Las excavaciones están apropiadamente apuntaladas o con pendiente?",
      "¿Las áreas de almacenamiento de materiales están organizadas y seguras?",
      "¿Los trabajadores siguen técnicas apropiadas de levantamiento?",
      "¿Las herramientas y equipos están en buenas condiciones de trabajo?"
    ]
  };

  const handleStartAudit = async () => {
    if (formData.selectedWorkTypes.length === 0) {
      toast({ title: "Debe seleccionar al menos 1 tipo de trabajo", variant: "destructive" });
      return;
    }

    try {
      console.log('Sending audit data:', {
        site_name: formData.siteName,
        auditor_name: formData.auditorName,
        selected_work_types: formData.selectedWorkTypes,
        language
      });
      
      const response = await axios.post(`${API}/audits`, {
        site_name: formData.siteName,
        auditor_name: formData.auditorName,
        selected_work_types: formData.selectedWorkTypes,
        language
      });
      
      console.log('Audit created:', response.data);
      
      // Generate dynamic questions based on selected work types
      const questionsResponse = await axios.post(`${API}/audits/questions`, {
        work_types: formData.selectedWorkTypes,
        language: language
      });
      
      setCurrentAudit(response.data);
      setAuditQuestions(questionsResponse.data.questions);
      setCurrentQuestionIndex(0);
      setFindings([]);
      
      toast({ title: "Audit started successfully!" });
    } catch (error) {
      console.error('Error creating audit:', error);
      toast({ title: `Error creating audit: ${error.response?.data?.detail || error.message}`, variant: "destructive" });
    }
  };

  const handleAnswerQuestion = async (isCompliant, photo, comment, actionTaken) => {
    const currentQ = auditQuestions[currentQuestionIndex];
    const finding = {
      question: currentQ?.question || currentQ,
      work_type: currentQ?.work_type || 'general',
      is_compliant: isCompliant,
      photo_url: photo,
      comment: comment,
      action_taken: actionTaken
    };

    try {
      await axios.post(`${API}/audits/${currentAudit.id}/findings`, finding);
      setFindings([...findings, finding]);
      
      if (currentQuestionIndex < auditQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        // Complete audit
        await axios.put(`${API}/audits/${currentAudit.id}/complete`, {});
        toast({ title: "Audit completed successfully!" });
        setCurrentAudit(null);
        onAuditCreated();
      }
    } catch (error) {
      toast({ title: "Error saving finding", variant: "destructive" });
    }
  };

  if (currentAudit) {
    return <AuditProgressForm 
      audit={currentAudit}
      questions={auditQuestions}
      currentQuestion={currentQuestionIndex}
      onAnswer={handleAnswerQuestion}
      language={language}
    />;
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>{t.createAudit}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <Label htmlFor="siteName">{t.siteName}</Label>
          <Input
            id="siteName"
            value={formData.siteName}
            onChange={(e) => setFormData({...formData, siteName: e.target.value})}
            data-testid="site-name-input"
          />
        </div>
        
        <div>
          <Label htmlFor="auditorName">{t.auditorName}</Label>
          <Input
            id="auditorName"
            value={formData.auditorName}
            onChange={(e) => setFormData({...formData, auditorName: e.target.value})}
            data-testid="auditor-name-input"
          />
        </div>
        
        <div>
          <Label>{t.selectWorkTypes} ({formData.selectedWorkTypes.length} seleccionados)</Label>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {workTypes.map((workType) => (
              <div key={workType.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={workType.id}
                  checked={formData.selectedWorkTypes.includes(workType.id)}
                  onChange={(e) => {
                    const newSelected = e.target.checked
                      ? [...formData.selectedWorkTypes, workType.id]
                      : formData.selectedWorkTypes.filter(id => id !== workType.id);
                    setFormData({...formData, selectedWorkTypes: newSelected});
                  }}
                />
                <label htmlFor={workType.id} className="text-sm">
                  {language === 'en' ? workType.name_en : workType.name_es}
                </label>
              </div>
            ))}
          </div>
        </div>
        
        <Button 
          onClick={handleStartAudit}
          className="w-full"
          disabled={!formData.siteName || !formData.auditorName || formData.selectedWorkTypes.length !== 3}
          data-testid="start-audit-btn"
        >
          {t.startAudit}
        </Button>
      </CardContent>
    </Card>
  );
}

// Audit Progress Form Component
function AuditProgressForm({ audit, questions, currentQuestion, onAnswer, language }) {
  const { t } = React.useContext(LanguageContext);
  const [isCompliant, setIsCompliant] = useState(null);
  const [photo, setPhoto] = useState('');
  const [comment, setComment] = useState('');
  const [actionTaken, setActionTaken] = useState('');

  const handleSubmit = () => {
    if (isCompliant === false && (!comment || !actionTaken)) {
      return;
    }
    
    onAnswer(isCompliant, photo, comment, actionTaken);
    
    // Reset form
    setIsCompliant(null);
    setPhoto('');
    setComment('');
    setActionTaken('');
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>{t.auditProgress}</CardTitle>
        <CardDescription>
          {t.question} {currentQuestion + 1} / {questions.length}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Progress value={(currentQuestion / questions.length) * 100} />
        
        <div>
          <div className="mb-2">
            <Badge variant="outline" className="mb-2">
              {workTypes.find(wt => wt.id === questions[currentQuestion]?.work_type)?.[language === 'es' ? 'name_es' : 'name_en'] || 'General'}
            </Badge>
          </div>
          <h3 className="text-lg font-medium mb-4">{questions[currentQuestion]?.question || questions[currentQuestion]}</h3>
          
          <div className="flex space-x-4 mb-4">
            <Button
              variant={isCompliant === true ? "default" : "outline"}
              onClick={() => setIsCompliant(true)}
              className="flex items-center space-x-2"
              data-testid="compliant-btn"
            >
              <CheckCircle className="w-4 h-4" />
              <span>{t.compliant}</span>
            </Button>
            
            <Button
              variant={isCompliant === false ? "destructive" : "outline"}
              onClick={() => setIsCompliant(false)}
              className="flex items-center space-x-2"
              data-testid="non-compliant-btn"
            >
              <XCircle className="w-4 h-4" />
              <span>{t.nonCompliant}</span>
            </Button>
          </div>
        </div>
        
        <div>
          <Label htmlFor="photo">{t.addPhoto}</Label>
          <Input
            id="photo"
            type="file"
            accept="image/*"
            onChange={(e) => {
              const file = e.target.files[0];
              if (file) {
                const url = URL.createObjectURL(file);
                setPhoto(url);
              }
            }}
            data-testid="photo-input"
          />
        </div>
        
        {isCompliant === false && (
          <>
            <div>
              <Label htmlFor="comment">{t.comment}</Label>
              <Textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                required
                data-testid="comment-textarea"
              />
            </div>
            
            <div>
              <Label htmlFor="actionTaken">{t.actionTaken}</Label>
              <Textarea
                id="actionTaken"
                value={actionTaken}
                onChange={(e) => setActionTaken(e.target.value)}
                required
                data-testid="action-taken-textarea"
              />
            </div>
          </>
        )}
        
        <Button 
          onClick={handleSubmit}
          disabled={isCompliant === null || (isCompliant === false && (!comment || !actionTaken))}
          className="w-full"
          data-testid="next-question-btn"
        >
          {currentQuestion === questions.length - 1 ? t.completeAudit : t.nextQuestion}
        </Button>
      </CardContent>
    </Card>
  );
}

// Subscription Settings Component
function SubscriptionSettings() {
  const { t } = React.useContext(LanguageContext);
  const [packages, setPackages] = useState({});
  const { user } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      const response = await axios.get(`${API}/payments/packages`);
      setPackages(response.data);
    } catch (error) {
      toast({ title: "Error loading packages", variant: "destructive" });
    }
  };

  const handleUpgrade = async (packageId) => {
    try {
      const originUrl = window.location.origin;
      const response = await axios.post(`${API}/payments/checkout/session`, {
        package_id: packageId,
        origin_url: originUrl
      }, { withCredentials: true });
      
      window.location.href = response.data.url;
    } catch (error) {
      toast({ title: "Error creating checkout session", variant: "destructive" });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t.currentPlan}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{user?.subscription_plan || "No active subscription"}</p>
        </CardContent>
      </Card>
      
      <div className="grid md:grid-cols-3 gap-6">
        {Object.entries(packages).map(([key, pkg]) => (
          <Card key={key}>
            <CardHeader>
              <CardTitle>{pkg.name}</CardTitle>
              <CardDescription>
                <span className="text-2xl font-bold">${pkg.price}</span>/month
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="mb-4">
                {pkg.audits_per_month === -1 ? 'Unlimited' : pkg.audits_per_month} {t.auditsPerMonth}
              </p>
              <Button 
                onClick={() => handleUpgrade(key)}
                className="w-full"
                disabled={user?.subscription_plan === key}
                data-testid={`upgrade-${key}-btn`}
              >
                {user?.subscription_plan === key ? t.currentPlan : t.upgradeNow}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Admin Dashboard Component
function AdminDashboard() {
  const { t } = React.useContext(LanguageContext);
  const [dashboardData, setDashboardData] = useState(null);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const [dashboardRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/dashboard`, { withCredentials: true }),
        axios.get(`${API}/admin/users?limit=20`, { withCredentials: true })
      ]);
      
      setDashboardData(dashboardRes.data);
      setUsers(usersRes.data.users);
    } catch (error) {
      toast({ title: "Error loading admin data", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const updateUserPlan = async (userId, newPlan) => {
    try {
      const expiresAt = new Date();
      expiresAt.setMonth(expiresAt.getMonth() + 1);
      
      await axios.put(`${API}/admin/user/${userId}`, {
        subscription_plan: newPlan,
        subscription_expires: expiresAt.toISOString(),
        audits_used_this_month: 0
      }, { withCredentials: true });
      
      toast({ title: "User plan updated successfully!" });
      loadAdminData();
    } catch (error) {
      toast({ title: "Error updating user plan", variant: "destructive" });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-slate-800">Panel de Administración</h2>
      
      {/* Métricas Principales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Usuarios Totales</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.metrics.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              +{dashboardData?.metrics.new_users_week || 0} esta semana
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Suscriptores Activos</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{dashboardData?.metrics.active_subscribers || 0}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.metrics.conversion_rate.toFixed(1)}% conversión
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue Total</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${dashboardData?.metrics.total_revenue.toFixed(2) || 0}</div>
            <p className="text-xs text-muted-foreground">
              ${dashboardData?.metrics.current_month_revenue.toFixed(2) || 0} este mes
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auditorías Totales</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData?.metrics.total_audits || 0}</div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.metrics.monthly_audits || 0} este mes
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Usuarios por Plan */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Usuarios por Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboardData?.users_by_plan.map((plan) => (
                <div key={plan._id || 'free'} className="flex justify-between items-center">
                  <span className="text-sm font-medium">
                    {plan._id || 'Free'}
                  </span>
                  <Badge variant="secondary">{plan.count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Usuarios</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboardData?.top_users.slice(0, 5).map((user, index) => (
                <div key={index} className="flex justify-between items-center p-2 border rounded">
                  <div>
                    <p className="font-medium text-sm">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{user.audit_count} auditorías</p>
                    <Badge variant={user.plan ? 'default' : 'secondary'} className="text-xs">
                      {user.plan || 'free'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Usuarios */}
      <Card>
        <CardHeader>
          <CardTitle>Gestión de Usuarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {users.slice(0, 10).map((user) => (
              <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <img 
                    src={user.picture || 'https://via.placeholder.com/40'} 
                    alt="Profile"
                    className="w-10 h-10 rounded-full"
                  />
                  <div>
                    <h4 className="font-medium">{user.name}</h4>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {user.total_audits} auditorías • 
                      ${user.total_paid?.toFixed(2) || 0} pagado
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={user.subscription_plan ? 'default' : 'secondary'}>
                    {user.subscription_plan || 'free'}
                  </Badge>
                  {user.role === 'admin' && (
                    <Badge variant="destructive">Admin</Badge>
                  )}
                  
                  <Select onValueChange={(plan) => updateUserPlan(user.id, plan)}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Cambiar Plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="basic">Basic</SelectItem>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="enterprise">Enterprise</SelectItem>
                      <SelectItem value="">Remove Plan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Team Management Component
function TeamManagement() {
  const { user } = useAuth();
  const { t } = React.useContext(LanguageContext);
  const [teamData, setTeamData] = useState(null);
  const [invitations, setInvitations] = useState([]);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [inviteForm, setInviteForm] = useState({ email: '', name: '', role: 'auditor' });
  const { toast } = useToast();

  useEffect(() => {
    loadTeamData();
    loadInvitations();
  }, []);

  const loadTeamData = async () => {
    try {
      if (user?.organization_id) {
        const response = await axios.get(`${API}/organization/team`, { withCredentials: true });
        setTeamData(response.data);
      }
    } catch (error) {
      console.log("No organization data or error:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadInvitations = async () => {
    try {
      const response = await axios.get(`${API}/organization/invitations`, { withCredentials: true });
      setInvitations(response.data);
    } catch (error) {
      console.log("No pending invitations");
    }
  };

  const createOrganization = async () => {
    const orgName = prompt("Nombre de tu organización/empresa:");
    if (orgName) {
      try {
        await axios.post(`${API}/organization/create`, { name: orgName }, { withCredentials: true });
        toast({ title: "Organización creada exitosamente!" });
        window.location.reload();
      } catch (error) {
        toast({ title: "Error creando organización", variant: "destructive" });
      }
    }
  };

  const inviteMember = async () => {
    try {
      await axios.post(`${API}/organization/invite`, inviteForm, { withCredentials: true });
      toast({ title: "Invitación enviada exitosamente!" });
      setShowInviteDialog(false);
      setInviteForm({ email: '', name: '', role: 'auditor' });
      loadTeamData();
    } catch (error) {
      toast({ title: error.response?.data?.detail || "Error enviando invitación", variant: "destructive" });
    }
  };

  const removeMember = async (memberId) => {
    if (window.confirm("¿Estás seguro de que quieres remover este miembro?")) {
      try {
        await axios.delete(`${API}/organization/team/${memberId}`, { withCredentials: true });
        toast({ title: "Miembro removido exitosamente" });
        loadTeamData();
      } catch (error) {
        toast({ title: "Error removiendo miembro", variant: "destructive" });
      }
    }
  };

  const acceptInvitation = async (invitationId) => {
    try {
      await axios.post(`${API}/organization/invitations/${invitationId}/accept`, {}, { withCredentials: true });
      toast({ title: "Invitación aceptada!" });
      window.location.reload();
    } catch (error) {
      toast({ title: "Error aceptando invitación", variant: "destructive" });
    }
  };

  const declineInvitation = async (invitationId) => {
    try {
      await axios.post(`${API}/organization/invitations/${invitationId}/decline`, {}, { withCredentials: true });
      toast({ title: "Invitación rechazada" });
      loadInvitations();
    } catch (error) {
      toast({ title: "Error rechazando invitación", variant: "destructive" });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Si tiene invitaciones pendientes, mostrarlas primero
  if (invitations.length > 0 && !user?.organization_id) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-800">Invitaciones Pendientes</h2>
        
        {invitations.map((invitation) => (
          <Card key={invitation.id} className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle>Invitación a {invitation.organization.name}</CardTitle>
              <CardDescription>
                {invitation.inviter.name} te ha invitado como {invitation.role === 'auditor' ? 'Auditor' : 'Observador'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex space-x-4">
                <Button 
                  onClick={() => acceptInvitation(invitation.id)}
                  className="bg-green-600 hover:bg-green-700"
                >
                  Aceptar Invitación
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => declineInvitation(invitation.id)}
                >
                  Rechazar
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                Expira: {new Date(invitation.expires_at).toLocaleDateString()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Si no tiene organización, mostrar opción de crear
  if (!user?.organization_id) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-800">Gestión de Equipo</h2>
        
        <Card>
          <CardHeader>
            <CardTitle>Crear Organización</CardTitle>
            <CardDescription>
              Crea tu organización para invitar miembros de tu equipo a colaborar en las auditorías
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p>Beneficios de crear una organización:</p>
              <ul className="list-disc list-inside space-y-2 text-sm">
                <li>Invita auditores y observadores a tu equipo</li>
                <li>Comparte auditorías entre miembros</li>
                <li>Gestiona límites de auditorías por organización</li>
                <li>Vista consolidada de todas las auditorías del equipo</li>
              </ul>
              
              <Button onClick={createOrganization} className="bg-blue-600 hover:bg-blue-700">
                <Building className="w-4 h-4 mr-2" />
                Crear Mi Organización
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Vista de organización existente
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">
            {teamData?.organization.name}
          </h2>
          <p className="text-muted-foreground">
            {teamData?.team_members.length} miembros • 
            Plan {teamData?.organization.subscription_plan || 'Free'}
          </p>
        </div>
        
        {user?.organization_role === 'owner' && (
          <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Users className="w-4 h-4 mr-2" />
                Invitar Miembro
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invitar Nuevo Miembro</DialogTitle>
                <DialogDescription>
                  Invita a un miembro de tu equipo para colaborar en las auditorías
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={inviteForm.email}
                    onChange={(e) => setInviteForm({...inviteForm, email: e.target.value})}
                    placeholder="usuario@empresa.com"
                  />
                </div>
                <div>
                  <Label htmlFor="name">Nombre</Label>
                  <Input
                    id="name"
                    value={inviteForm.name}
                    onChange={(e) => setInviteForm({...inviteForm, name: e.target.value})}
                    placeholder="Nombre completo"
                  />
                </div>
                <div>
                  <Label htmlFor="role">Rol</Label>
                  <Select value={inviteForm.role} onValueChange={(role) => setInviteForm({...inviteForm, role})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auditor">Auditor - Puede crear y editar auditorías</SelectItem>
                      <SelectItem value="viewer">Observador - Solo puede ver auditorías</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={inviteMember} className="w-full">
                  Enviar Invitación
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Miembros del Equipo */}
      <Card>
        <CardHeader>
          <CardTitle>Miembros del Equipo ({teamData?.team_members.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {teamData?.team_members.map((member) => (
              <div key={member.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <img 
                    src={member.user?.picture || 'https://via.placeholder.com/40'} 
                    alt="Profile"
                    className="w-10 h-10 rounded-full"
                  />
                  <div>
                    <h4 className="font-medium">{member.user?.name}</h4>
                    <p className="text-sm text-muted-foreground">{member.user?.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {member.audit_count} auditorías • {member.completed_audits} completadas
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={member.role === 'owner' ? 'default' : 'secondary'}>
                    {member.role === 'owner' ? 'Propietario' : 
                     member.role === 'auditor' ? 'Auditor' : 'Observador'}
                  </Badge>
                  
                  {user?.organization_role === 'owner' && member.role !== 'owner' && (
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => removeMember(member.id)}
                    >
                      Remover
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Invitaciones Pendientes */}
      {teamData?.pending_invitations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Invitaciones Pendientes ({teamData.pending_invitations.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {teamData.pending_invitations.map((invitation) => (
                <div key={invitation.id} className="flex justify-between items-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <div>
                    <p className="font-medium">{invitation.invitee_name}</p>
                    <p className="text-sm text-muted-foreground">{invitation.invitee_email}</p>
                    <p className="text-xs text-muted-foreground">
                      Rol: {invitation.role === 'auditor' ? 'Auditor' : 'Observador'}
                    </p>
                  </div>
                  <Badge variant="outline">Pendiente</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Límites del Plan */}
      <Card>
        <CardHeader>
          <CardTitle>Límites del Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Auditorías este mes</p>
              <p className="text-2xl font-bold">
                {teamData?.organization.audits_used_this_month || 0}
                {teamData?.organization.subscription_plan && 
                  SUBSCRIPTION_PACKAGES[teamData.organization.subscription_plan]?.audits_per_month !== -1 
                  ? ` / ${SUBSCRIPTION_PACKAGES[teamData.organization.subscription_plan]?.audits_per_month}` 
                  : ' / Ilimitadas'
                }
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Miembros del equipo</p>
              <p className="text-2xl font-bold">
                {teamData?.organization.team_members_count || 0}
                {teamData?.organization.subscription_plan && 
                  SUBSCRIPTION_PACKAGES[teamData.organization.subscription_plan]?.team_members !== -1 
                  ? ` / ${SUBSCRIPTION_PACKAGES[teamData.organization.subscription_plan]?.team_members}` 
                  : ' / Ilimitados'
                }
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Support Dashboard Component
function SupportDashboard() {
  const [supportData, setSupportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadSupportData();
  }, []);

  const loadSupportData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/support-tickets`, { withCredentials: true });
      setSupportData(response.data);
    } catch (error) {
      toast({ title: "Error loading support data", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const createAdminUser = async () => {
    const email = prompt("Email del nuevo administrador:");
    const name = prompt("Nombre del nuevo administrador:");
    
    if (email && name) {
      try {
        await axios.post(`${API}/admin/create-admin`, { email, name }, { withCredentials: true });
        toast({ title: "Administrador creado exitosamente!" });
      } catch (error) {
        toast({ title: "Error creando administrador", variant: "destructive" });
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-slate-800">Panel de Soporte</h2>
        <Button onClick={createAdminUser} className="bg-blue-600 hover:bg-blue-700">
          Crear Administrador
        </Button>
      </div>
      
      {/* Pagos Fallidos */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span>Pagos Fallidos ({supportData?.failed_payments.length || 0})</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.failed_payments.slice(0, 5).map((payment) => (
              <div key={payment.id} className="flex justify-between items-center p-3 bg-red-50 border border-red-200 rounded">
                <div>
                  <p className="font-medium">User ID: {payment.user_id}</p>
                  <p className="text-sm text-muted-foreground">
                    ${payment.amount} • {payment.package_type}
                  </p>
                </div>
                <Badge variant="destructive">Failed</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Usuarios Activos Sin Suscripción */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-yellow-500" />
            <span>Usuarios Activos Sin Suscripción ({supportData?.active_users_no_subscription.length || 0})</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.active_users_no_subscription.slice(0, 8).map((user) => (
              <div key={user.id} className="flex justify-between items-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                <div>
                  <p className="font-medium">{user.name}</p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                  <p className="text-xs text-muted-foreground">
                    Registrado: {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant="secondary">No Plan</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Usuarios Heavy Sin Upgrade */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            <span>Usuarios con Muchas Auditorías (Sin Upgrade)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.heavy_users_no_upgrade.slice(0, 5).map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-blue-50 border border-blue-200 rounded">
                <div>
                  <p className="font-medium">{item.user.name}</p>
                  <p className="text-sm text-muted-foreground">{item.user.email}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline">{item.audit_count} auditorías</Badge>
                  <p className="text-xs text-muted-foreground mt-1">¡Candidato a upgrade!</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Comandos de Soporte */}
      <Card>
        <CardHeader>
          <CardTitle>Herramientas de Soporte</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded border">
              <h4 className="font-medium mb-2">Comandos MongoDB Útiles:</h4>
              <code className="text-sm bg-slate-100 p-2 rounded block">
                {`// Ver usuario por email
db.users.findOne({email: "usuario@email.com"});

// Extender suscripción 30 días
db.users.updateOne(
  {email: "usuario@email.com"},
  {$set: {subscription_expires: new Date(Date.now() + 30*24*60*60*1000)}}
);

// Reset auditorías mensuales
db.users.updateOne(
  {email: "usuario@email.com"},
  {$set: {audits_used_this_month: 0}}
);`}
              </code>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button variant="outline" className="justify-start">
                <Shield className="w-4 h-4 mr-2" />
                Manual de Soporte
              </Button>
              <Button variant="outline" className="justify-start">
                <FileText className="w-4 h-4 mr-2" />
                Logs del Sistema
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Session Handler Component
function SessionHandler({ children }) {
  const { setUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fragment = location.hash;
    const sessionIdMatch = fragment.match(/session_id=([^&]*)/);
    
    if (sessionIdMatch) {
      const sessionId = sessionIdMatch[1];
      handleSessionId(sessionId);
    }
  }, [location]);

  const handleSessionId = async (sessionId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/auth/session?session_id=${sessionId}`);
      const { user, session_token } = response.data;
      
      // Set cookie
      document.cookie = `session_token=${session_token}; path=/; secure; samesite=none; max-age=${7 * 24 * 60 * 60}`;
      
      setUser(user);
      
      // Clean URL and redirect
      window.history.replaceState({}, '', '/dashboard');
      navigate('/dashboard');
    } catch (error) {
      console.error('Session handling error:', error);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-lg">Processing authentication...</p>
        </div>
      </div>
    );
  }

  return children;
}

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/" />;
}

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <SessionHandler>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/subscription-success" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
          </Routes>
          <Toaster />
        </SessionHandler>
      </Router>
    </AuthProvider>
  );
}

export default App;