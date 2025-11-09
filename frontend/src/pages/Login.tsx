import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Logo } from '../components/Logo';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { Spinner } from '../components/ui/spinner';
import { motion } from 'framer-motion';

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const { signIn, signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        await signUp(email, password);
        toast.success('Account created successfully!');
      } else {
        await signIn(email, password);
        toast.success('Signed in successfully!');
      }
      navigate('/dashboard');
    } catch (error: any) {
      toast.error(error.message || 'Authentication failed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      await signInWithGoogle();
      toast.success('Signed in with Google!');
      navigate('/dashboard');
    } catch (error: any) {
      toast.error(error.message || 'Google sign-in failed');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex items-center justify-center px-4 py-20 md:py-32">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md bg-white rounded-[16px] p-8 shadow-[0_1px_3px_rgba(0,0,0,0.08)] border border-[#E5E7EB]"
      >
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <Logo />
          </div>
          <h1 className="text-[42px] md:text-[56px] font-semibold text-[#0F172A] mb-3 leading-tight">
            {isSignUp ? 'Create Account' : 'Welcome Back'}
          </h1>
          <p className="text-lg text-[#64748B] font-normal leading-relaxed">
            {isSignUp ? 'Create your account to get started' : 'Sign in to your account'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="email" className="text-sm font-medium text-[#0F172A] mb-2 block">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              className="border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
            />
          </div>
          <div>
            <Label htmlFor="password" className="text-sm font-medium text-[#0F172A] mb-2 block">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              className="border-[#E5E7EB] rounded-lg focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-[#2563EB] text-white hover:bg-[#1d4ed8] rounded-lg font-medium transition-all duration-200 hover:scale-[1.02]"
            disabled={loading}
            size="lg"
          >
            {loading ? (
              <>
                <Spinner className="mr-2" size="sm" />
                {isSignUp ? 'Creating Account...' : 'Signing In...'}
              </>
            ) : (
              isSignUp ? 'Sign Up' : 'Sign In'
            )}
          </Button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-[#E5E7EB]" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-[#64748B] font-medium">Or continue with</span>
          </div>
        </div>

        <Button
          type="button"
          variant="outline"
          className="w-full border-[#E5E7EB] rounded-lg !bg-white hover:!bg-[#F9FAFB] hover:!border-[#2563EB] hover:!text-[#0F172A] transition-all duration-200"
          onClick={handleGoogleSignIn}
          disabled={loading}
        >
          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          Google
        </Button>

        <div className="mt-6 text-center text-sm">
          <button
            type="button"
            onClick={() => setIsSignUp(!isSignUp)}
            className="text-[#2563EB] hover:text-[#1d4ed8] hover:underline transition-colors font-medium"
          >
            {isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
          </button>
        </div>

        <div className="mt-4 text-center text-xs text-[#64748B] font-normal">
          <Link to="/" className="text-[#2563EB] hover:text-[#1d4ed8] hover:underline transition-colors">
            ← Back to Home
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

