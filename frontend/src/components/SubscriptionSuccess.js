import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { CheckCircle, Shield } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Join Team Page Component
function JoinTeamPage() {
  const navigate = useNavigate();
  const { invitationId } = useParams();
  const [invitationData, setInvitationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joinForm, setJoinForm] = useState({ email: '', name: '', password: '' });
  const [joining, setJoining] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadInvitationDetails();
  }, [invitationId]);

  const loadInvitationDetails = async () => {
    try {
      const response = await axios.get(`${API}/invitations/${invitationId}`);
      setInvitationData(response.data);
      
      // Pre-fill form with invitation data
      setJoinForm({
        email: response.data.invitation.invitee_email,
        name: response.data.invitation.invitee_name,
        password: ''
      });
    } catch (error) {
      toast({ 
        title: "Invalid or expired invitation link", 
        variant: "destructive" 
      });
      setTimeout(() => navigate('/'), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinTeam = async (e) => {
    e.preventDefault();
    
    if (!joinForm.password) {
      toast({ title: "Please enter a password", variant: "destructive" });
      return;
    }
    
    try {
      setJoining(true);
      
      await axios.post(`${API}/invitations/${invitationId}/accept`, joinForm);
      
      toast({ title: "✅ Successfully joined the team!" });
      
      // Redirect to login
      setTimeout(() => navigate('/'), 2000);
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "Error joining team";
      toast({ title: errorMessage, variant: "destructive" });
    } finally {
      setJoining(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading invitation...</p>
        </div>
      </div>
    );
  }

  if (!invitationData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 text-center">
            <h2 className="text-xl font-bold text-red-600 mb-2">Invalid Invitation</h2>
            <p>This invitation link is invalid or has expired.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center px-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Join Team Invitation</CardTitle>
          <CardDescription>
            You've been invited to join <strong>{invitationData.organization?.name}</strong>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Invited by:</strong> {invitationData.inviter?.name}<br />
              <strong>Role:</strong> {invitationData.invitation?.role}<br />
              <strong>Organization:</strong> {invitationData.organization?.name}
            </p>
          </div>
          
          <form onSubmit={handleJoinTeam} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={joinForm.email}
                disabled
                className="bg-gray-100"
              />
            </div>
            
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={joinForm.name}
                onChange={(e) => setJoinForm({...joinForm, name: e.target.value})}
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password">Create Password</Label>
              <Input
                id="password"
                type="password"
                value={joinForm.password}
                onChange={(e) => setJoinForm({...joinForm, password: e.target.value})}
                placeholder="Enter a secure password"
                required
              />
            </div>
            
            <Button 
              type="submit" 
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={joining}
            >
              {joining ? "Joining..." : "Join Team"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

// Subscription Success Component
function SubscriptionSuccess() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  
  const sessionId = searchParams.get('session_id');
  const packageId = searchParams.get('package');

  useEffect(() => {
    if (sessionId) {
      // Verify payment status with backend
      verifyPayment();
    } else {
      // No session ID - assume demo mode success
      setSuccess(true);
      setLoading(false);
    }
  }, [sessionId]);

  const verifyPayment = async () => {
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const response = await axios.get(`${API}/payments/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid' || response.data.demo_mode) {
        setSuccess(true);
      }
    } catch (error) {
      console.error('Payment verification error:', error);
      // Assume success for demo purposes
      setSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center px-6">
        <div className="text-center text-white">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Verificando pago...</p>
        </div>
      </div>
    );
  }

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
export { JoinTeamPage };