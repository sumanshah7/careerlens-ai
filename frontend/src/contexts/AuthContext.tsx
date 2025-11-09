import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { 
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User
} from 'firebase/auth';
import { auth } from '../lib/firebase';
import type { Auth as FirebaseAuth } from 'firebase/auth';

interface AuthContextType {
  currentUser: User | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const signUp = async (email: string, password: string) => {
    if (!auth) {
      throw new Error('Firebase is not configured. Please add Firebase config to .env file.');
    }
    await createUserWithEmailAndPassword(auth as FirebaseAuth, email, password);
  };

  const signIn = async (email: string, password: string) => {
    if (!auth) {
      throw new Error('Firebase is not configured. Please add Firebase config to .env file.');
    }
    await signInWithEmailAndPassword(auth as FirebaseAuth, email, password);
  };

  const signInWithGoogle = async () => {
    if (!auth) {
      throw new Error('Firebase is not configured. Please add Firebase config to .env file.');
    }
    try {
      const provider = new GoogleAuthProvider();
      // Add additional scopes if needed
      provider.addScope('profile');
      provider.addScope('email');
      
      // Use popup instead of redirect to avoid sessionStorage issues
      const result = await signInWithPopup(auth as FirebaseAuth, provider);
      return result;
    } catch (error: any) {
      // Handle specific Firebase Auth errors
      if (error.code === 'auth/popup-blocked') {
        throw new Error('Popup was blocked by your browser. Please allow popups for this site and try again.');
      } else if (error.code === 'auth/popup-closed-by-user') {
        throw new Error('Sign-in was cancelled. Please try again.');
      } else if (error.code === 'auth/cancelled-popup-request') {
        throw new Error('Another sign-in request is already in progress. Please wait.');
      } else if (error.message?.includes('sessionStorage') || error.message?.includes('initial state')) {
        // Clear any stale auth state and retry
        console.warn('SessionStorage issue detected, clearing auth state...');
        await firebaseSignOut(auth as FirebaseAuth);
        throw new Error('Authentication session expired. Please try signing in again.');
      }
      throw error;
    }
  };

  const signOut = async () => {
    if (!auth) {
      return;
    }
    await firebaseSignOut(auth as FirebaseAuth);
  };

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }
    
    const unsubscribe = onAuthStateChanged(auth as FirebaseAuth, (user) => {
      setCurrentUser(user);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    loading,
    signUp,
    signIn,
    signInWithGoogle,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

