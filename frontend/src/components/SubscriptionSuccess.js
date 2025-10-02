import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { CheckCircle, Shield } from 'lucide-react';

function SubscriptionSuccess() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center px-6">
      <div className="max-w-md w-full">
        <Card className="bg-white/10 backdrop-blur-md border-white/20">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <Shield className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">CSA Safety Audit</h1>
            </div>
            
            <div className="flex justify-center mb-4">
              <CheckCircle className="w-16 h-16 text-green-400" />
            </div>
            
            <CardTitle className="text-white text-xl">
              ¡Suscripción Exitosa!
            </CardTitle>
            <CardDescription className="text-blue-200">
              Tu suscripción ha sido activada correctamente
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center space-y-4">
            <p className="text-white/80">
              Gracias por suscribirte a CSA Safety Audit. 
              Ya puedes acceder a todas las funcionalidades de tu plan.
            </p>
            
            <Button 
              onClick={() => navigate('/dashboard')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            >
              Ir al Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default SubscriptionSuccess;