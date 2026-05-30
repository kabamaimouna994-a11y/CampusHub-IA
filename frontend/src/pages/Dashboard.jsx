import { useState, useEffect } from 'react'
import { Card, StatCard, Tag, Btn, ProgressBar, SkillDots } from '../components/UI.jsx'
import { matching, skills, events, users } from '../services/api'
import { useAuth } from '../context/AuthContext'

const pageStyles = `
  .db-grid-top   { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 22px; }
  .db-grid-mid   { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 22px; }
  .db-grid-bot   { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
  .bar-chart     { display: flex; align-items: flex-end; gap: 7px; height: 74px; }
  .bar-col       { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; }
  .bar           { width: 100%; border-radius: 4px 4px 0 0; min-height: 4px; }
  .bar-label     { font-size: 9px; color: var(--muted); font-weight: 500; }
  .next-event-box {
    background: rgba(79,124,255,.07);
    border-radius: 9px; padding: 13px;
    margin-bottom: 11px;
    border: 1px solid rgba(79,124,255,.13);
  }
  @media (max-width: 900px) {
    .db-grid-top { grid-template-columns: repeat(2,1fr); }
    .db-grid-mid { grid-template-columns: 1fr; }
    .db-grid-bot { grid-template-columns: 1fr; }
  }
`

const BARS = [
  { label: 'Lun', v: 62 }, { label: 'Mar', v: 78 }, { label: 'Mer', v: 55 },
  { label: 'Jeu', v: 88 }, { label: 'Ven', v: 72 }, { label: 'Sam', v: 34 }, { label: 'Dim', v: 28 },
]

