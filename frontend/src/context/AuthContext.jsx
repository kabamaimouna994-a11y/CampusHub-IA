import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api, { auth as authService } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await authService.getMe();
      const userData = response.data;
      setUser(userData);
      // ⭐ AJOUT : Sauvegarder l'utilisateur dans localStorage pour accès rapide
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (err) {
      console.error('Erreur chargement utilisateur:', err);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user'); // ⭐ Nettoyer aussi l'user
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    const handleLogout = () => {
      setUser(null);
      setLoading(false);
    };
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  const login = async (email, password) => {
    setError(null);
    try {
      const response = await authService.login({ email, password });
      const { access_token, refresh_token, user_id, role, year_level, full_name } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // ⭐ Récupérer l'utilisateur complet depuis l'API
      const userResponse = await authService.getMe();
      const fullUserData = userResponse.data;
      
      // ⭐ Sauvegarder l'utilisateur complet dans localStorage
      localStorage.setItem('user', JSON.stringify(fullUserData));
      
      setUser(fullUserData);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Erreur de connexion';
      setError(message);
      throw new Error(message);
    }
  };

  const register = async (data) => {
    setError(null);
    try {
      const response = await authService.register(data);
      const { access_token, refresh_token, user_id, role, year_level, full_name } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // ⭐ Récupérer l'utilisateur complet depuis l'API
      const userResponse = await authService.getMe();
      const fullUserData = userResponse.data;
      
      // ⭐ Sauvegarder l'utilisateur complet dans localStorage
      localStorage.setItem('user', JSON.stringify(fullUserData));
      
      setUser(fullUserData);
      return response.data;
    } catch (err) {
      const message = err.response?.data?.detail || 'Erreur d\'inscription';
      setError(message);
      throw new Error(message);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.warn('Erreur déconnexion (ignorée):', err?.message);
    } finally {
      // ⭐ Nettoyer TOUT localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user'); // ⭐ CRUCIAL
      setUser(null);
    }
  };

  const updateUser = (updates) => {
    setUser((prev) => {
      if (!prev) return null;
      const updated = { ...prev, ...updates };
      // ⭐ Mettre à jour localStorage
      localStorage.setItem('user', JSON.stringify(updated));
      return updated;
    });
  };

  const refreshUser = async () => {
    try {
      const response = await authService.getMe();
      const userData = response.data;
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      return userData;
    } catch (err) {
      console.error('Erreur refresh:', err);
      return null;
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updateUser,
    refreshUser, // ⭐ Ajout de refreshUser
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isMentor: user?.role === 'mentor',
    isStudent: user?.role === 'student',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}