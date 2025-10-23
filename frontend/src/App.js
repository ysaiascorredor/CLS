import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation, useParams } from 'react-router-dom';
import axios from 'axios';
import TestAudit from './TestAudit';
import SubscriptionSuccess from './components/SubscriptionSuccess';
import DemoCheckout from './components/DemoCheckout';
import JobSites from './components/JobSites';
import ProfileSettings from './components/ProfileSettings';
import Notifications from './components/Notifications';
import MyFindings from './components/MyFindings';
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
import { CheckCircle, XCircle, BarChart3, FileText, Settings, LogOut, Camera, Shield, Building, Users, User, TrendingUp, Bell, ClipboardList } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TermsOfService, PrivacyPolicy } from './components/LegalTerms';
import { JoinTeamPage } from './components/SubscriptionSuccess';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Stripe Configuration - Load from environment variables
const STRIPE_PUBLIC_KEY = process.env.REACT_APP_STRIPE_PUBLIC_KEY;

// Configure axios interceptors for authentication
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Subscription packages reference (should match backend)
const SUBSCRIPTION_PACKAGES = {
  "personal": {"price": 5.99, "name": "CSA Safety Personal", "audits_per_month": -1, "team_members": 1},
  "corporate": {"price": 49.99, "name": "CSA Safety Corporate", "audits_per_month": -1, "team_members": -1}
};

const FREE_TRIAL_AUDITS = 5; // Users get 5 free audits before requiring subscription

// Language context
const LanguageContext = React.createContext();

// Global Language Provider
function LanguageProvider({ children }) {
  const [language, setLanguage] = useState('en');
  
  const t = language === 'en' ? translations.en : translations.es;
  
  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

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
    notApplicable: "N/A",
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
    unlimitedPlan: "CSA Safety Pro",
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
    acceptInvitation: "Accept Invitation",
    createAdmin: "Create Administrator",
    supportManual: "Support Manual", 
    systemLogs: "System Logs",
    supportTools: "Support Tools",
    failedPayments: "Failed Payments",
    activeUsersNoSubscription: "Active Users Without Subscription",
    heavyUsersNoUpgrade: "Heavy Users (No Upgrade)",
    auditTrends: "Audit Trends",
    complianceTrends: "Compliance Over Time",
    workTypePerformance: "Work Type Performance",
    monthlyStats: "Monthly Statistics",
    compliantAudits: "Compliant",
    nonCompliantAudits: "Non-Compliant",
    month: "Month",
    auditCount: "Audit Count",
    complianceRate: "Compliance Rate",
    avgScore: "Average Score"
  },
  es: {
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
    notApplicable: "N/A",
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
    unlimitedPlan: "CSA Seguridad Pro",
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
    acceptInvitation: "Accept Invitation",
    createAdmin: "Create Admin",
    supportManual: "Support Manual", 
    systemLogs: "System Logs",
    supportTools: "Support Tools",
    failedPayments: "Failed Payments",
    activeUsersNoSubscription: "Active Users No Subscription",
    heavyUsersNoUpgrade: "Heavy Users No Upgrade",
    auditTrends: "Audit Trends",
    complianceTrends: "Compliance Over Time",
    workTypePerformance: "Work Type Performance",
    monthlyStats: "Monthly Statistics",
    compliantAudits: "Compliant",
    nonCompliantAudits: "Non-Compliant",
    month: "Month",
    auditCount: "Audit Count",
    complianceRate: "Compliance Rate",
    avgScore: "Average Score"
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
  const { language, setLanguage, t } = React.useContext(LanguageContext);
  
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
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 text-white"
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
        
        {/* Production ready - no demo accounts displayed */}
      </div>
    </div>
  );
}