export default function Dashboard({ setPage, addToast }) {
  const { user } = useAuth()
  const [projects, setProjects] = useState([])
  const [userSkills, setUserSkills] = useState([])
  const [nextEvent, setNextEvent] = useState(null)
  const [mentor, setMentor] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projectsRes, skillsRes, eventsRes, mentorsRes] = await Promise.all([
          matching.getProjects({ top_k: 3 }),
          skills.getAll(),
          events.getAll(),
          matching.getMentors({ top_k: 1 }),
        ])
        setProjects(projectsRes.data || [])
        setUserSkills(skillsRes.data || [])
        setNextEvent(eventsRes.data?.[0] || null)
        setMentor(mentorsRes.data?.[0] || null)
      } catch (error) {
        console.error('Erreur chargement dashboard:', error)
        addToast('❌', 'Erreur', 'Impossible de charger les données')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [addToast])

  const stats = {
    skillsCount: userSkills.length,
    avgMatch: projects.length ? Math.round(projects.reduce((a, b) => a + (b.score_percent || 0), 0) / projects.length) : 0,
    mentorCount: mentor ? 1 : 0,
    eventsCount: nextEvent ? 1 : 0,
  }

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', padding: 40 }}>Chargement du tableau de bord...</div>
  }

  return (
    <div className="fade-up">
      <style>{pageStyles}</style>

      <div className="welcome-banner">
        <div className="welcome-title">Bonjour, {user?.fullName || 'Étudiant'} 👋</div>
        <div className="welcome-sub">
          Voici votre activité campus. {projects.length} recommandations IA disponibles.
        </div>
        <div className="welcome-actions">
          <Btn onClick={() => setPage('matching')}>🎯 Voir mes matchings</Btn>
          <Btn variant="secondary" onClick={() => setPage('mentorat')}>💬 Contacter un mentor</Btn>
        </div>
      </div>

      <div className="db-grid-top">
        <StatCard icon="⚡" value={stats.skillsCount} label="Compétences" delta={`+${Math.min(3, stats.skillsCount)} ce mois`} color="blue" />
        <StatCard icon="🎯" value={`${stats.avgMatch}%`} label="Score matching" delta="+7% vs avant" color="green" />
        <StatCard icon="🧑‍🏫" value={stats.mentorCount} label="Mentors disponibles" delta={stats.mentorCount ? "1 recommandé" : "Aucun"} color="purple" />
        <StatCard icon="📅" value={stats.eventsCount} label="Événements" delta={nextEvent ? "1 à venir" : "Aucun"} color="orange" />
      </div>

      <div className="db-grid-mid">
        <Card title="📈 Activité hebdomadaire">
          <div className="bar-chart">
            {BARS.map((b, i) => (
              <div key={b.label} className="bar-col">
                <div className="bar" style={{
                  height: `${b.v}%`,
                  background: i === 3 ? 'var(--accent)' : 'var(--surface2)',
                  border: '1px solid var(--border)',
                }} />
                <span className="bar-label">{b.label}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="🎯 Projets recommandés">
          {projects.slice(0, 3).map(p => (
            <div key={p.project_id} className="list-item">
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--accent)', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{p.project_title}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                  {p.required_skills?.slice(0, 3).map(s => s.name).join(' · ') || 'Aucune compétence requise'}
                </div>
              </div>
              <Tag color="green">🎯 {p.score_percent || 0}%</Tag>
            </div>
          ))}
          {projects.length === 0 && (
            <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>
              Aucun projet recommandé pour le moment
            </div>
          )}
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 8, width: '100%' }} onClick={() => setPage('matching')}>
            Voir tous →
          </button>
        </Card>
      </div>

      <div className="db-grid-bot">
        <Card title="🧑‍🏫 Votre mentor">
          {mentor ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 13 }}>
                <div style={{
                  width: 42, height: 42, borderRadius: '50%', flexShrink: 0,
                  background: 'rgba(167,139,250,.2)', color: 'var(--accent2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: 14,
                }}>{mentor.mentor_name?.charAt(0) || 'M'}</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{mentor.mentor_name}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>{mentor.year_level} — {mentor.specialty || 'Spécialité non renseignée'}</div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, marginBottom: 13, flexWrap: 'wrap' }}>
                <Tag color="blue">Score: {mentor.score_percent}% match</Tag>
                <Tag color={mentor.is_available ? 'green' : 'orange'}>{mentor.is_available ? 'Disponible' : 'Indisponible'}</Tag>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>
              Aucun mentor recommandé pour le moment
            </div>
          )}
          <Btn style={{ width: '100%' }} onClick={() => setPage('mentorat')}>💬 Trouver un mentor</Btn>
        </Card>

        <Card title="📅 Prochain événement">
          {nextEvent ? (
            <>
              <div className="next-event-box">
                <div style={{ fontSize: 28, marginBottom: 5 }}>{nextEvent.emoji || '🎉'}</div>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>{nextEvent.title}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                  {new Date(nextEvent.event_date).toLocaleDateString('fr-FR')} · {nextEvent.event_type}
                </div>
              </div>
              <div style={{ marginBottom: 10 }}>
                <ProgressBar value={nextEvent.fill_rate || 0} color="var(--accent)" />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--muted)' }}>
                <span>{nextEvent.registered_count || 0} / {nextEvent.capacity || 0} inscrits</span>
                {nextEvent.available_spots > 0 ? (
                  <Tag color="green">{nextEvent.available_spots} places disponibles</Tag>
                ) : (
                  <Tag color="orange">Complet</Tag>
                )}
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>
              Aucun événement à venir
            </div>
          )}
        </Card>

        <Card title="⚡ Mes compétences">
          {userSkills.slice(0, 4).map(s => (
            <div key={s.id} className="skill-row">
              <span className="skill-name">{s.name}</span>
              <SkillDots level={s.level} />
              <Tag style={{ marginLeft: 'auto', fontSize: 10 }}>{s.level}</Tag>
            </div>
          ))}
          {userSkills.length === 0 && (
            <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>
              Aucune compétence ajoutée
            </div>
          )}
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 4, width: '100%' }} onClick={() => setPage('skillshare')}>
            {userSkills.length > 0 ? 'Éditer profil →' : '+ Ajouter des compétences →'}
          </button>
        </Card>
      </div>
    </div>
  )
}