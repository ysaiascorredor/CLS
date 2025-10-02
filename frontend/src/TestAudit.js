import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { CheckCircle, XCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function TestAudit() {
  const [step, setStep] = useState('login'); // login, audit-form, questions, results
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState('');
  const [formData, setFormData] = useState({
    email: 'demo@csaaudit.com',
    password: 'demo123',
    siteName: 'Obra de Prueba',
    auditorName: 'Auditor Demo',
    selectedWorkTypes: ['excavation', 'height_work']
  });
  const [currentAudit, setCurrentAudit] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [findings, setFindings] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Estados para el formulario de preguntas (deben estar en el nivel superior)
  const [showNonCompliantForm, setShowNonCompliantForm] = useState(false);
  const [comment, setComment] = useState('');
  const [actionTaken, setActionTaken] = useState('');

  const workTypes = [
    { id: 'excavation', name: 'Excavation Work (Trabajo de Excavación)' },
    { id: 'height_work', name: 'Height Work (Trabajo en Altura)' },
    { id: 'welding', name: 'Welding Operations (Operaciones de Soldadura)' },
    { id: 'heavy_machinery', name: 'Heavy Machinery Operation (Operación de Maquinaria Pesada)' },
    { id: 'electrical', name: 'Electrical Work (Trabajo Eléctrico)' },
    { id: 'concrete', name: 'Concrete Work (Trabajo de Concreto)' },
    { id: 'scaffolding', name: 'Scaffolding (Andamiaje)' },
    { id: 'demolition', name: 'Demolition (Demolición)' },
    { id: 'roofing', name: 'Roofing Work (Trabajo de Techado)' },
    { id: 'painting', name: 'Painting/Coating (Pintura/Recubrimiento)' },
    { id: 'plumbing', name: 'Plumbing (Plomería)' },
    { id: 'hvac', name: 'HVAC Installation (Instalación HVAC)' },
    { id: 'steel_erection', name: 'Steel Erection (Montaje de Acero)' },
    { id: 'road_construction', name: 'Road Construction (Construcción de Carreteras)' },
    { id: 'underground_utilities', name: 'Underground Utilities (Servicios Subterráneos)' }
  ];

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(''), 5000);
  };

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });

      const { user, access_token } = response.data;
      setUser(user);
      setAccessToken(access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      showMessage(`¡Login exitoso! Bienvenido ${user.name}`);
      setStep('audit-form');
    } catch (error) {
      showMessage(`Error: ${error.response?.data?.detail || error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAudit = async () => {
    if (formData.selectedWorkTypes.length === 0) {
      showMessage('Debes seleccionar al menos 1 tipo de trabajo', 'error');
      return;
    }

    setLoading(true);
    try {
      // Create audit
      const auditResponse = await axios.post(`${API}/audits`, {
        site_name: formData.siteName,
        auditor_name: formData.auditorName,
        selected_work_types: formData.selectedWorkTypes,
        language: 'es'
      });

      setCurrentAudit(auditResponse.data);

      // Generate questions
      const questionsResponse = await axios.post(`${API}/audits/questions`, {
        work_types: formData.selectedWorkTypes,
        language: 'es'
      });

      setQuestions(questionsResponse.data.questions);
      showMessage('¡Auditoría creada exitosamente!');
      setStep('questions');
    } catch (error) {
      showMessage(`Error creando auditoría: ${error.response?.data?.detail || error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerQuestion = async (isCompliant, comment = '', actionTaken = '') => {
    const currentQ = questions[currentQuestionIndex];
    
    try {
      const finding = {
        question: currentQ.question,
        work_type: currentQ.work_type,
        is_compliant: isCompliant,
        comment: comment || '',
        action_taken: actionTaken || ''
      };

      console.log('Sending finding:', finding);

      await axios.post(`${API}/audits/${currentAudit.id}/findings`, finding);
      
      const newFindings = [...findings, finding];
      setFindings(newFindings);

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        // Complete audit
        console.log('Completing audit...');
        await axios.put(`${API}/audits/${currentAudit.id}/complete`);
        showMessage('¡Auditoría completada exitosamente!');
        setStep('results');
      }
    } catch (error) {
      console.error('Error in handleAnswerQuestion:', error);
      showMessage(`Error guardando respuesta: ${error.response?.data?.detail || error.message}`, 'error');
    }
  };

  if (step === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 p-6">
        <div className="max-w-md mx-auto mt-20">
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white text-center">🔒 CSA Safety Audit - Prueba Completa</CardTitle>
              <CardDescription className="text-blue-200 text-center">
                Paso 1: Iniciar Sesión
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-white">Email:</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="bg-white/10 border-white/20 text-white"
                />
              </div>
              <div>
                <Label className="text-white">Password:</Label>
                <Input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="bg-white/10 border-white/20 text-white"
                />
              </div>
              <Button
                onClick={handleLogin}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
              </Button>

              <div className="text-xs text-blue-300 text-center mt-4">
                <strong>Credenciales Demo:</strong><br/>
                Admin: admin@csaaudit.com / admin123<br/>
                User: demo@csaaudit.com / demo123
              </div>
            </CardContent>
          </Card>
        </div>
        
        {message && (
          <div className={`fixed top-4 right-4 p-4 rounded-lg ${
            message.type === 'error' ? 'bg-red-600' : 'bg-green-600'
          } text-white`}>
            {message.text}
          </div>
        )}
      </div>
    );
  }

  if (step === 'audit-form') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 p-6">
        <div className="max-w-2xl mx-auto mt-10">
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white">Paso 2: Crear Auditoría</CardTitle>
              <CardDescription className="text-blue-200">
                Usuario: {user?.name} | Plan: {user?.subscription_plan}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label className="text-white">Nombre del Sitio:</Label>
                <Input
                  value={formData.siteName}
                  onChange={(e) => setFormData({...formData, siteName: e.target.value})}
                  className="bg-white/10 border-white/20 text-white"
                />
              </div>
              <div>
                <Label className="text-white">Nombre del Auditor:</Label>
                <Input
                  value={formData.auditorName}
                  onChange={(e) => setFormData({...formData, auditorName: e.target.value})}
                  className="bg-white/10 border-white/20 text-white"
                />
              </div>
              <div>
                <Label className="text-white">
                  Seleccionar Tipos de Trabajo ({formData.selectedWorkTypes.length} seleccionados):
                </Label>
                <div className="grid grid-cols-1 gap-2 mt-2">
                  {workTypes.map((workType) => (
                    <div key={workType.id} className="flex items-center space-x-2 p-2 bg-white/5 rounded">
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
                      <label htmlFor={workType.id} className="text-sm text-white">
                        {workType.name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              <Button
                onClick={handleCreateAudit}
                disabled={loading || formData.selectedWorkTypes.length === 0}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? 'Creando auditoría...' : 'Iniciar Auditoría'}
              </Button>
            </CardContent>
          </Card>
        </div>
        
        {message && (
          <div className={`fixed top-4 right-4 p-4 rounded-lg ${
            message.type === 'error' ? 'bg-red-600' : 'bg-green-600'
          } text-white`}>
            {message.text}
          </div>
        )}
      </div>
    );
  }

  if (step === 'questions') {
    const currentQ = questions[currentQuestionIndex];

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 p-6">
        <div className="max-w-2xl mx-auto mt-10">
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white">Paso 3: Responder Preguntas</CardTitle>
              <CardDescription className="text-blue-200">
                Pregunta {currentQuestionIndex + 1} de {questions.length}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-blue-600/20 p-3 rounded-lg">
                <Badge variant="outline" className="mb-2 text-blue-200">
                  Tipo: {currentQ?.work_type?.toUpperCase()}
                </Badge>
              </div>
              
              <div className="text-white">
                <h3 className="text-lg font-medium mb-4">
                  {currentQ?.question}
                </h3>
              </div>

              <div className="flex space-x-4">
                <Button
                  onClick={() => handleAnswerQuestion(true)}
                  className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>✅ Cumple</span>
                </Button>
                
                <Button
                  onClick={() => setShowNonCompliantForm(true)}
                  variant="destructive"
                  className="flex items-center space-x-2"
                >
                  <XCircle className="w-4 h-4" />
                  <span>❌ No Cumple</span>
                </Button>
              </div>

              {showNonCompliantForm && (
                <div className="space-y-4 p-4 border border-red-300 rounded-lg bg-red-50/10">
                  <div>
                    <Label className="text-white">Comentario (Obligatorio):</Label>
                    <Textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Describe el problema encontrado..."
                      className="bg-white/10 border-white/20 text-white"
                    />
                  </div>
                  <div>
                    <Label className="text-white">Acción Tomada (Obligatorio):</Label>
                    <Textarea
                      value={actionTaken}
                      onChange={(e) => setActionTaken(e.target.value)}
                      placeholder="Describe la acción correctiva tomada..."
                      className="bg-white/10 border-white/20 text-white"
                    />
                  </div>
                  <Button
                    onClick={() => {
                      if (comment && actionTaken) {
                        handleAnswerQuestion(false, comment, actionTaken);
                        setShowNonCompliantForm(false);
                        setComment('');
                        setActionTaken('');
                      }
                    }}
                    disabled={!comment || !actionTaken}
                    className="w-full bg-red-600 hover:bg-red-700"
                  >
                    Continuar con No Cumple
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {message && (
          <div className={`fixed top-4 right-4 p-4 rounded-lg ${
            message.type === 'error' ? 'bg-red-600' : 'bg-green-600'
          } text-white`}>
            {message.text}
          </div>
        )}
      </div>
    );
  }

  if (step === 'results') {
    const compliantCount = findings.filter(f => f.is_compliant).length;
    const score = (compliantCount / findings.length) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 p-6">
        <div className="max-w-2xl mx-auto mt-10">
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardHeader>
              <CardTitle className="text-white text-center">🎉 ¡Auditoría Completada!</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 text-center">
              <div className="bg-green-600/20 p-6 rounded-lg">
                <div className="text-4xl font-bold text-white mb-2">
                  {score.toFixed(1)}%
                </div>
                <div className="text-green-200">Puntaje de Cumplimiento</div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-white">
                <div className="bg-white/10 p-4 rounded">
                  <div className="text-2xl font-bold">{findings.length}</div>
                  <div className="text-sm">Preguntas Respondidas</div>
                </div>
                <div className="bg-green-600/20 p-4 rounded">
                  <div className="text-2xl font-bold">{compliantCount}</div>
                  <div className="text-sm">Respuestas Conformes</div>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-white font-medium">Tipos de Trabajo Auditados:</h4>
                <div className="flex flex-wrap gap-2 justify-center">
                  {formData.selectedWorkTypes.map(type => (
                    <Badge key={type} variant="outline" className="text-blue-200">
                      {type}
                    </Badge>
                  ))}
                </div>
              </div>

              <Button
                onClick={() => window.location.reload()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Hacer Otra Auditoría
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }
}

export default TestAudit;