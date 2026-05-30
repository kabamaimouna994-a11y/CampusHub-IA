import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const registerStyles = `
  .register-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg);
    padding: 20px;
  }
  .register-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 32px;
    width: 100%;
    max-width: 480px;
    animation: fadeUp 0.4s ease;
  }
  .register-logo {
    text-align: center;
    margin-bottom: 28px;
  }
  .register-logo-icon {
    width: 52px;
    height: 52px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    margin: 0 auto 14px;
  }
  .register-title {
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 22px;
    text-align: center;
    margin-bottom: 6px;
  }
  .register-sub {
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 24px;
  }
  .register-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .register-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .register-input {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 11px 14px;
    color: var(--text);
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s;
  }
  .register-input:focus {
    border-color: var(--accent);
  }
  .register-select {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 11px 14px;
    color: var(--text);
    font-size: 13px;
    cursor: pointer;
  }
  .register-error {
    background: rgba(251, 146, 60, 0.12);
    border: 1px solid rgba(251, 146, 60, 0.2);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    color: var(--orange);
    font-size: 12px;
    text-align: center;
  }
  .register-btn {
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
  .register-btn:hover {
    background: #3d6be8;
  }
  .register-footer {
    text-align: center;
    margin-top: 22px;
    font-size: 13px;
    color: var(--muted);
  }
  .register-link {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }
`;

const YEAR_LEVELS = [
  { value: 'B1', label: 'Bachelor 1' },
  { value: 'B2', label: 'Bachelor 2' },
  { value: 'B3', label: 'Bachelor 3' },
  { value: 'M1', label: 'Master 1' },
  { value: 'M2', label: 'Master 2' },
];

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    year_level: 'B1',
    specialty: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const { register, error: authError } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (formData.password !== formData.confirmPassword) {
      setLocalError('Les mots de passe ne correspondent pas');
      return;
    }
    if (formData.password.length < 8) {
      setLocalError('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    setIsLoading(true);
    try {
      const { confirmPassword, ...registerData } = formData;
      await register(registerData);
      navigate('/');
    } catch (err) {
      setLocalError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const displayError = localError || authError;

  return (
    <div className="register-page">
      <style>{registerStyles}</style>
      <div className="register-card">
        <div className="register-logo">
          <div className="register-logo-icon">🎓</div>
          <div className="register-title">CampusHub IA</div>
          <div className="register-sub">Créez votre compte étudiant</div>
        </div>

        <form className="register-form" onSubmit={handleSubmit}>
          <div className="register-row">
            <input
              type="text"
              name="first_name"
              className="register-input"
              placeholder="Prénom"
              value={formData.first_name}
              onChange={handleChange}
              required
            />
            <input
              type="text"
              name="last_name"
              className="register-input"
              placeholder="Nom"
              value={formData.last_name}
              onChange={handleChange}
              required
            />
          </div>

          <input
            type="email"
            name="email"
            className="register-input"
            placeholder="Email étudiant"
            value={formData.email}
            onChange={handleChange}
            required
          />

          <div className="register-row">
            <select
              name="year_level"
              className="register-select"
              value={formData.year_level}
              onChange={handleChange}
            >
              {YEAR_LEVELS.map(level => (
                <option key={level.value} value={level.value}>{level.label}</option>
              ))}
            </select>
            <input
              type="text"
              name="specialty"
              className="register-input"
              placeholder="Spécialité (ex: Développement)"
              value={formData.specialty}
              onChange={handleChange}
            />
          </div>

          <input
            type="password"
            name="password"
            className="register-input"
            placeholder="Mot de passe (min. 8 caractères)"
            value={formData.password}
            onChange={handleChange}
            required
          />
          <input
            type="password"
            name="confirmPassword"
            className="register-input"
            placeholder="Confirmer le mot de passe"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
          />

          {displayError && <div className="register-error">{displayError}</div>}

          <button type="submit" className="register-btn" disabled={isLoading}>
            {isLoading ? 'Inscription...' : "S'inscrire"}
          </button>
        </form>

        <div className="register-footer">
          Déjà un compte ?{' '}
          <Link to="/login" className="register-link">
            Se connecter
          </Link>
        </div>
      </div>
    </div>
  );
}