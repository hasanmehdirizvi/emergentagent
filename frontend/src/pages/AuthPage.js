import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, Code, Mail, Lock, User } from 'lucide-react';
import { toast } from 'sonner';

const AuthPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  
  const { login, signup } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const result = await login(loginData.email, loginData.password);
      if (result.success) {
        toast.success('Welcome back!');
        navigate('/dashboard');
      } else {
        setError(result.error);
        toast.error(result.error);
      }
    } catch (error) {
      setError('Login failed. Please try again.');
      toast.error('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (signupData.password !== signupData.confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      toast.error('Passwords do not match');
      return;
    }

    if (signupData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      setIsLoading(false);
      toast.error('Password must be at least 6 characters long');
      return;
    }

    try {
      const result = await signup(signupData.username, signupData.email, signupData.password);
      if (result.success) {
        toast.success('Account created successfully! Welcome to PythonQuest!');
        navigate('/dashboard');
      } else {
        setError(result.error);
        toast.error(result.error);
      }
    } catch (error) {
      setError('Signup failed. Please try again.');
      toast.error('Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className=\"min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8\">
      <div className=\"w-full max-w-md space-y-8\">
        {/* Header */}
        <div className=\"text-center\">
          <div className=\"flex justify-center mb-4\">
            <div className=\"p-3 rounded-full bg-gradient-to-br from-orange-400 to-amber-500\">
              <Code className=\"h-8 w-8 text-white\" />
            </div>
          </div>
          <h2 className=\"text-3xl font-bold gradient-text mb-2\">Welcome to PythonQuest</h2>
          <p className=\"text-gray-600\">Start your Python learning journey today</p>
        </div>

        {/* Auth Forms */}
        <Card className=\"glass-card border-0\">
          <Tabs defaultValue=\"login\" className=\"w-full\">
            <CardHeader className=\"pb-0\">
              <TabsList className=\"grid w-full grid-cols-2 mb-4\">
                <TabsTrigger value=\"login\" data-testid=\"login-tab\">Login</TabsTrigger>
                <TabsTrigger value=\"signup\" data-testid=\"signup-tab\">Sign Up</TabsTrigger>
              </TabsList>
            </CardHeader>

            <CardContent>
              {error && (
                <Alert className=\"mb-4 border-red-200 bg-red-50\" data-testid=\"auth-error\">
                  <AlertDescription className=\"text-red-800\">{error}</AlertDescription>
                </Alert>
              )}

              {/* Login Form */}
              <TabsContent value=\"login\" className=\"space-y-4\">
                <form onSubmit={handleLogin} className=\"space-y-4\">
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"login-email\">Email</Label>
                    <div className=\"relative\">
                      <Mail className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"login-email\"
                        type=\"email\"
                        placeholder=\"Enter your email\"
                        className=\"pl-10\"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                        data-testid=\"login-email\"
                      />
                    </div>
                  </div>
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"login-password\">Password</Label>
                    <div className=\"relative\">
                      <Lock className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"login-password\"
                        type=\"password\"
                        placeholder=\"Enter your password\"
                        className=\"pl-10\"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                        data-testid=\"login-password\"
                      />
                    </div>
                  </div>
                  <Button
                    type=\"submit\"
                    className=\"w-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600\"
                    disabled={isLoading}
                    data-testid=\"login-submit\"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className=\"mr-2 h-4 w-4 animate-spin\" />
                        Logging in...
                      </>
                    ) : (
                      'Login'
                    )}
                  </Button>
                </form>
              </TabsContent>

              {/* Signup Form */}
              <TabsContent value=\"signup\" className=\"space-y-4\">
                <form onSubmit={handleSignup} className=\"space-y-4\">
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"signup-username\">Username</Label>
                    <div className=\"relative\">
                      <User className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"signup-username\"
                        type=\"text\"
                        placeholder=\"Choose a username\"
                        className=\"pl-10\"
                        value={signupData.username}
                        onChange={(e) => setSignupData({ ...signupData, username: e.target.value })}
                        required
                        data-testid=\"signup-username\"
                      />
                    </div>
                  </div>
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"signup-email\">Email</Label>
                    <div className=\"relative\">
                      <Mail className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"signup-email\"
                        type=\"email\"
                        placeholder=\"Enter your email\"
                        className=\"pl-10\"
                        value={signupData.email}
                        onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                        required
                        data-testid=\"signup-email\"
                      />
                    </div>
                  </div>
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"signup-password\">Password</Label>
                    <div className=\"relative\">
                      <Lock className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"signup-password\"
                        type=\"password\"
                        placeholder=\"Create a password\"
                        className=\"pl-10\"
                        value={signupData.password}
                        onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                        required
                        minLength={6}
                        data-testid=\"signup-password\"
                      />
                    </div>
                  </div>
                  <div className=\"space-y-2\">
                    <Label htmlFor=\"signup-confirm-password\">Confirm Password</Label>
                    <div className=\"relative\">
                      <Lock className=\"absolute left-3 top-3 h-4 w-4 text-gray-400\" />
                      <Input
                        id=\"signup-confirm-password\"
                        type=\"password\"
                        placeholder=\"Confirm your password\"
                        className=\"pl-10\"
                        value={signupData.confirmPassword}
                        onChange={(e) => setSignupData({ ...signupData, confirmPassword: e.target.value })}
                        required
                        data-testid=\"signup-confirm-password\"
                      />
                    </div>
                  </div>
                  <Button
                    type=\"submit\"
                    className=\"w-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600\"
                    disabled={isLoading}
                    data-testid=\"signup-submit\"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className=\"mr-2 h-4 w-4 animate-spin\" />
                        Creating account...
                      </>
                    ) : (
                      'Create Account'
                    )}
                  </Button>
                </form>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>

        {/* Demo Credentials */}
        <div className=\"text-center text-sm text-gray-500\">
          <p>New to programming? No worries!</p>
          <p className=\"mt-1\">Start with Level 100 and learn step by step 🚀</p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;"