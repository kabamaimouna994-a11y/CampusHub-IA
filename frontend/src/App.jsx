import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import SkillShare from './pages/SkillShare';
import TalentMatch from './pages/TalentMatch';
import MentorLoop from './pages/MentorLoop';
import KPIsCampus from './pages/KPIsCampus';
import EventBoost from './pages/EventBoost';
import { skills, matching, mentorat, clubs, events } from './services/api';
import notificationService from './services/notificationService';

const appStyles = `
  .app { display: flex; min-height: 100vh; }

  .sidebar {
    width: 230px; min-width: 230px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    padding: 22px 0;
    position: sticky; top: 0; height: 100vh;
    overflow-y: auto;
  }
  .logo {
    padding: 0 20px 26px;
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-display);
    font-weight: 800; font-size: 17px; letter-spacing: -.5px;
  }
  .logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
  }
  .nav-section { padding: 0 10px; margin-bottom: 6px; }
  .nav-label {
    font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; color: var(--muted);
    padding: 0 10px; margin-bottom: 4px;
  }
  .nav-item {
    display: flex; align-items: center; gap: 9px;
    padding: 8px 10px; border-radius: var(--radius-sm);
    cursor: pointer; transition: all .15s;
    font-weight: 500; color: var(--muted);
    position: relative; user-select: none;
  }
  .nav-item:hover { background: var(--surface2); color: var(--text); }
  .nav-item.active { background: rgba(79,124,255,.12); color: var(--accent); }
  .nav-item.active::before {
    content: ''; position: absolute;
    left: 0; top: 50%; transform: translateY(-50%);
    width: 3px; height: 16px;
    background: var(--accent); border-radius: 0 4px 4px 0;
  }
  .nav-badge {
    margin-left: auto;
    background: var(--accent); color: #fff;
    font-size: 10px; font-weight: 700;
    padding: 1px 6px; border-radius: 99px; min-width: 18px; text-align: center;
  }
  .nav-badge.green { background: var(--green); color: #0a0d14; }
  .nav-badge.orange { background: var(--orange); }

  .sidebar-bottom {
    margin-top: auto; padding: 14px 20px 0;
    border-top: 1px solid var(--border);
  }
  .user-card { display: flex; align-items: center; gap: 10px; padding: 8px 0; }
  .avatar {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 12px; flex-shrink: 0;
  }
  .user-info { flex: 1; min-width: 0; }
  .user-name { font-weight: 600; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .user-role { font-size: 11px; color: var(--muted); }

  .main { flex: 1; overflow-y: auto; }
  .topbar {
    position: sticky; top: 0; z-index: 10;
    background: rgba(10,13,20,.88); backdrop-filter: blur(18px);
    border-bottom: 1px solid var(--border);
    padding: 0 28px; height: 58px;
    display: flex; align-items: center; gap: 14px;
  }
  .topbar-title { font-family: var(--font-display); font-weight: 700; font-size: 15px; }
  .topbar-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }

  .icon-btn {
    width: 32px; height: 32px; border-radius: var(--radius-sm);
    background: var(--surface); border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; transition: all .15s; color: var(--muted); font-size: 15px;
  }
  .icon-btn:hover { border-color: var(--border2); color: var(--text); }
  .notif-dot { position: relative; }
  .notif-dot::after {
    content: ''; position: absolute; top: 5px; right: 5px;
    width: 6px; height: 6px; background: var(--accent);
    border-radius: 50%; border: 2px solid var(--bg);
  }

  .content { padding: 28px; }

  .search-wrap { position: relative; width: 200px; }
  .search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 13px; pointer-events: none; }
  .search-input {
    width: 100%; background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 6px 10px 6px 30px;
    color: var(--text); font-family: var(--font-body); font-size: 12px;
    outline: none; transition: border-color .15s; height: 32px;
  }
  .search-input:focus { border-color: var(--accent); }
  .search-input::placeholder { color: var(--muted); }

  .toast-container { position: fixed; bottom: 22px; right: 22px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
  .toast {
    background: var(--surface); border: 1px solid var(--border2);
    border-radius: var(--radius-sm); padding: 11px 15px;
    display: flex; align-items: center; gap: 10px;
    min-width: 270px; box-shadow: 0 8px 24px rgba(0,0,0,.4);
    animation: slideIn .3s ease;
  }
  .toast-icon { font-size: 17px; }
  .toast-title { font-weight: 700; font-size: 12px; }
  .toast-text { font-size: 11px; color: var(--muted); margin-top: 1px; }

  @media (max-width: 860px) { .sidebar { display: none; } }
  @media (max-width: 600px) { .content { padding: 14px; } }
`

const PAGE_TITLES = {
  dashboard: 'Vue d\'ensemble',
  skillshare: 'SkillShare — Compétences',
  matching: 'TalentMatch — Projets',
  mentorat: 'MentorLoop — Mentorat',
  clubs: 'KPIs Campus',
  events: 'EventBoost — Événements',
}

