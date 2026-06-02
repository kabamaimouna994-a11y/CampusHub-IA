import { useState, useEffect } from 'react'
import { Tag, Btn, ProgressBar, SectionHeader, Card } from '../components/UI.jsx'
import { events } from '../services/api'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

const eb = `
  .events-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
  .ev-card {
    background:var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); overflow:hidden;
    transition:all .2s; cursor:pointer;
  }
  .ev-card:hover { border-color:var(--border2); transform:translateY(-2px); }
  .ev-banner {
    height:78px; display:flex; align-items:center; justify-content:center;
    font-size:36px; position:relative; overflow:hidden;
  }
  .ev-body   { padding:15px; }
  .ev-title  { font-weight:700; font-size:13px; margin-bottom:5px; }
  .ev-meta   { display:flex; gap:10px; font-size:10px; color:var(--muted); margin-bottom:9px; }
  .ev-foot   { display:flex; align-items:center; justify-content:space-between; }
  .top-match-badge {
    position:absolute; top:8px; left:8px;
    background:var(--green); color:#0a0d14;
    font-size:9px; font-weight:700; padding:2px 7px; border-radius:99px;
  }
  .type-badge {
    position:absolute; top:8px; right:8px;
    background:rgba(0,0,0,.45); border:none; color:#fff;
    font-size:9px; font-weight:600; padding:2px 7px; border-radius:99px;
  }
  .filter-row { display:flex; gap:7px; margin-bottom:18px; flex-wrap:wrap; }
  .form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; }
  .form-group label { font-size: 12px; font-weight: 600; color: var(--muted); }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media (max-width:900px) { .events-grid { grid-template-columns:repeat(2,1fr); } }
  @media (max-width:560px) { .events-grid { grid-template-columns:1fr; } .form-row { grid-template-columns:1fr; } }
`

const BANNER_BG = {
  '#4f7cff': 'linear-gradient(135deg,#1e3a8a,#4f7cff)',
  '#f472b6': 'linear-gradient(135deg,#831843,#f472b6)',
  '#fbbf24': 'linear-gradient(135deg,#78350f,#fbbf24)',
  '#34d399': 'linear-gradient(135deg,#065f46,#34d399)',
  '#a78bfa': 'linear-gradient(135deg,#4c1d95,#a78bfa)',
  '#fb923c': 'linear-gradient(135deg,#7c2d12,#fb923c)',
}