// Landing Page Component
function LandingPage() {
  const { register, login } = useAuth();
  const { language, setLanguage, t } = React.useContext(LanguageContext);
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

  // Production mode - no test components

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
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 text-white"
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

              {/* Professional production login - no test mode */}
            </form>
          </CardContent>
        </Card>
        
        {/* Production ready - no demo accounts displayed */}
        
        {/* Legal Footer */}
        <div className="mt-8 text-center text-xs text-blue-200 space-x-4">
          <TermsOfService />
          <span>•</span>
          <PrivacyPolicy />
          <br />
          <div className="mt-2">
            © 2024 Construction Labor Solution LLC. All rights reserved.
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Dashboard Component  
function Dashboard() {
  const { user, logout } = useAuth();
  const [language, setLanguage] = useState('en');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [workTypes, setWorkTypes] = useState([]);
  const [audits, setAudits] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [auditSearch, setAuditSearch] = useState('');
  const [currentAudit, setCurrentAudit] = useState(null);
  const [jobSites, setJobSites] = useState([]);
  const { toast } = useToast();
  
  const t = language === 'en' ? translations.en : translations.es;

  useEffect(() => {
    loadWorkTypes();
    loadAudits();
    loadStatistics();
    loadJobSites();
  }, []);

  const loadJobSites = async () => {
    try {
      const response = await axios.get(`${API}/job-sites`);
      setJobSites(response.data);
    } catch (error) {
      console.error('Error loading job sites:', error);
    }
  };

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

  const downloadAuditPDF = async (auditId, siteName) => {
    try {
      const response = await axios.get(`${API}/audits/${auditId}/pdf`, {
        responseType: 'blob', // Important for file downloads
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_${siteName.replace(/\s+/g, '_')}_${auditId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast({ title: language === 'en' ? "PDF downloaded successfully!" : "PDF descargado exitosamente!" });
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast({ title: language === 'en' ? "Error downloading PDF" : "Error descargando PDF", variant: "destructive" });
    }
  };

  const viewAudit = (auditId) => {
    // Navigate to audit details or open audit view modal
    toast({ 
      title: language === 'en' ? "Opening audit details..." : "Abriendo detalles de auditoría...",
      description: `Audit ID: ${auditId}`
    });
    // TODO: Implement audit detail view
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50">
        {/* Header */}
        <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-orange-600 shadow-lg border-b border-blue-200">
          <div className="container mx-auto px-6 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-white" />
              <h1 className="text-2xl font-bold text-white">{t.appName}</h1>
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
            <TabsList className={`grid w-full ${user?.role === 'admin' ? 'grid-cols-7' : 'grid-cols-5'} mb-8 bg-white/80 backdrop-blur-sm shadow-lg rounded-xl border-0`}>
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
              <TabsTrigger value="jobsites" className="flex items-center space-x-2">
                <Building className="w-4 h-4" />
                <span>{language === 'en' ? 'Job Sites' : 'Sitios'}</span>
              </TabsTrigger>
              <TabsTrigger value="myfindings" className="flex items-center space-x-2">
                <ClipboardList className="w-4 h-4" />
                <span>{language === 'en' ? 'My Findings' : 'Mis Findings'}</span>
              </TabsTrigger>
              <TabsTrigger value="notifications" className="flex items-center space-x-2">
                <Bell className="w-4 h-4" />
                <span>{language === 'en' ? 'Notifications' : 'Notificaciones'}</span>
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
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:scale-105">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{t.totalAudits}</CardTitle>
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{audits?.length || 0}</div>
                  </CardContent>
                </Card>
                
                <Card className="hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-green-50 to-green-100 border-green-200 shadow-lg hover:scale-105">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-green-800">{t.compliantAudits}</CardTitle>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">{statistics?.compliant_audits || 0}</div>
                    <div className="text-xs text-green-600 mt-1">
                      {statistics?.total_audits > 0 ? 
                        `${((statistics?.compliant_audits || 0) / statistics?.total_audits * 100).toFixed(1)}% of total` :
                        '0% of total'
                      }
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-red-50 to-red-100 border-red-200 shadow-lg hover:scale-105">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-red-800">{t.nonCompliantAudits}</CardTitle>
                    <XCircle className="h-4 w-4 text-red-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{statistics?.non_compliant_audits || 0}</div>
                    <div className="text-xs text-red-600 mt-1">
                      {statistics?.total_audits > 0 ? 
                        `${((statistics?.non_compliant_audits || 0) / statistics?.total_audits * 100).toFixed(1)}% of total` :
                        '0% of total'
                      }
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-blue-50 to-purple-100 border-blue-200 shadow-lg hover:scale-105">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-blue-800">{language === 'en' ? 'Average Compliance' : 'Promedio de Cumplimiento'}</CardTitle>
                    <BarChart3 className="h-4 w-4 text-blue-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold" style={{
                      color: (statistics?.average_compliance_score || 0) >= 80 ? '#22c55e' : 
                             (statistics?.average_compliance_score || 0) >= 60 ? '#f59e0b' : '#ef4444'
                    }}>
                      {statistics?.average_compliance_score?.toFixed(1) || 0}%
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {language === 'en' ? 'Overall performance' : 'Rendimiento general'}
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mt-2">
                      <div 
                        className="h-full transition-all duration-300"
                        style={{
                          width: `${statistics?.average_compliance_score || 0}%`,
                          backgroundColor: (statistics?.average_compliance_score || 0) >= 80 ? '#22c55e' : 
                                         (statistics?.average_compliance_score || 0) >= 60 ? '#f59e0b' : '#ef4444'
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              {/* Free Trial Banner */}
              {!user.subscription_plan && (
                <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-4xl">⚠️</div>
                        <div>
                          <h3 className="text-lg font-bold text-yellow-800">
                            {language === 'en' ? 'Free Trial Active' : 'Trial Gratuito Activo'}
                          </h3>
                          <p className="text-yellow-700">
                            {language === 'en' 
                              ? `${user.audits_used_this_month || 0} / ${FREE_TRIAL_AUDITS} free audits used`
                              : `${user.audits_used_this_month || 0} / ${FREE_TRIAL_AUDITS} auditorías gratuitas usadas`}
                          </p>
                          {(user.audits_used_this_month || 0) >= FREE_TRIAL_AUDITS && (
                            <p className="text-red-600 font-bold mt-2">
                              {language === 'en' 
                                ? '🚫 Trial limit reached! Subscribe to continue creating audits.'
                                : '🚫 ¡Límite alcanzado! Suscríbete para continuar creando auditorías.'}
                            </p>
                          )}
                        </div>
                      </div>
                      <Button 
                        onClick={() => setActiveTab('subscription')}
                        className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700"
                      >
                        {language === 'en' ? '⭐ Upgrade Now' : '⭐ Mejorar Ahora'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
              
              {/* All Audits with Search */}
              <Card className="hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:scale-105">
                <CardHeader className="space-y-4">
                  <CardTitle>{language === 'en' ? 'All Audits' : 'Todas las Auditorías'} ({audits.length})</CardTitle>
                  <Input 
                    placeholder={language === 'en' ? 'Search audits by site name or auditor...' : 'Buscar auditorías por sitio o auditor...'}
                    className="max-w-sm"
                    onChange={(e) => setAuditSearch(e.target.value)}
                    value={auditSearch || ''}
                  />
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 max-h-96 overflow-y-auto">
                    {audits
                      .filter(audit => 
                        !auditSearch || 
                        audit.site_name?.toLowerCase().includes(auditSearch.toLowerCase()) ||
                        audit.auditor_name?.toLowerCase().includes(auditSearch.toLowerCase())
                      )
                      .map((audit) => (
                      <div key={audit.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex-grow">
                          <h4 className="font-medium">{audit.site_name}</h4>
                          <p className="text-sm text-muted-foreground">{audit.auditor_name}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(audit.created_at).toLocaleDateString()} • {audit.work_types?.join(', ') || 'N/A'}
                          </p>
                        </div>
                        <div className="flex items-center space-x-3">
                          {/* Compliance Score with Progress Bar */}
                          <div className="text-right min-w-24">
                            <div className="text-lg font-bold" style={{
                              color: audit.overall_compliance_score >= 80 ? '#22c55e' : 
                                     audit.overall_compliance_score >= 60 ? '#f59e0b' : '#ef4444'
                            }}>
                              {audit.overall_compliance_score?.toFixed(1) || 0}%
                            </div>
                            <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full transition-all duration-300"
                                style={{
                                  width: `${audit.overall_compliance_score || 0}%`,
                                  backgroundColor: audit.overall_compliance_score >= 80 ? '#22c55e' : 
                                                 audit.overall_compliance_score >= 60 ? '#f59e0b' : '#ef4444'
                                }}
                              />
                            </div>
                          </div>
                          {audit.status === 'completed' ? (
                            <Badge variant={audit.overall_compliance_score >= 80 ? "default" : "secondary"}>
                              {audit.overall_compliance_score >= 80 ? 
                                (language === 'en' ? "✅ Compliant" : "✅ Cumple") : 
                                (language === 'en' ? "⚠️ Non-Compliant" : "⚠️ No Cumple")
                              }
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
                              ⏳ {language === 'en' ? 'In Progress' : 'En Progreso'}
                            </Badge>
                          )}
                          
                          {audit.status === 'completed' ? (
                            <>
                              <Button variant="outline" size="sm" onClick={() => viewAudit(audit.id)}>
                                👁️ {language === 'en' ? 'View' : 'Ver'}
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm" 
                                onClick={() => downloadAuditPDF(audit.id, audit.site_name)}
                                className="bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
                              >
                                📄 {language === 'en' ? 'PDF' : 'PDF'}
                              </Button>
                            </>
                          ) : (
                            <Button 
                              variant="default" 
                              size="sm" 
                              onClick={() => {
                                setCurrentAudit(audit);
                                setActiveTab('new-audit');
                              }}
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                              ▶️ {language === 'en' ? 'Continue' : 'Continuar'}
                            </Button>
                          )}
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
              <StatisticsCharts language={language} />
            </TabsContent>

            {/* Job Sites Tab */}
            <TabsContent value="jobsites">
              <JobSites language={language} />
            </TabsContent>

            {/* My Findings Tab */}
            <TabsContent value="myfindings">
              <MyFindings language={language} />
            </TabsContent>

            {/* Notifications Tab */}
            <TabsContent value="notifications">
              <Notifications language={language} />
            </TabsContent>

            {/* Team Tab */}
            <TabsContent value="team">
              <TeamManagement />
            </TabsContent>

            {/* Settings Tab */}
            <TabsContent value="settings">
              <div className="space-y-6">
                <ProfileSettings language={language} user={user} onUpdate={(updatedUser) => setUser(updatedUser)} />
                <UserSettings />
                <CompanySettings />
                <SubscriptionSettings />
              </div>
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
          
          {/* Simple Support Footer - Always Visible */}
          <div className="mt-8 pt-4 border-t border-gray-200 bg-gray-50 rounded-lg">
            <div className="text-center text-sm text-gray-600 space-y-1">
              <p className="font-medium">
                {language === 'en' ? '🆘 Need Help? Contact Support:' : '🆘 ¿Necesitas Ayuda? Contáctanos:'}
              </p>
              <div className="flex justify-center items-center space-x-4">
                <a 
                  href="mailto:ysaias.corredor@clsolution.net?subject=CSA Support Request" 
                  className="text-blue-600 hover:text-blue-800 hover:underline flex items-center space-x-1"
                >
                  <span>📧</span>
                  <span>ysaias.corredor@clsolution.net</span>
                </a>
                <span className="text-gray-400">•</span>
                <a 
                  href="tel:+19198087751" 
                  className="text-green-600 hover:text-green-800 hover:underline flex items-center space-x-1"
                >
                  <span>📱</span>
                  <span>+1 (919) 808-7751</span>
                </a>
              </div>
              <p className="text-xs text-gray-500">
                Construction Labor Solution LLC • {language === 'en' ? 'Mon-Fri 9AM-6PM EST' : 'Lun-Vie 9AM-6PM EST'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </LanguageContext.Provider>
  );
}

// New Audit Form Component
function NewAuditForm({ workTypes, jobSites, language, onAuditCreated, currentAudit, setCurrentAudit }) {
  const { t } = React.useContext(LanguageContext);
  const [formData, setFormData] = useState({
    siteName: '',
    auditorName: '',
    selectedWorkTypes: [],
    selectedJobSite: null,
    siteLocation: ''
  });
  const [auditQuestions, setAuditQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [findings, setFindings] = useState([]);
  const { toast } = useToast();
  
  // Load questions when currentAudit is passed (for continuing existing audit)
  React.useEffect(() => {
    const loadAuditForContinue = async () => {
      if (currentAudit && currentAudit.id) {
        console.log('Loading audit to continue:', currentAudit);
        
        // Pre-fill form with existing audit data
        setFormData({
          siteName: currentAudit.site_name || '',
          auditorName: currentAudit.auditor_name || '',
          selectedWorkTypes: currentAudit.selected_work_types || []
        });
        
        // Load questions for this audit's work types
        try {
          const questionsResponse = await axios.post(`${API}/audits/questions`, {
            work_types: currentAudit.selected_work_types || [],
            language: language
          });
          
          setAuditQuestions(questionsResponse.data.questions || []);
          
          // Set current question index based on existing findings
          const existingFindings = currentAudit.findings || [];
          setFindings(existingFindings);
          setCurrentQuestionIndex(existingFindings.length); // Start where they left off
          
          console.log(`Loaded ${questionsResponse.data.questions.length} questions, continuing from question ${existingFindings.length + 1}`);
        } catch (error) {
          console.error('Error loading questions for audit:', error);
          toast({ title: "Error loading audit questions", variant: "destructive" });
        }
      }
    };
    
    loadAuditForContinue();
  }, [currentAudit]);

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

  const handleAnswerQuestion = async (complianceStatus, photo, comment, actionTaken) => {
    const currentQ = auditQuestions[currentQuestionIndex];
    const finding = {
      question: currentQ?.question || currentQ,
      work_type: currentQ?.work_type || 'general',
      compliance_status: complianceStatus,
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
      workTypes={workTypes}
    />;
  }

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>{t.createAudit}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Job Site Selector */}
        <div>
          <Label htmlFor="jobSiteSelect">
            {language === 'en' ? 'Select Job Site (Optional)' : 'Seleccionar Sitio (Opcional)'}
          </Label>
          <select
            id="jobSiteSelect"
            className="w-full border rounded px-3 py-2 bg-white"
            value={formData.selectedJobSite || ''}
            onChange={async (e) => {
              const siteId = e.target.value;
              setFormData({...formData, selectedJobSite: siteId});
              
              // If a site is selected, load its info
              if (siteId) {
                try {
                  const response = await axios.get(`${API}/job-sites/${siteId}`);
                  const site = response.data;
                  setFormData({
                    ...formData,
                    selectedJobSite: siteId,
                    siteName: site.name,
                    siteLocation: site.location || ''
                  });
                } catch (error) {
                  console.error('Error loading site:', error);
                }
              } else {
                setFormData({...formData, selectedJobSite: '', siteName: '', siteLocation: ''});
              }
            }}
          >
            <option value="">{language === 'en' ? '-- Manual Entry --' : '-- Entrada Manual --'}</option>
            {jobSites.map(site => (
              <option key={site.id} value={site.id}>
                {site.name} {site.location ? `(${site.location})` : ''}
              </option>
            ))}
          </select>
        </div>
        
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
          disabled={!formData.siteName || !formData.auditorName || formData.selectedWorkTypes.length === 0}
          data-testid="start-audit-btn"
        >
          {t.startAudit}
        </Button>
      </CardContent>
    </Card>
  );
}

// Audit Progress Form Component
function AuditProgressForm({ audit, questions, currentQuestion, onAnswer, language, workTypes }) {
  const { t } = React.useContext(LanguageContext);
  const [complianceStatus, setComplianceStatus] = useState(null); // "compliant", "non_compliant", "n/a"
  const [photo, setPhoto] = useState('');
  const [comment, setComment] = useState('');
  const [actionTaken, setActionTaken] = useState('');

  const handleSubmit = () => {
    if (complianceStatus === 'non_compliant' && (!comment || !actionTaken)) {
      return;
    }
    
    onAnswer(complianceStatus, photo, comment, actionTaken);
    
    // Reset form
    setComplianceStatus(null);
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
              variant={complianceStatus === 'compliant' ? "default" : "outline"}
              onClick={() => setComplianceStatus('compliant')}
              className="flex items-center space-x-2"
              data-testid="compliant-btn"
            >
              <CheckCircle className="w-4 h-4" />
              <span>{t.compliant}</span>
            </Button>
            
            <Button
              variant={complianceStatus === 'non_compliant' ? "destructive" : "outline"}
              onClick={() => setComplianceStatus('non_compliant')}
              className="flex items-center space-x-2"
              data-testid="non-compliant-btn"
            >
              <XCircle className="w-4 h-4" />
              <span>{t.nonCompliant}</span>
            </Button>
            
            <Button
              variant={complianceStatus === 'n/a' ? "secondary" : "outline"}
              onClick={() => setComplianceStatus('n/a')}
              className="flex items-center space-x-2"
              data-testid="na-btn"
            >
              <span className="w-4 h-4 text-center">—</span>
              <span>{t.notApplicable}</span>
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
        
        {complianceStatus === 'non_compliant' && (
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
          disabled={complianceStatus === null || (complianceStatus === 'non_compliant' && (!comment || !actionTaken))}
          className="w-full"
          data-testid="next-question-btn"
        >
          {currentQuestion === questions.length - 1 ? t.completeAudit : t.nextQuestion}
        </Button>
      </CardContent>
    </Card>
  );
}

// User Settings Component (Password Change)
function UserSettings() {
  const { language } = React.useContext(LanguageContext);
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const { toast } = useToast();

  const changePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast({ 
        title: language === 'en' ? "❌ Password Mismatch" : "❌ Contraseñas No Coinciden",
        description: language === 'en' ? "New passwords don't match" : "Las contraseñas nuevas no coinciden",
        variant: "destructive" 
      });
      return;
    }

    if (passwordForm.new_password.length < 6) {
      toast({ 
        title: language === 'en' ? "❌ Password Too Short" : "❌ Contraseña Muy Corta",
        description: language === 'en' ? "Password must be at least 6 characters" : "La contraseña debe tener al menos 6 caracteres",
        variant: "destructive" 
      });
      return;
    }

    try {
      await axios.post(`${API}/auth/change-password`, {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      });

      toast({ 
        title: language === 'en' ? "✅ Password Changed" : "✅ Contraseña Cambiada",
        description: language === 'en' ? "Your password has been updated successfully" : "Tu contraseña se actualizó exitosamente"
      });

      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });

    } catch (error) {
      const errorMessage = error.response?.data?.detail || (language === 'en' ? "Error changing password" : "Error cambiando contraseña");
      toast({ 
        title: language === 'en' ? "❌ Password Change Failed" : "❌ Error Cambiando Contraseña",
        description: errorMessage,
        variant: "destructive" 
      });
    }
  };

  const cancelSubscription = async () => {
    try {
      await axios.post(`${API}/payments/cancel-subscription`);
      
      toast({ 
        title: language === 'en' ? "✅ Subscription Cancelled" : "✅ Suscripción Cancelada",
        description: language === 'en' ? "Your subscription has been cancelled. Access continues until expiration." : "Tu suscripción ha sido cancelada. El acceso continúa hasta la expiración."
      });

      setShowCancelDialog(false);

    } catch (error) {
      toast({ 
        title: language === 'en' ? "❌ Cancellation Failed" : "❌ Error en Cancelación",
        description: error.response?.data?.detail || (language === 'en' ? "Error cancelling subscription" : "Error cancelando suscripción"),
        variant: "destructive" 
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Password Change */}
      <Card>
        <CardHeader>
          <CardTitle>
            {language === 'en' ? 'Change Password' : 'Cambiar Contraseña'}
          </CardTitle>
          <CardDescription>
            {language === 'en' ? 'Update your account password' : 'Actualiza la contraseña de tu cuenta'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>{language === 'en' ? 'Current Password' : 'Contraseña Actual'}</Label>
            <Input
              type="password"
              value={passwordForm.old_password}
              onChange={(e) => setPasswordForm({...passwordForm, old_password: e.target.value})}
              placeholder={language === 'en' ? 'Enter current password' : 'Ingresa contraseña actual'}
            />
          </div>
          <div>
            <Label>{language === 'en' ? 'New Password' : 'Nueva Contraseña'}</Label>
            <Input
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm({...passwordForm, new_password: e.target.value})}
              placeholder={language === 'en' ? 'Enter new password (6+ characters)' : 'Nueva contraseña (6+ caracteres)'}
            />
          </div>
          <div>
            <Label>{language === 'en' ? 'Confirm New Password' : 'Confirmar Nueva Contraseña'}</Label>
            <Input
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
              placeholder={language === 'en' ? 'Confirm new password' : 'Confirmar nueva contraseña'}
            />
          </div>
          <Button onClick={changePassword} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
            {language === 'en' ? '🔐 Change Password' : '🔐 Cambiar Contraseña'}
          </Button>
        </CardContent>
      </Card>

      {/* Cancel Subscription */}
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-700">
            {language === 'en' ? 'Cancel Subscription' : 'Cancelar Suscripción'}
          </CardTitle>
          <CardDescription>
            {language === 'en' ? 'Cancel your subscription (access continues until expiration)' : 'Cancela tu suscripción (el acceso continúa hasta la expiración)'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
            <DialogTrigger asChild>
              <Button variant="destructive">
                {language === 'en' ? '❌ Cancel Subscription' : '❌ Cancelar Suscripción'}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{language === 'en' ? 'Confirm Cancellation' : 'Confirmar Cancelación'}</DialogTitle>
                <DialogDescription>
                  {language === 'en' 
                    ? 'Are you sure you want to cancel your subscription? You will continue to have access until your current billing period ends.'
                    : '¿Estás seguro de que quieres cancelar tu suscripción? Continuarás teniendo acceso hasta que termine tu período de facturación actual.'
                  }
                </DialogDescription>
              </DialogHeader>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowCancelDialog(false)}>
                  {language === 'en' ? 'Keep Subscription' : 'Mantener Suscripción'}
                </Button>
                <Button variant="destructive" onClick={cancelSubscription}>
                  {language === 'en' ? 'Yes, Cancel' : 'Sí, Cancelar'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}

// Company Settings Component
function CompanySettings() {
  const { t } = React.useContext(LanguageContext);
  const [companyData, setCompanyData] = useState({
    company_name: '',
    company_logo: null
  });
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadCompanySettings();
  }, []);

  const loadCompanySettings = async () => {
    try {
      const response = await axios.get(`${API}/company/settings`);
      setCompanyData(response.data);
    } catch (error) {
      console.error('Error loading company settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCompanyData({...companyData, company_logo: e.target.result});
      };
      reader.readAsDataURL(file);
    }
  };

  const saveSettings = async () => {
    try {
      await axios.post(`${API}/admin/company/settings`, companyData);
      toast({ title: t.language === 'en' ? "Settings saved successfully!" : "Configuración guardada exitosamente!" });
    } catch (error) {
      toast({ title: "Error saving settings", variant: "destructive" });
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
      <Card>
        <CardHeader>
          <CardTitle>
            {t.language === 'en' ? 'Company Settings' : 'Configuración de Empresa'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>
              {t.language === 'en' ? 'Company Name' : 'Nombre de Empresa'}
            </Label>
            <Input
              value={companyData.company_name}
              onChange={(e) => setCompanyData({...companyData, company_name: e.target.value})}
              placeholder="Construction Labor Solution LLC"
            />
          </div>
          
          <div>
            <Label>
              {t.language === 'en' ? 'Company Logo' : 'Logo de Empresa'}
            </Label>
            <Input
              type="file"
              accept="image/*"
              onChange={handleLogoUpload}
              className="mt-2"
            />
            {companyData.company_logo && (
              <div className="mt-2">
                <img 
                  src={companyData.company_logo} 
                  alt="Company Logo" 
                  className="max-w-32 max-h-32 object-contain border"
                />
              </div>
            )}
          </div>
          
          <Button onClick={saveSettings} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
            {t.language === 'en' ? 'Save Settings' : 'Guardar Configuración'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// Subscription Settings Component - Single Unlimited Plan
function SubscriptionSettings() {
  const { t, language } = React.useContext(LanguageContext);
  const { user } = useAuth();
  const { toast } = useToast();

  const handleSubscribe = async (planId) => {
    try {
      console.log(`🚀 Starting subscription process for ${planId}`);
      
      const originUrl = window.location.origin;
      const requestData = {
        package_id: planId,
        origin_url: originUrl
      };
      
      console.log('📤 Sending subscription request:', requestData);
      
      const response = await axios.post(`${API}/payments/checkout/session`, requestData);
      
      console.log('📥 Checkout response:', response.data);
      
      if (response.data.url) {
        const planName = SUBSCRIPTION_PACKAGES[planId]?.name || planId;
        toast({
          title: language === 'en' ? `🔄 Redirecting to Stripe...` : `🔄 Redirigiendo a Stripe...`,
          description: language === 'en' ? `Opening secure payment for ${planName}` : `Abriendo pago seguro para ${planName}`
        });
        window.location.href = response.data.url;
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (error) {
      console.error('❌ Subscription error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast({ 
        title: language === 'en' ? "❌ Error creating subscription" : "❌ Error creando suscripción", 
        description: `${errorMessage}. Please try again or contact support.`,
        variant: "destructive" 
      });
    }
  };

  const isSubscribed = user?.subscription_plan !== null && user?.subscription_plan !== undefined;
  const currentPlan = user?.subscription_plan;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-center mb-6">
        {language === 'en' ? 'Choose Your Plan' : 'Elige Tu Plan'}
      </h2>
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Personal Plan */}
        <Card className={`hover:shadow-xl transition-all duration-300 ${currentPlan === 'personal' ? 'border-4 border-green-500' : 'border-2 border-blue-200'}`}>
          <CardHeader className="text-center">
            <div className="mb-4">
              <span className="text-5xl">👤</span>
            </div>
            <CardTitle className="text-2xl font-bold text-blue-600">
              {language === 'en' ? 'Personal' : 'Personal'}
            </CardTitle>
            {currentPlan === 'personal' && (
              <Badge variant="default" className="mt-2 bg-green-500">
                {language === 'en' ? 'Current Plan' : 'Plan Actual'}
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-800">$5.99</p>
              <p className="text-gray-600">{language === 'en' ? 'per month' : 'por mes'}</p>
            </div>
            <ul className="space-y-3">
              <li className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span>{language === 'en' ? 'Unlimited audits' : 'Auditorías ilimitadas'}</span>
              </li>
              <li className="flex items-center">
                <User className="w-5 h-5 text-blue-500 mr-2" />
                <span>{language === 'en' ? '1 user only' : '1 usuario solamente'}</span>
              </li>
              <li className="flex items-center">
                <FileText className="w-5 h-5 text-purple-500 mr-2" />
                <span>{language === 'en' ? 'PDF reports' : 'Reportes PDF'}</span>
              </li>
            </ul>
            {currentPlan !== 'personal' && (
              <Button 
                onClick={() => handleSubscribe('personal')} 
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={currentPlan === 'corporate'}
              >
                {currentPlan === 'corporate' 
                  ? (language === 'en' ? 'Downgrade' : 'Cambiar') 
                  : (language === 'en' ? 'Subscribe' : 'Suscribirse')}
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Corporate Plan */}
        <Card className={`hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-purple-50 to-blue-50 ${currentPlan === 'corporate' ? 'border-4 border-green-500' : 'border-2 border-purple-200'}`}>
          <CardHeader className="text-center">
            <div className="mb-4">
              <span className="text-5xl">💼</span>
            </div>
            <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              {language === 'en' ? 'Corporate' : 'Corporativa'}
            </CardTitle>
            {currentPlan === 'corporate' && (
              <Badge variant="default" className="mt-2 bg-green-500">
                {language === 'en' ? 'Current Plan' : 'Plan Actual'}
              </Badge>
            )}
            <Badge variant="secondary" className="mt-2">
              {language === 'en' ? 'Most Popular' : 'Más Popular'}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <p className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">$49.99</p>
              <p className="text-gray-600">{language === 'en' ? 'per month' : 'por mes'}</p>
            </div>
            <ul className="space-y-3">
              <li className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span className="font-bold">{language === 'en' ? 'Unlimited audits' : 'Auditorías ilimitadas'}</span>
              </li>
              <li className="flex items-center">
                <Users className="w-5 h-5 text-blue-500 mr-2" />
                <span className="font-bold">{language === 'en' ? 'Unlimited team members' : 'Miembros de equipo ilimitados'}</span>
              </li>
              <li className="flex items-center">
                <Building className="w-5 h-5 text-purple-500 mr-2" />
                <span>{language === 'en' ? 'Organization management' : 'Gestión de organización'}</span>
              </li>
              <li className="flex items-center">
                <FileText className="w-5 h-5 text-green-500 mr-2" />
                <span>{language === 'en' ? 'Advanced PDF reports' : 'Reportes PDF avanzados'}</span>
              </li>
            </ul>
            {currentPlan !== 'corporate' && (
              <Button 
                onClick={() => handleSubscribe('corporate')} 
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                {language === 'en' ? 'Subscribe' : 'Suscribirse'}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Free Trial Info */}
      {!isSubscribed && (
        <Card className="bg-yellow-50 border-yellow-300">
          <CardContent className="pt-6">
            <p className="text-center text-yellow-800">
              ⚠️ {language === 'en' 
                ? `You have a free trial of 5 audits. After that, you need to subscribe.`
                : `Tienes un trial gratuito de 5 auditorías. Después, necesitas suscribirte.`}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Duplicate code removed

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
        axios.get(`${API}/admin/dashboard`),
        axios.get(`${API}/admin/users?limit=20`)
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
      
      // Handle "none" as removing the plan
      const planToSet = newPlan === 'none' ? null : newPlan;
      const expiresAtToSet = newPlan === 'none' ? null : expiresAt.toISOString();
      
      await axios.put(`${API}/admin/user/${userId}`, {
        subscription_plan: planToSet,
        subscription_expires: expiresAtToSet,
        audits_used_this_month: 0
      });
      
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
          <CardTitle className="flex items-center justify-between">
            <span>Gestión de Usuarios</span>
            <Badge variant="outline">{users.length} usuarios</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {users.filter(u => u.email !== 'admin@csaaudit.com' && u.email !== 'demo@csaaudit.com').slice(0, 15).map((user) => (
              <div key={user.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center space-x-4 flex-1">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{user.name}</h4>
                    <p className="text-sm text-gray-500">{user.email}</p>
                  </div>
                  <div className="text-right mr-4">
                    <p className="text-sm font-medium text-gray-700">{user.total_audits || 0} auditorías</p>
                    <p className="text-xs text-gray-500">${user.total_paid?.toFixed(2) || '0.00'}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={user.subscription_plan ? 'default' : 'secondary'} className="min-w-24 justify-center">
                    {user.subscription_plan || 'free'}
                  </Badge>
                  {user.role === 'admin' && (
                    <Badge variant="destructive">Admin</Badge>
                  )}
                  
                  <Select onValueChange={(plan) => updateUserPlan(user.id, plan)}>
                    <SelectTrigger className="w-36">
                      <SelectValue placeholder="Cambiar Plan" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="basic">Basic</SelectItem>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="enterprise">Enterprise</SelectItem>
                      <SelectItem value="none">Remove Plan</SelectItem>
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
  const { t, language } = React.useContext(LanguageContext);
  const [teamData, setTeamData] = useState(null);
  const [invitations, setInvitations] = useState([]);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showCreateUserDialog, setShowCreateUserDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [inviteForm, setInviteForm] = useState({ email: '', name: '', role: 'auditor' });
  const [createUserForm, setCreateUserForm] = useState({ email: '', name: '', role: 'auditor', password: '' });
  const { toast } = useToast();

  useEffect(() => {
    loadAllTeamData();
  }, []);

  const loadAllTeamData = async () => {
    try {
      setLoading(true);
      console.log('🔍 Loading all team data for user:', {
        userId: user?.id,
        organizationId: user?.organization_id,
        organizationRole: user?.organization_role
      });
      
      if (user?.organization_id) {
        console.log('📡 Fetching organization team data and invitations...');
        
        const [teamResponse, invitationsResponse] = await Promise.allSettled([
          axios.get(`${API}/organization/team`),
          axios.get(`${API}/organization/invitations`)
        ]);

        if (teamResponse.status === 'fulfilled') {
          console.log('✅ Team data loaded:', teamResponse.value.data);
          setTeamData(teamResponse.value.data);
        } else {
          console.error('❌ Error loading team data:', teamResponse.reason);
        }

        if (invitationsResponse.status === 'fulfilled') {
          console.log('✅ Invitations loaded:', invitationsResponse.value.data);
          setInvitations(invitationsResponse.value.data);
        } else {
          console.log('⚠️ No pending invitations or error loading them');
        }
      } else {
        console.log('⚠️ User has no organization_id, showing create organization UI');
      }
    } catch (error) {
      console.error("❌ Unexpected error loading team data:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeamData = async () => {
    // Keep for manual refresh calls
    await loadAllTeamData();
  };

  const loadInvitations = async () => {
    // Keep for manual refresh calls
    try {
      const response = await axios.get(`${API}/organization/invitations`);
      setInvitations(response.data);
    } catch (error) {
      console.log("No pending invitations");
    }
  };

  const createOrganization = async () => {
    const orgName = prompt("Nombre de tu organización/empresa:");
    if (orgName) {
      try {
        console.log('🏢 Creating organization:', orgName);
        
        const response = await axios.post(`${API}/organization/create`, { name: orgName });
        
        console.log('✅ Organization created:', response.data);
        
        toast({ 
          title: language === 'en' ? "Organization created successfully!" : "¡Organización creada exitosamente!" 
        });
        
        // Reload team data instead of full page
        loadTeamData();
        
      } catch (error) {
        console.error('❌ Organization creation error:', error);
        
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        toast({ 
          title: language === 'en' ? "Error creating organization" : "Error creando organización",
          description: errorMessage,
          variant: "destructive" 
        });
      }
    }
  };

  const inviteMember = async () => {
    console.log('🚀 FORCE CREATE USER INSTEAD OF INVITE - HIJACKED FUNCTION EXECUTED');
    console.log('📋 Form data:', inviteForm);
    
    // Clear any previous error toasts
    document.querySelectorAll('[data-sonner-toaster]').forEach(el => el.innerHTML = '');
    
    try {
      console.log('📡 Making API call to CREATE USER endpoint...');
      console.log('🔗 URL:', `${API}/organization/create-user`);
      
      // *** FORCE USE NEW CREATE USER SYSTEM ***
      const response = await axios.post(`${API}/organization/create-user`, {
        email: inviteForm.email,
        name: inviteForm.name,
        role: inviteForm.role,
        password: undefined  // Auto-generate password
      });
      
      console.log('✅ API Response received:', response.data);
      
      const passwordInfo = response.data.user.temporary_password;
      
      // Show success notification  
      toast({ 
        title: "🎉 ¡USUARIO CREADO EXITOSAMENTE!",
        description: `CREDENCIALES PARA ${inviteForm.name}:\n📧 Email: ${inviteForm.email}\n🔐 Password: ${passwordInfo}\n\n¡Guarda estas credenciales!`,
        duration: 15000  // Show longer so user can copy
      });
      
      console.log('🎉 SUCCESS! User created successfully');
      console.log('🔑 SHARE THESE CREDENTIALS:');
      console.log(`👤 Name: ${inviteForm.name}`);
      console.log(`📧 Email: ${inviteForm.email}`);
      console.log(`🔐 Password: ${passwordInfo}`);
      console.log('💾 SAVE THESE CREDENTIALS NOW!');
      
      // Close dialog and clear form
      setShowInviteDialog(false);
      setInviteForm({ email: '', name: '', role: 'auditor' });
      
      // Force reload team data
      console.log('🔄 Reloading team data to show new member...');
      setTimeout(() => {
        loadAllTeamData();
      }, 1000);
      
    } catch (error) {
      console.error('💥 CRITICAL ERROR creating user:', error);
      console.error('📋 Error details:', error.response?.data);
      
      const errorMessage = error.response?.data?.detail || `Error creando usuario: ${error.message}`;
      toast({ 
        title: "💥 ERROR CRITICO CREANDO USUARIO", 
        description: errorMessage,
        variant: "destructive",
        duration: 8000
      });
    }
  };

  const createTeamUser = async () => {
    console.log('🚀 CREATE USER FUNCTION CALLED - Starting user creation...');
    console.log('📋 Form data:', createUserForm);
    console.log('🔗 API endpoint:', `${API}/organization/create-user`);
    
    try {
      
      const response = await axios.post(`${API}/organization/create-user`, {
        email: createUserForm.email,
        name: createUserForm.name,
        role: createUserForm.role,
        password: createUserForm.password || undefined  // Only send if provided
      });
      
      const passwordInfo = response.data.user.temporary_password;
      const passwordType = response.data.password_type;
      
      toast({ 
        title: language === 'en' ? "✅ User Created Successfully!" : "✅ ¡Usuario Creado Exitosamente!",
        description: language === 'en' 
          ? `${createUserForm.name} can login with: ${createUserForm.email} / ${passwordInfo} ${passwordType === 'generated' ? '(auto-generated)' : '(your password)'}`
          : `${createUserForm.name} puede iniciar con: ${createUserForm.email} / ${passwordInfo} ${passwordType === 'generated' ? '(auto-generada)' : '(tu contraseña)'}`
      });
      
      console.log('✅ User created successfully:', response.data);
      
      setShowCreateUserDialog(false);
      setCreateUserForm({ email: '', name: '', role: 'auditor', password: '' });
      loadAllTeamData(); // Reload to show new team member
      
    } catch (error) {
      console.error('❌ Create user error:', error);
      
      const errorMessage = error.response?.data?.detail || (language === 'en' ? "Error creating user" : "Error creando usuario");
      toast({ 
        title: language === 'en' ? "❌ User Creation Failed" : "❌ Error Creando Usuario", 
        description: errorMessage,
        variant: "destructive" 
      });
    }
  };

  const deleteMember = async (memberId) => {
    console.log('🗑️ DELETE FUNCTION CALLED for member:', memberId);
    console.log('🔍 Type of memberId:', typeof memberId);
    console.log('🔍 MemberId value:', memberId);
    
    if (!memberId) {
      console.error('❌ ERROR: memberId is null/undefined');
      toast({ 
        title: "❌ Error al Eliminar", 
        description: "ID de usuario no válido",
        variant: "destructive" 
      });
      return;
    }
    
    const confirmMessage = "⚠️ ¿Estás seguro de que quieres eliminar este usuario? ¡Esta acción no se puede deshacer!";
      
    console.log('🔔 Showing confirmation dialog...');
    if (window.confirm(confirmMessage)) {
      console.log('✅ User confirmed deletion, proceeding...');
      console.log('🔗 DELETE URL:', `${API}/organization/remove-user/${memberId}`);
      
      try {
        console.log('🚀 Making DELETE request...');
        const response = await axios.delete(`${API}/organization/remove-user/${memberId}`);
        console.log('✅ DELETE request successful:', response);
        
        toast({ 
          title: "✅ Usuario eliminado exitosamente",
          description: `Usuario con ID ${memberId} eliminado correctamente`
        });
        
        console.log('🔄 Reloading team data...');
        loadAllTeamData(); // Correct function call
        
      } catch (error) {
        console.error('❌ Delete user error - FULL ERROR:', error);
        console.error('❌ Error response:', error.response);
        console.error('❌ Error status:', error.response?.status);
        console.error('❌ Error data:', error.response?.data);
        
        const errorMessage = error.response?.data?.detail || `Error eliminando usuario: ${error.message}`;
        toast({ 
          title: "❌ Error al Eliminar", 
          description: errorMessage,
          variant: "destructive" 
        });
      }
    } else {
      console.log('❌ User cancelled deletion');
    }
  };

  const acceptInvitation = async (invitationId) => {
    try {
      console.log('✅ Accepting invitation:', invitationId);
      
      await axios.post(`${API}/organization/invitations/${invitationId}/accept`, {});
      
      toast({ 
        title: language === 'en' ? "Invitation accepted!" : "¡Invitación aceptada!" 
      });
      
      // Reload to get updated user data with organization
      window.location.reload();
      
    } catch (error) {
      console.error('❌ Accept invitation error:', error);
      
      toast({ 
        title: language === 'en' ? "Error accepting invitation" : "Error aceptando invitación", 
        variant: "destructive" 
      });
    }
  };

  const declineInvitation = async (invitationId) => {
    try {
      console.log('❌ Declining invitation:', invitationId);
      
      await axios.post(`${API}/organization/invitations/${invitationId}/decline`, {});
      
      toast({ 
        title: language === 'en' ? "Invitation declined" : "Invitación rechazada" 
      });
      
      loadInvitations();
      
    } catch (error) {
      console.error('❌ Decline invitation error:', error);
      
      toast({ 
        title: language === 'en' ? "Error declining invitation" : "Error rechazando invitación", 
        variant: "destructive" 
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // If user has pending invitations, show them first
  if (invitations.length > 0 && !user?.organization_id) {
    return (
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-800">Pending Invitations</h2>
        
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
            <CardTitle>Create Organization</CardTitle>
            <CardDescription>
              Create your organization to invite team members to collaborate on audits
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
              
              <Button onClick={createOrganization} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                <Building className="w-4 h-4 mr-2" />
                Create My Organization
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
          <Dialog open={showCreateUserDialog} onOpenChange={setShowCreateUserDialog}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700" data-testid="create-user-button">
                <Users className="w-4 h-4 mr-2" />
                🚀 CREATE USER NOW
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>🚀 CREATE NEW TEAM USER</DialogTitle>
                <DialogDescription>
                  Create a user account directly with email and password - NO invitations needed!
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={createUserForm.email}
                    onChange={(e) => setCreateUserForm({...createUserForm, email: e.target.value})}
                    placeholder="empleado@empresa.com"
                  />
                </div>
                <div>
                  <Label htmlFor="name">{language === 'en' ? 'Full Name' : 'Nombre Completo'}</Label>
                  <Input
                    id="name"
                    type="text"
                    value={createUserForm.name}
                    onChange={(e) => setCreateUserForm({...createUserForm, name: e.target.value})}
                    placeholder={language === 'en' ? 'Juan Pérez' : 'Juan Pérez'}
                  />
                </div>
                <div>
                  <Label htmlFor="role">{language === 'en' ? 'Role' : 'Rol'}</Label>
                  <Select value={createUserForm.role} onValueChange={(value) => setCreateUserForm({...createUserForm, role: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auditor">{language === 'en' ? 'Auditor - Can create and edit audits' : 'Auditor - Puede crear y editar auditorías'}</SelectItem>
                      <SelectItem value="viewer">{language === 'en' ? 'Observer - Can only view audits' : 'Observador - Solo puede ver auditorías'}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="password">{language === 'en' ? 'Password (Optional)' : 'Contraseña (Opcional)'}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={createUserForm.password}
                    onChange={(e) => setCreateUserForm({...createUserForm, password: e.target.value})}
                    placeholder={language === 'en' ? 'Leave empty for auto-generated' : 'Dejar vacío para auto-generar'}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    {language === 'en' 
                      ? 'If empty, a secure password will be generated automatically' 
                      : 'Si está vacío, se generará una contraseña segura automáticamente'
                    }
                  </p>
                </div>
                <Button onClick={createTeamUser} className="w-full bg-green-600 hover:bg-green-700" data-testid="submit-create-user">
                  🚀 CREATE USER ACCOUNT NOW
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Team Members */}
      <Card>
        <CardHeader>
          <CardTitle>{language === 'en' ? 'Team Members' : 'Miembros del Equipo'} ({teamData?.team_members.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {teamData?.team_members.map((member) => (
              <div key={member.user_id || member.id} className="flex items-center justify-between p-4 border rounded-lg">
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
                    {member.role === 'owner' ? (language === 'en' ? 'Owner' : 'Propietario') : 
                     member.role === 'auditor' ? (language === 'en' ? 'Auditor' : 'Auditor') : (language === 'en' ? 'Observer' : 'Observador')}
                  </Badge>
                  
                  {user?.organization_role === 'owner' && member.role !== 'owner' && (
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => {
                        console.log('🎯 DELETE BUTTON CLICKED for member:', member);
                        console.log('🔍 Member user_id:', member.user_id);
                        console.log('🔍 Member user.id:', member.user?.id);
                        console.log('🔍 Member data:', JSON.stringify(member));
                        // Use user_id which is the actual user ID
                        deleteMember(member.user_id || member.user?.id);
                      }}
                      data-testid={`delete-button-${member.user_id}`}
                    >
                      {language === 'en' ? 'Delete' : 'Eliminar'}
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Pending Invitations */}
      {teamData?.pending_invitations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{language === 'en' ? 'Pending Invitations' : 'Invitaciones Pendientes'} ({teamData.pending_invitations.length})</CardTitle>
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
                  <Badge variant="outline">{language === 'en' ? 'Pending' : 'Pendiente'}</Badge>
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
              <p className="text-sm text-muted-foreground">Team members</p>
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

// Statistics Charts Component
function StatisticsCharts({ language }) {
  const { t } = React.useContext(LanguageContext);
  const [statistics, setStatistics] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    loadStatisticsData();
  }, []);

  const loadStatisticsData = async () => {
    try {
      setLoading(true);
      const [statsResponse, chartsResponse] = await Promise.all([
        axios.get(`${API}/statistics`),
        axios.get(`${API}/statistics/charts`)
      ]);
      
      setStatistics(statsResponse.data);
      setChartData(chartsResponse.data);
    } catch (error) {
      console.error('Error loading statistics:', error);
      toast({ title: "Error loading statistics", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!statistics || !chartData) {
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">
          {language === 'en' ? 'No data available. Complete some audits to see statistics.' : 'No hay datos disponibles. Completa algunas auditorías para ver estadísticas.'}
        </p>
      </div>
    );
  }

  // Color scheme
  const colors = {
    compliant: '#22c55e',
    nonCompliant: '#ef4444',
    primary: '#3b82f6',
    secondary: '#8b5cf6',
    accent: '#f59e0b'
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t.totalAudits}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statistics.total_audits}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t.compliantAudits}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{statistics.compliant_audits}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t.nonCompliantAudits}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{statistics.non_compliant_audits}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t.averageScore}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{statistics.average_compliance_score.toFixed(1)}%</div>
            <Progress value={statistics.average_compliance_score} className="h-2 mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Audit Trends */}
        <Card>
          <CardHeader>
            <CardTitle>{t.auditTrends}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData.monthly_summary}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="total_audits" 
                  stroke={colors.primary}
                  name={t.auditCount}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Compliance Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>{t.complianceTrends}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData.compliance_trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="compliant" 
                  stackId="1"
                  stroke={colors.compliant}
                  fill={colors.compliant}
                  name={t.compliantAudits}
                />
                <Area 
                  type="monotone" 
                  dataKey="non_compliant" 
                  stackId="1"
                  stroke={colors.nonCompliant}
                  fill={colors.nonCompliant}
                  name={t.nonCompliantAudits}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Work Type Performance */}
        <Card>
          <CardHeader>
            <CardTitle>{t.workTypePerformance}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.work_type_performance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="work_type" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar 
                  dataKey="avg_score" 
                  fill={colors.accent}
                  name={t.avgScore}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Compliance Rate Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>{t.overallScore}</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: t.compliantAudits, value: statistics.compliant_audits, fill: colors.compliant },
                    { name: t.nonCompliantAudits, value: statistics.non_compliant_audits, fill: colors.nonCompliant }
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Summary Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t.monthlyStats}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">{t.month}</th>
                  <th className="text-right p-2">{t.totalAudits}</th>
                  <th className="text-right p-2">{t.compliantAudits}</th>
                  <th className="text-right p-2">{t.nonCompliantAudits}</th>
                  <th className="text-right p-2">{t.avgScore}</th>
                  <th className="text-right p-2">{t.complianceRate}</th>
                </tr>
              </thead>
              <tbody>
                {chartData.monthly_summary.map((month, index) => (
                  <tr key={index} className="border-b">
                    <td className="p-2 font-medium">{month.month}</td>
                    <td className="text-right p-2">{month.total_audits}</td>
                    <td className="text-right p-2 text-green-600">{month.compliant}</td>
                    <td className="text-right p-2 text-red-600">{month.non_compliant}</td>
                    <td className="text-right p-2">{month.avg_score}%</td>
                    <td className="text-right p-2">
                      {month.total_audits > 0 ? Math.round((month.compliant / month.total_audits) * 100) : 0}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Support Dashboard Component
function SupportDashboard() {
  const { t } = React.useContext(LanguageContext);
  const [supportData, setSupportData] = useState(null);
  const [systemLogs, setSystemLogs] = useState("");
  const [loading, setLoading] = useState(true);
  const [showManual, setShowManual] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
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
    const email = prompt(t.language === 'en' ? "New administrator email:" : "Email del nuevo administrador:");
    const name = prompt(t.language === 'en' ? "New administrator name:" : "Nombre del nuevo administrador:");
    
    if (email && name) {
      try {
        await axios.post(`${API}/admin/create-admin`, { email, name }, { withCredentials: true });
        toast({ title: t.language === 'en' ? "Administrator created successfully!" : "Administrador creado exitosamente!" });
      } catch (error) {
        toast({ title: t.language === 'en' ? "Error creating administrator" : "Error creando administrador", variant: "destructive" });
      }
    }
  };

  const loadSystemLogs = async () => {
    try {
      const response = await axios.get(`${API}/admin/logs`, { withCredentials: true });
      setSystemLogs(response.data.logs);
      setShowLogs(true);
    } catch (error) {
      toast({ title: t.language === 'en' ? "Error loading system logs" : "Error cargando logs del sistema", variant: "destructive" });
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
        <h2 className="text-3xl font-bold text-slate-800">
          {t.language === 'en' ? t.supportPanel : 'Panel de Soporte'}
        </h2>
        <div className="flex space-x-2">
          <Button onClick={createAdminUser} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
            {t.language === 'en' ? t.createAdmin : 'Crear Administrador'}
          </Button>
          <Button onClick={() => setShowManual(true)} variant="outline">
            {t.language === 'en' ? t.supportManual : 'Manual de Soporte'}
          </Button>
          <Button onClick={loadSystemLogs} variant="outline">
            {t.language === 'en' ? t.systemLogs : 'Logs del Sistema'}
          </Button>
        </div>
      </div>
      
      {/* Failed Payments / Pagos Fallidos */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <XCircle className="w-5 h-5 text-red-500" />
            <span>
              {t.language === 'en' ? t.failedPayments : 'Pagos Fallidos'} ({supportData?.failed_payments?.length || 0})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.failed_payments?.slice(0, 5).map((payment) => (
              <div key={payment.id} className="flex justify-between items-center p-3 bg-red-50 border border-red-200 rounded">
                <div>
                  <p className="font-medium">User ID: {payment.user_id}</p>
                  <p className="text-sm text-muted-foreground">
                    ${payment.amount} • {payment.package_type}
                  </p>
                </div>
                <Badge variant="destructive">Failed</Badge>
              </div>
            )) || <p className="text-muted-foreground">No failed payments found</p>}
          </div>
        </CardContent>
      </Card>

      {/* Active Users Without Subscription / Usuarios Activos Sin Suscripción */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-yellow-500" />
            <span>
              {t.language === 'en' ? t.activeUsersNoSubscription : 'Usuarios Activos Sin Suscripción'} ({supportData?.active_users_no_subscription?.length || 0})
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.active_users_no_subscription?.slice(0, 8).map((user) => (
              <div key={user.id} className="flex justify-between items-center p-3 bg-yellow-50 border border-yellow-200 rounded">
                <div>
                  <p className="font-medium">{user.name}</p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.language === 'en' ? 'Registered:' : 'Registrado:'} {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Badge variant="secondary">No Plan</Badge>
              </div>
            )) || <p className="text-muted-foreground">No users without subscription found</p>}
          </div>
        </CardContent>
      </Card>

      {/* Heavy Users No Upgrade / Usuarios Heavy Sin Upgrade */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            <span>
              {t.language === 'en' ? t.heavyUsersNoUpgrade : 'Usuarios con Muchas Auditorías (Sin Upgrade)'}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {supportData?.heavy_users_no_upgrade?.slice(0, 5).map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-blue-50 border border-blue-200 rounded">
                <div>
                  <p className="font-medium">{item.user.name}</p>
                  <p className="text-sm text-muted-foreground">{item.user.email}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline">
                    {item.audit_count} {t.language === 'en' ? 'audits' : 'auditorías'}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-1">
                    {t.language === 'en' ? 'Upgrade candidate!' : '¡Candidato a upgrade!'}
                  </p>
                </div>
              </div>
            )) || <p className="text-muted-foreground">No heavy users found</p>}
          </div>
        </CardContent>
      </Card>

      {/* Support Tools / Herramientas de Soporte */}
      <Card>
        <CardHeader>
          <CardTitle>
            {t.language === 'en' ? t.supportTools : 'Herramientas de Soporte'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded border">
              <h4 className="font-medium mb-2">
                {t.language === 'en' ? 'Useful MongoDB Commands:' : 'Comandos MongoDB Útiles:'}
              </h4>
              <code className="text-sm bg-slate-100 p-2 rounded block whitespace-pre">
                {t.language === 'en' ? 
                  `// Find user by email
db.users.findOne({email: "user@email.com"});

// Extend subscription 30 days
db.users.updateOne(
  {email: "user@email.com"},
  {$set: {subscription_expires: new Date(Date.now() + 30*24*60*60*1000)}}
);

// Reset monthly audits
db.users.updateOne(
  {email: "user@email.com"},
  {$set: {audits_used_this_month: 0}}
);` :
                  `// Ver usuario por email
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
          </div>
        </CardContent>
      </Card>

      {/* Contact Support Information */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-blue-800">
            <Shield className="w-5 h-5" />
            <span>
              {t.language === 'en' ? 'Technical Support Contact' : 'Contacto de Soporte Técnico'}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">📧</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">Email Support</p>
                    <p className="text-blue-600 hover:underline">
                      <a href="mailto:ysaias.corredor@clsolution.net">
                        ysaias.corredor@clsolution.net
                      </a>
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">📱</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">
                      {t.language === 'en' ? 'Phone Support' : 'Soporte Telefónico'}
                    </p>
                    <p className="text-green-600 hover:underline">
                      <a href="tel:+19198087751">+1 (919) 808-7751</a>
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">🏢</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">
                      {t.language === 'en' ? 'Company' : 'Empresa'}
                    </p>
                    <p className="text-purple-600">Construction Labor Solution LLC</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-3">
                <div className="p-4 bg-white rounded border">
                  <h4 className="font-semibold text-gray-800 mb-2">
                    {t.language === 'en' ? '🕐 Support Hours' : '🕐 Horarios de Soporte'}
                  </h4>
                  <p className="text-sm text-gray-600">
                    {t.language === 'en' ? 
                      'Monday - Friday: 9:00 AM - 6:00 PM EST' : 
                      'Lunes - Viernes: 9:00 AM - 6:00 PM EST'}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {t.language === 'en' ? 
                      'Response time: Within 24 hours' : 
                      'Tiempo de respuesta: Dentro de 24 horas'}
                  </p>
                </div>
                
                <div className="flex space-x-2">
                  <Button 
                    onClick={() => window.open('mailto:ysaias.corredor@clsolution.net?subject=CSA Support Request')}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex-1"
                  >
                    📧 {t.language === 'en' ? 'Send Email' : 'Enviar Email'}
                  </Button>
                  <Button 
                    onClick={() => window.open('tel:+19198087751')}
                    variant="outline"
                    className="border-green-600 text-green-600 hover:bg-green-50 flex-1"
                  >
                    📱 {t.language === 'en' ? 'Call Now' : 'Llamar'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Support Manual Dialog */}
      {showManual && (
        <Dialog open={showManual} onOpenChange={setShowManual}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {t.language === 'en' ? 'Support Manual' : 'Manual de Soporte'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">
                {t.language === 'en' ? 'CSA Construction Safety Audit - Support Guide' : 'CSA Auditoría de Seguridad en Construcción - Guía de Soporte'}
              </h3>
              
              <div className="space-y-3">
                <h4 className="font-medium">
                  {t.language === 'en' ? '1. User Management' : '1. Gestión de Usuarios'}
                </h4>
                <ul className="list-disc ml-4 space-y-1 text-sm">
                  <li>
                    {t.language === 'en' ? 
                      'Create admin users using the "Create Administrator" button' : 
                      'Crear usuarios admin usando el botón "Crear Administrador"'}
                  </li>
                  <li>
                    {t.language === 'en' ? 
                      'Monitor user subscriptions in the Admin dashboard' : 
                      'Monitorear suscripciones de usuarios en el panel de Admin'}
                  </li>
                  <li>
                    {t.language === 'en' ? 
                      'Track failed payments and assist users with billing issues' : 
                      'Rastrear pagos fallidos y ayudar a usuarios con problemas de facturación'}
                  </li>
                </ul>
                
                <h4 className="font-medium">
                  {t.language === 'en' ? '2. System Monitoring' : '2. Monitoreo del Sistema'}
                </h4>
                <ul className="list-disc ml-4 space-y-1 text-sm">
                  <li>
                    {t.language === 'en' ? 
                      'Check system logs regularly for errors or issues' : 
                      'Revisar logs del sistema regularmente para errores o problemas'}
                  </li>
                  <li>
                    {t.language === 'en' ? 
                      'Monitor application performance and database health' : 
                      'Monitorear rendimiento de la aplicación y salud de la base de datos'}
                  </li>
                </ul>
                
                <h4 className="font-medium">
                  {t.language === 'en' ? '3. Common Issues' : '3. Problemas Comunes'}
                </h4>
                <ul className="list-disc ml-4 space-y-1 text-sm">
                  <li>
                    {t.language === 'en' ? 
                      'Login issues: Check user credentials and JWT tokens' : 
                      'Problemas de login: Verificar credenciales de usuario y tokens JWT'}
                  </li>
                  <li>
                    {t.language === 'en' ? 
                      'Payment failures: Verify Stripe integration and webhook settings' : 
                      'Fallas de pago: Verificar integración de Stripe y configuración de webhooks'}
                  </li>
                  <li>
                    {t.language === 'en' ? 
                      'Audit creation errors: Check work types and database connectivity' : 
                      'Errores de creación de auditorías: Verificar tipos de trabajo y conectividad de base de datos'}
                  </li>
                </ul>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* System Logs Dialog */}
      {showLogs && (
        <Dialog open={showLogs} onOpenChange={setShowLogs}>
          <DialogContent className="max-w-4xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>
                {t.language === 'en' ? 'System Logs' : 'Logs del Sistema'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  {t.language === 'en' ? 'Latest system logs:' : 'Últimos logs del sistema:'}
                </p>
                <Button onClick={loadSystemLogs} variant="outline" size="sm">
                  {t.language === 'en' ? 'Refresh' : 'Actualizar'}
                </Button>
              </div>
              <div className="bg-black text-green-400 p-4 rounded font-mono text-sm max-h-96 overflow-y-auto">
                <pre>{systemLogs || (t.language === 'en' ? 'Loading logs...' : 'Cargando logs...')}</pre>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
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
    <LanguageProvider>
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
              <Route path="/test" element={<TestAudit />} />
              <Route path="/subscription-success" element={<SubscriptionSuccess />} />
              <Route path="/demo-checkout" element={<DemoCheckout />} />
              <Route path="/join-team/:invitationId" element={<JoinTeamPage />} />
            </Routes>
            <Toaster />
          </SessionHandler>
        </Router>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;