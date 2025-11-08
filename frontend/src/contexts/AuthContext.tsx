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
    const provider = new GoogleAuthProvider();
    await signInWithPopup(auth as FirebaseAuth, provider);
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

