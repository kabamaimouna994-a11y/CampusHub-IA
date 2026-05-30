import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const loginStyles = `
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg);
    padding: 20px;
  }
  .login-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 40px;
    width: 100%;
    max-width: 420px;
    animation: fadeUp 0.4s ease;
  }
  .login-logo {
    text-align: center;
    margin-bottom: 32px;
  }
  .login-logo-icon {
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin: 0 auto 16px;
  }
  .login-title {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 24px;
    text-align: center;
    margin-bottom: 8px;
  }
  .login-sub {
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 28px;
  }
  .login-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .login-input {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: border-color 0.15s;
  }
  .login-input:focus {
    border-color: var(--accent);
  }
  .login-input::placeholder {
    color: var(--muted);
  }
  .login-error {
    background: rgba(251, 146, 60, 0.12);
    border: 1px solid rgba(251, 146, 60, 0.2);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    color: var(--orange);
    font-size: 12px;
    text-align: center;
  }
  .login-btn {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    margin-top: 8px;
  }
  .login-btn:hover {
    background: #3d6be8;
  }
  .login-footer {
    text-align: center;
    margin-top: 24px;
    font-size: 13px;
    color: var(--muted);
  }
  .login-link {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
  .login-link:hover {
    text-decoration: underline;
  }
`;

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const { login, error: authError } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const displayError = localError || authError;

  return (
    <div className="login-page">
      <style>{loginStyles}</style>
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">🎓</div>
          <div className="login-title">CampusHub IA</div>
          <div className="login-sub">Plateforme intelligente de matching</div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="email"
            className="login-input"
            placeholder="Email étudiant"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <input
            type="password"
            className="login-input"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {displayError && (
            <div className="login-error">{displayError}</div>
          )}
          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="login-footer">
          Pas encore de compte ?{' '}
          <Link to="/register" className="login-link">
            S'inscrire
          </Link>
        </div>
      </div>
    </div>
  );
}