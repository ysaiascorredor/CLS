import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
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
    selectWorkTypes: "Select 3 Work Types",
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
    viewAudit: "View Audit"
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
    selectWorkTypes: "Seleccionar 3 Tipos de Trabajo",
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
    viewAudit: "Ver Auditoría"
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
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      console.log('Not authenticated');
    } finally {
      setLoading(false);
    }
  };

  const login = (redirectUrl) => {
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    console.log('Auth URL:', authUrl);
    console.log('Redirecting to:', authUrl);
    window.location.href = authUrl;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// Landing Page Component
function LandingPage() {
  const { login } = useAuth();
  const [language, setLanguage] = useState('en');
  const t = translations[language];
  
  const handleLogin = () => {
    // Temporary demo mode - simulate login
    const demoUser = {
      id: 'demo-user-123',
      email: 'demo@csaaudit.com',
      name: 'Demo User',
      picture: 'https://via.placeholder.com/150',
      subscription_plan: 'professional'
    };
    setUser(demoUser);
    window.location.hash = '#demo-mode';
    window.location.pathname = '/dashboard';
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800">
        {/* Header */}
        <header className="fixed w-full top-0 z-50 bg-white/10 backdrop-blur-md border-b border-white/20">
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">{t.appName}</h1>
            </div>
            
            <div className="flex items-center space-x-6">
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="w-20 bg-white/10 border-white/20 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">EN</SelectItem>
                  <SelectItem value="es">ES</SelectItem>
                </SelectContent>
              </Select>
              
              <nav className="hidden md:flex space-x-6 text-white/90">
                <a href="#features" className="hover:text-blue-400 transition-colors">{t.features}</a>
                <a href="#pricing" className="hover:text-blue-400 transition-colors">{t.pricing}</a>
              </nav>
              
              <Button onClick={handleLogin} className="bg-blue-600 hover:bg-blue-700 text-white">
                {t.login}
              </Button>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <div className="container mx-auto text-center">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
                {t.welcome}
              </h2>
              <p className="text-xl md:text-2xl text-blue-200 mb-12 max-w-3xl mx-auto">
                {t.subtitle}
              </p>
              
              <div className="grid md:grid-cols-3 gap-8 mb-12">
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
                  <Building className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Multi-Work Type Audits</h3>
                  <p className="text-blue-200">Audit 15 different construction work types with specialized checklists</p>
                </div>
                
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
                  <Camera className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Photo Documentation</h3>
                  <p className="text-blue-200">Capture evidence with mandatory photos for non-compliance issues</p>
                </div>
                
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
                  <BarChart3 className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">Advanced Analytics</h3>
                  <p className="text-blue-200">Track compliance trends and identify improvement opportunities</p>
                </div>
              </div>
              
              <Button 
                onClick={handleLogin}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white px-12 py-4 text-lg rounded-full"
                data-testid="get-started-btn"
              >
                {t.login}
              </Button>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 px-6 bg-white/5">
          <div className="container mx-auto">
            <h2 className="text-4xl font-bold text-center text-white mb-12">{t.pricing}</h2>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
                <CardHeader>
                  <CardTitle className="text-2xl">{t.basicPlan}</CardTitle>
                  <CardDescription className="text-blue-200">
                    <span className="text-3xl font-bold">$29.99</span>/month
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-blue-200 mb-4">50 {t.auditsPerMonth}</p>
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">{t.choosePlan}</Button>
                </CardContent>
              </Card>
              
              <Card className="bg-blue-600/20 backdrop-blur-md border-blue-400/50 text-white transform scale-105">
                <CardHeader>
                  <CardTitle className="text-2xl">{t.professionalPlan}</CardTitle>
                  <CardDescription className="text-blue-200">
                    <span className="text-3xl font-bold">$79.99</span>/month
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-blue-200 mb-4">200 {t.auditsPerMonth}</p>
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">{t.choosePlan}</Button>
                </CardContent>
              </Card>
              
              <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
                <CardHeader>
                  <CardTitle className="text-2xl">{t.enterprisePlan}</CardTitle>
                  <CardDescription className="text-blue-200">
                    <span className="text-3xl font-bold">$199.99</span>/month
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-blue-200 mb-4">Unlimited {t.auditsPerMonth}</p>
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">{t.choosePlan}</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </div>
    </LanguageContext.Provider>
  );
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
      const response = await axios.get(`${API}/audits`, { withCredentials: true });
      setAudits(response.data);
    } catch (error) {
      toast({ title: "Error loading audits", variant: "destructive" });
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`, { withCredentials: true });
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
            <TabsList className={`grid w-full ${user?.role === 'admin' ? 'grid-cols-6' : 'grid-cols-4'} mb-8`}>
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
              <TabsTrigger value="settings" className="flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>{t.settings}</span>
              </TabsTrigger>
              {user?.role === 'admin' && (
                <>
                  <TabsTrigger value="admin" className="flex items-center space-x-2">
                    <Users className="w-4 h-4" />
                    <span>Admin</span>
                  </TabsTrigger>
                  <TabsTrigger value="support" className="flex items-center space-x-2">
                    <Shield className="w-4 h-4" />
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

            {/* Settings Tab */}
            <TabsContent value="settings">
              <SubscriptionSettings />
            </TabsContent>
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
    if (formData.selectedWorkTypes.length !== 3) {
      toast({ title: "Must select exactly 3 work types", variant: "destructive" });
      return;
    }

    try {
      const response = await axios.post(`${API}/audits`, {
        ...formData,
        language
      }, { withCredentials: true });
      
      setCurrentAudit(response.data);
      setAuditQuestions(questions[language]);
      setCurrentQuestionIndex(0);
      setFindings([]);
      
      toast({ title: "Audit started successfully!" });
    } catch (error) {
      toast({ title: "Error creating audit", variant: "destructive" });
    }
  };

  const handleAnswerQuestion = async (isCompliant, photo, comment, actionTaken) => {
    const finding = {
      question: auditQuestions[currentQuestionIndex],
      is_compliant: isCompliant,
      photo_url: photo,
      comment: comment,
      action_taken: actionTaken
    };

    try {
      await axios.post(`${API}/audits/${currentAudit.id}/findings`, finding, { withCredentials: true });
      setFindings([...findings, finding]);
      
      if (currentQuestionIndex < auditQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        // Complete audit
        await axios.put(`${API}/audits/${currentAudit.id}/complete`, {}, { withCredentials: true });
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
          <Label>{t.selectWorkTypes} ({formData.selectedWorkTypes.length}/3)</Label>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {workTypes.map((workType) => (
              <div key={workType.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={workType.id}
                  checked={formData.selectedWorkTypes.includes(workType.id)}
                  onChange={(e) => {
                    const newSelected = e.target.checked
                      ? [...formData.selectedWorkTypes, workType.id].slice(0, 3)
                      : formData.selectedWorkTypes.filter(id => id !== workType.id);
                    setFormData({...formData, selectedWorkTypes: newSelected});
                  }}
                  disabled={formData.selectedWorkTypes.length >= 3 && !formData.selectedWorkTypes.includes(workType.id)}
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
          <h3 className="text-lg font-medium mb-4">{questions[currentQuestion]}</h3>
          
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