export default function EventBoost({ addToast }) {
  const { user } = useAuth()
  const [filter, setFilter] = useState('tous')
  const [eventsList, setEventsList] = useState([])
  const [registeredEvents, setRegisteredEvents] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    emoji: '🎉',
    event_date: '',
    event_type: 'Conférence',
    capacity: 50,
    location: ''
  })

  useEffect(() => {
    fetchEvents()
  }, [filter])

  const fetchEvents = async () => {
    setLoading(true)
    try {
      const res = await events.getAll()
      let data = res.data || []
      if (filter !== 'tous') {
        data = data.filter(e => e.event_type === filter)
      }
      setEventsList(data)
      const userRegistrations = data.filter(e => e.is_registered).map(e => e.id)
      setRegisteredEvents(new Set(userRegistrations))
    } catch (error) {
      console.error('Erreur chargement événements:', error)
      addToast('❌', 'Erreur', 'Impossible de charger les événements')
    } finally {
      setLoading(false)
    }
  }

  const registerEvent = async (eventId, eventTitle) => {
    if (registeredEvents.has(eventId)) {
      addToast('⚠️', 'Déjà inscrit', `Vous êtes déjà inscrit à ${eventTitle}`)
      return
    }
    try {
      await events.register(eventId)
      setRegisteredEvents(prev => new Set([...prev, eventId]))
      addToast('✅', 'Inscription confirmée !', `Vous êtes inscrit à ${eventTitle}`)
      fetchEvents()
    } catch (error) {
      addToast('❌', 'Erreur', error.response?.data?.detail || "Impossible de s'inscrire")
    }
  }

  const createEvent = async () => {
    if (!newEvent.title.trim()) {
      addToast('⚠️', 'Erreur', 'Le titre de l\'événement est requis')
      return
    }
    if (!newEvent.event_date) {
      addToast('⚠️', 'Erreur', 'La date de l\'événement est requise')
      return
    }
    try {
      await events.create({
        ...newEvent,
        event_date: new Date(newEvent.event_date).toISOString()
      })
      addToast('✅', 'Événement créé !', `${newEvent.title} a été programmé`)
      setShowCreateForm(false)
      setNewEvent({
        title: '',
        description: '',
        emoji: '🎉',
        event_date: '',
        event_type: 'Conférence',
        capacity: 50,
        location: ''
      })
      fetchEvents()
    } catch (error) {
      console.error('Erreur création:', error)
      addToast('❌', 'Erreur', error.response?.data?.detail || "Impossible de créer l'événement")
    }
  }

  const deleteEvent = async (eventId, eventTitle) => {
    if (window.confirm(`Supprimer l'événement "${eventTitle}" ?\n\nCette action est irréversible.`)) {
      try {
        await api.delete(`/api/events/${eventId}`)
        addToast('🗑️', 'Événement supprimé', `L'événement "${eventTitle}" a été supprimé`)
        fetchEvents()
      } catch (error) {
        console.error('Erreur suppression:', error)
        addToast('❌', 'Erreur', error.response?.data?.detail || "Impossible de supprimer l'événement")
      }
    }
  }

  const types = ['tous', 'Conférence', 'Workshop', 'Compétition', 'Networking', 'Pitch']

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', padding: 40 }}>Chargement des événements...</div>
  }

  return (
    <div className="fade-up">
      <style>{eb}</style>

      <SectionHeader
        title="🎉 EventBoost"
        sub="Événements recommandés pour vous"
        action={<Btn onClick={() => setShowCreateForm(!showCreateForm)}>{showCreateForm ? 'Annuler' : '+ Créer un événement'}</Btn>}
      />

      {showCreateForm && (
        <Card style={{ marginBottom: 20 }}>
          <div style={{ marginBottom: 15, fontWeight: 700, fontSize: 14 }}>📅 Nouvel événement</div>
          <div className="form-group">
            <label>Titre de l'événement *</label>
            <input className="input" placeholder="Ex: Hackathon IA 48h" value={newEvent.title} onChange={e => setNewEvent({...newEvent, title: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea className="input" placeholder="Décrivez votre événement..." rows={2} value={newEvent.description} onChange={e => setNewEvent({...newEvent, description: e.target.value})} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Date et heure *</label>
              <input className="input" type="datetime-local" value={newEvent.event_date} onChange={e => setNewEvent({...newEvent, event_date: e.target.value})} />
            </div>
            <div className="form-group">
              <label>Lieu</label>
              <input className="input" placeholder="Amphi A, Salle 204..." value={newEvent.location} onChange={e => setNewEvent({...newEvent, location: e.target.value})} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Type d'événement</label>
              <select className="input" value={newEvent.event_type} onChange={e => setNewEvent({...newEvent, event_type: e.target.value})}>
                <option>Conférence</option><option>Workshop</option><option>Compétition</option><option>Networking</option><option>Pitch</option><option>Autre</option>
              </select>
            </div>
            <div className="form-group">
              <label>Capacité maximale</label>
              <input className="input" type="number" min="1" max="500" value={newEvent.capacity} onChange={e => setNewEvent({...newEvent, capacity: e.target.value})} />
            </div>
          </div>
          <div className="form-group">
            <label>Icône (emoji)</label>
            <input className="input" placeholder="🎉" value={newEvent.emoji} onChange={e => setNewEvent({...newEvent, emoji: e.target.value})} />
          </div>
          <Btn onClick={createEvent}>🎉 Publier l'événement</Btn>
        </Card>
      )}

      <div className="filter-row">
        {types.map(t => (
          <Btn key={t} variant={filter === t ? 'primary' : 'secondary'} size="sm" onClick={() => setFilter(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </Btn>
        ))}
      </div>

      <div className="events-grid">
        {eventsList.map(e => {
          const fillPct = Math.round(((e.registered_count || 0) / (e.capacity || 1)) * 100)
          const isReg = registeredEvents.has(e.id)
          const isTopMatch = (e.fill_rate || 0) > 70
          const isOrganizer = e.organizer_id === user?.id
          const color = '#4f7cff'

          return (
            <div key={e.id} className="ev-card">
              <div className="ev-banner" style={{ background: BANNER_BG[color] || 'var(--surface2)' }}>
                <span>{e.emoji || '🎉'}</span>
                {isTopMatch && <span className="top-match-badge">✨ POPULAIRE</span>}
                <span className="type-badge">{e.event_type}</span>
              </div>

              <div className="ev-body">
                <div className="ev-title">{e.title}</div>
                <div className="ev-meta">
                  <span>📅 {new Date(e.event_date).toLocaleDateString('fr-FR')}</span>
                  <span>📍 {e.location || 'À définir'}</span>
                </div>

                <div style={{ marginBottom: 9 }}>
                  <ProgressBar value={fillPct} color={color} />
                </div>

                <div className="ev-foot">
                  <span style={{ fontSize: 10, color: 'var(--muted)' }}>
                    {e.registered_count || 0}/{e.capacity || 0} inscrits
                  </span>
                  <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                    <Tag color="green">🎯 {e.fill_rate || 0}%</Tag>
                    {isOrganizer && (
                      <Btn size="sm" variant="secondary" onClick={() => deleteEvent(e.id, e.title)}>
                        🗑️
                      </Btn>
                    )}
                    <Btn size="sm" variant={isReg ? 'secondary' : 'primary'} onClick={() => registerEvent(e.id, e.title)}>
                      {isReg ? '✓ Inscrit' : "S'inscrire"}
                    </Btn>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {eventsList.length === 0 && !showCreateForm && (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          Aucun événement trouvé. Créez le premier événement !
        </div>
      )}
    </div>
  )
}