function AuthenticatedLayout({ children, page, setPage, addToast, logout, user, navBadges }) {
  const NAV = [
    { id: 'dashboard', label: 'Tableau de bord', icon: '⊞' },
    { id: 'skillshare', label: 'SkillShare', icon: '⚡', badge: navBadges.skills, badgeColor: 'blue' },
    { id: 'matching', label: 'TalentMatch', icon: '🎯', badge: navBadges.projects, badgeColor: '' },
    { id: 'mentorat', label: 'MentorLoop', icon: '🧑‍🏫', badge: navBadges.mentors, badgeColor: 'green' },
    { id: 'clubs', label: 'KPIs Campus', icon: '📊', badge: navBadges.clubs, badgeColor: '' },
    { id: 'events', label: 'EventBoost', icon: '🎉', badge: navBadges.events, badgeColor: 'orange' },
  ]

  // Récupérer le nom complet et le niveau depuis user
  const getUserName = () => {
    if (user?.full_name) return user.full_name
    if (user?.fullName) return user.fullName
    if (user?.first_name && user?.last_name) return `${user.first_name} ${user.last_name}`
    return 'Utilisateur'
  }

  const getUserRole = () => {
    if (user?.role === 'student') return 'Étudiant'
    if (user?.role === 'mentor') return 'Mentor'
    if (user?.role === 'admin') return 'Administrateur'
    return 'Utilisateur'
  }

  const getUserLevel = () => {
    return user?.year_level || user?.yearLevel || 'B1'
  }

  const getAvatarInitial = () => {
    const name = getUserName()
    return name.charAt(0) || 'U'
  }

  return (
    <div className="app">
      <style>{appStyles}</style>
      <nav className="sidebar">
        <div className="logo">
          <div className="logo-icon">🎓</div>
          CampusHub IA
        </div>

        <div className="nav-section">
          <div className="nav-label">Navigation</div>
          {NAV.map(n => (
            <div key={n.id} className={`nav-item ${page === n.id ? 'active' : ''}`} onClick={() => setPage(n.id)}>
              <span>{n.icon}</span>
              <span>{n.label}</span>
              {n.badge !== undefined && n.badge > 0 && (
                <span className={`nav-badge ${n.badgeColor || ''}`}>{n.badge}</span>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="user-card">
            <div className="avatar" style={{ background: 'linear-gradient(135deg,var(--accent),var(--pink))' }}>
              {getAvatarInitial()}
            </div>
            <div className="user-info">
              <div className="user-name">{getUserName()}</div>
              <div className="user-role">{getUserRole()} · {getUserLevel()}</div>
            </div>
          </div>
          <button onClick={logout} className="btn btn-ghost btn-sm" style={{ marginTop: 12, width: '100%' }}>
            Déconnexion
          </button>
        </div>
      </nav>

      <div className="main">
        <header className="topbar">
          <div className="topbar-title">{PAGE_TITLES[page]}</div>
          <div className="topbar-right">
            <div className="search-wrap">
              <span className="search-icon">🔍</span>
              <input className="search-input" placeholder="Rechercher…" />
            </div>
            <div className="icon-btn notif-dot">🔔</div>
            <div className="icon-btn">❓</div>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}

function AppContent() {
  const [page, setPage] = useState('dashboard');
  const [toasts, setToasts] = useState([]);
  const [navBadges, setNavBadges] = useState({
    skills: 0,
    projects: 0,
    mentors: 0,
    clubs: 0,
    events: 0
  });
  const { user, logout } = useAuth();

  const addToast = (icon, title, text) => {
    const id = Date.now();
    setToasts(t => [...t, { id, icon, title, text }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3800);
  };

  // NOTIFICATIONS PUSH
  useEffect(() => {
    if (window.Notification) {
      notificationService.requestPermission()
    }
  }, [])

  // Charger les badges dynamiques
  useEffect(() => {
    const fetchBadges = async () => {
      try {
        const [skillsRes, projectsRes, mentorsRes, clubsRes, eventsRes] = await Promise.all([
          skills.getAll().catch(() => ({ data: [] })),
          matching.getProjects({ top_k: 50 }).catch(() => ({ data: [] })),
          matching.getMentors({ top_k: 50 }).catch(() => ({ data: [] })),
          clubs.getAll().catch(() => ({ data: [] })),
          events.getAll().catch(() => ({ data: [] })),
        ]);
        
        setNavBadges({
          skills: skillsRes.data?.length || 0,
          projects: projectsRes.data?.length || 0,
          mentors: mentorsRes.data?.length || 0,
          clubs: clubsRes.data?.length || 0,
          events: eventsRes.data?.length || 0,
        });
      } catch (error) {
        console.error('Erreur chargement badges:', error);
      }
    };
    
    fetchBadges();
    const interval = setInterval(fetchBadges, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    const props = { setPage, addToast };
    switch (page) {
      case 'dashboard': return <Dashboard {...props} />;
      case 'skillshare': return <SkillShare {...props} />;
      case 'matching': return <TalentMatch {...props} />;
      case 'mentorat': return <MentorLoop {...props} />;
      case 'clubs': return <KPIsCampus {...props} />;
      case 'events': return <EventBoost {...props} />;
      default: return <Dashboard {...props} />;
    }
  };

  return (
    <AuthenticatedLayout page={page} setPage={setPage} addToast={addToast} logout={logout} user={user} navBadges={navBadges}>
      {renderPage()}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className="toast">
            <span className="toast-icon">{t.icon}</span>
            <div>
              <div className="toast-title">{t.title}</div>
              <div className="toast-text">{t.text}</div>
            </div>
          </div>
        ))}
      </div>
    </AuthenticatedLayout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <AppContent />
            </ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}