import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Shield, CreditCard } from 'lucide-react';

function DemoCheckout() {
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);
  const [formData, setFormData] = useState({
    cardNumber: '4242 4242 4242 4242',
    expiryDate: '12/25',
    cvv: '123',
    name: 'Demo User'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setProcessing(true);
    
    // Simulate payment processing
    setTimeout(() => {
      setProcessing(false);
      navigate('/subscription-success');
    }, 2000);
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
            
            <div className="flex justify-center mb-4">
              <CreditCard className="w-16 h-16 text-blue-400" />
            </div>
            
            <CardTitle className="text-white text-xl">
              🎭 Demo Checkout
            </CardTitle>
            <CardDescription className="text-blue-200">
              Simulación de pago - Modo Demo
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="name" className="text-white">Nombre en la tarjeta</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="bg-white/10 border-white/20 text-white placeholder-white/60"
                  disabled
                />
              </div>
              
              <div>
                <Label htmlFor="cardNumber" className="text-white">Número de tarjeta</Label>
                <Input
                  id="cardNumber"
                  value={formData.cardNumber}
                  onChange={(e) => setFormData({...formData, cardNumber: e.target.value})}
                  className="bg-white/10 border-white/20 text-white placeholder-white/60"
                  disabled
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="expiryDate" className="text-white">Fecha de vencimiento</Label>
                  <Input
                    id="expiryDate"
                    value={formData.expiryDate}
                    onChange={(e) => setFormData({...formData, expiryDate: e.target.value})}
                    className="bg-white/10 border-white/20 text-white placeholder-white/60"
                    disabled
                  />
                </div>
                
                <div>
                  <Label htmlFor="cvv" className="text-white">CVV</Label>
                  <Input
                    id="cvv"
                    value={formData.cvv}
                    onChange={(e) => setFormData({...formData, cvv: e.target.value})}
                    className="bg-white/10 border-white/20 text-white placeholder-white/60"
                    disabled
                  />
                </div>
              </div>
              
              <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-3 mt-4">
                <p className="text-yellow-200 text-sm text-center">
                  🎭 Este es un pago simulado para demostración.
                  <br />
                  No se procesará ningún cargo real.
                </p>
              </div>
              
              <Button 
                type="submit" 
                disabled={processing}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white mt-4"
              >
                {processing ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Procesando pago demo...
                  </div>
                ) : (
                  'Completar Pago Demo'
                )}
              </Button>
              
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate('/dashboard')}
                className="w-full text-blue-200 hover:text-white hover:bg-white/10"
              >
                Cancelar y volver al Dashboard
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default DemoCheckout;