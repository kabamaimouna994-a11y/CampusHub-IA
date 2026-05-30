import { useState, useEffect, useRef } from 'react'
import { Card, Tag, Btn, ProgressBar, SkillDots, Tabs, RingChart, SectionHeader, Input } from '../components/UI.jsx'
import { skills } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { exportSkillsToPDF } from '../utils/pdfExport'

const ss = `
  .profile-grid { display: grid; grid-template-columns: 1fr 1.6fr; gap: 14px; }
  .student-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(260px,1fr)); gap: 13px; }
  .profile-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px;
    transition: all .2s; cursor: pointer;
  }
  .profile-card:hover { border-color: var(--border2); transform: translateY(-2px); }
  .profile-top  { display: flex; align-items: center; gap: 11px; margin-bottom: 12px; }
  .profile-name { font-weight: 600; font-size: 13px; }
  .profile-meta { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .skill-tags   { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }
  .match-row    { display: flex; align-items: center; gap: 9px; font-size: 11px; color: var(--muted); }
  .match-val    { font-family: var(--font-display); font-weight: 700; font-size: 17px; color: var(--green); }
  .completude-box {
    background: var(--surface2); border-radius: 9px;
    padding: 13px; margin-bottom: 13px;
  }
  .avatar-upload-container {
    position: relative;
    display: inline-block;
    cursor: pointer;
  }
  .avatar-upload-overlay {
    position: absolute;
    bottom: 0;
    right: 0;
    background: var(--accent);
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    border: 2px solid var(--surface);
  }
  .skill-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  .skill-name {
    flex: 1;
    font-weight: 500;
    font-size: 13px;
  }
  @media (max-width: 820px) { .profile-grid { grid-template-columns: 1fr; } }
`

const SKILL_CATEGORIES = ['Développement', 'Data & IA', 'Design', 'Business', 'Langues', 'Soft Skills', 'Autre']
const SKILL_LEVELS = ['débutant', 'intermédiaire', 'avancé', 'expert']

// Avatar par défaut en DataURL (pas de dépendance externe)
const DEFAULT_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Crect width='80' height='80' fill='%234f7cff'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='white' font-size='32'%3E👤%3C/text%3E%3C/svg%3E"

// Composant d'upload d'avatar CORRIGÉ
const AvatarUpload = ({ currentAvatar, onUploadSuccess, addToast }) => {
  const [uploading, setUploading] = useState(false)
  const [avatarSrc, setAvatarSrc] = useState(DEFAULT_AVATAR)
  const fileInputRef = useRef(null)

  // Construction de l'URL complète de l'avatar
  const getFullAvatarUrl = (avatar) => {
    if (!avatar) return DEFAULT_AVATAR
    if (avatar.startsWith('http')) return avatar
    if (avatar.startsWith('/')) return `http://localhost:8000${avatar}`
    return `http://localhost:8000/static/${avatar}`
  }

  // Met à jour l'avatar quand currentAvatar change
  useEffect(() => {
    const fullUrl = getFullAvatarUrl(currentAvatar)
    setAvatarSrc(fullUrl)
  }, [currentAvatar])

  const handleUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    if (!file.type.startsWith('image/')) {
      addToast('❌', 'Format invalide', 'Veuillez choisir une image')
      return
    }
    
    if (file.size > 2 * 1024 * 1024) {
      addToast('❌', 'Fichier trop lourd', 'Maximum 2MB')
      return
    }
    
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('http://localhost:8000/api/users/me/avatar', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Erreur upload')
      }
      
      const data = await response.json()
      
      const newAvatarUrl = `http://localhost:8000${data.avatar_url}`
      setAvatarSrc(newAvatarUrl)
      
      if (onUploadSuccess) {
        await onUploadSuccess(data.avatar_url)
      }
      
      addToast('✅', 'Photo mise à jour', 'Votre avatar a été changé')
      
    } catch (error) {
      console.error('Erreur upload:', error)
      addToast('❌', 'Erreur', error.message || "Impossible d'uploader l'image")
    } finally {
      setUploading(false)
    }
  }

  const handleImageError = (e) => {
    if (e.target.src !== DEFAULT_AVATAR) {
      e.target.src = DEFAULT_AVATAR
    }
  }

  return (
    <div style={{ textAlign: 'center', marginBottom: 20 }}>
      <div 
        className="avatar-upload-container"
        onClick={() => fileInputRef.current?.click()}
      >
        <img
          src={avatarSrc}
          alt="Avatar"
          style={{
            width: 80,
            height: 80,
            borderRadius: '50%',
            objectFit: 'cover',
            border: '3px solid var(--accent)'
          }}
          onError={handleImageError}
        />
        <div className="avatar-upload-overlay">
          📷
        </div>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleUpload}
      />
      {uploading && <div style={{ fontSize: 11, marginTop: 5, color: 'var(--muted)' }}>Upload en cours...</div>}
    </div>
  )
}

export default function SkillShare({ addToast }) {
  const { user, refreshUser } = useAuth()
  const [tab, setTab] = useState('profil')
  const [userSkills, setUserSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSkill, setNewSkill] = useState({ name: '', category: 'Développement', level: 'intermédiaire' })
  const [search, setSearch] = useState('')
  const [avatarUrl, setAvatarUrl] = useState(null)

  useEffect(() => {
    // Charger l'avatar depuis localStorage au cas où
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      const userData = JSON.parse(savedUser)
      if (userData.avatar_url) {
        setAvatarUrl(userData.avatar_url)
      }
    }
    
    fetchSkills()
  }, [])

  // Mettre à jour l'avatar quand user change
  useEffect(() => {
    if (user?.avatar_url) {
      setAvatarUrl(user.avatar_url)
    }
  }, [user])

  const fetchSkills = async () => {
    try {
      const res = await skills.getAll()
      setUserSkills(res.data || [])
    } catch (error) {
      console.error('Erreur chargement compétences:', error)
      if (addToast) addToast('❌', 'Erreur', 'Impossible de charger vos compétences')
    } finally {
      setLoading(false)
    }
  }

  const addSkill = async () => {
    if (!newSkill.name.trim()) {
      if (addToast) addToast('⚠️', 'Erreur', 'Le nom de la compétence est requis')
      return
    }
    try {
      await skills.create(newSkill)
      if (addToast) addToast('✅', 'Compétence ajoutée', `${newSkill.name} ajoutée à votre profil`)
      setNewSkill({ name: '', category: 'Développement', level: 'intermédiaire' })
      setShowAddForm(false)
      fetchSkills()
    } catch (error) {
      if (addToast) addToast('❌', 'Erreur', error.response?.data?.detail || "Impossible d'ajouter la compétence")
    }
  }

  const deleteSkill = async (skillId, skillName) => {
    try {
      await skills.delete(skillId)
      if (addToast) addToast('🗑️', 'Compétence supprimée', `${skillName} a été retirée`)
      fetchSkills()
    } catch (error) {
      if (addToast) addToast('❌', 'Erreur', "Impossible de supprimer la compétence")
    }
  }

  const updateSkillLevel = async (skillId, newLevel) => {
    try {
      await skills.update(skillId, { level: newLevel })
      fetchSkills()
    } catch (error) {
      if (addToast) addToast('❌', 'Erreur', "Impossible de modifier le niveau")
    }
  }

  const handleExportPDF = () => {
    if (userSkills.length === 0) {
      if (addToast) addToast('⚠️', 'Aucune compétence', 'Ajoutez des compétences avant d\'exporter')
      return
    }
    exportSkillsToPDF(user, userSkills)
    if (addToast) addToast('📄', 'Export PDF', 'Votre portfolio a été généré')
  }

  const skillsByCategory = (category) => {
    return userSkills.filter(s => s.category === category)
  }

  const categories = SKILL_CATEGORIES.filter(cat => skillsByCategory(cat).length > 0)

  // Calcul du nom complet
  const getFullName = () => {
    if (user?.full_name) return user.full_name
    if (user?.first_name && user?.last_name) return `${user.first_name} ${user.last_name}`
    return 'Utilisateur'
  }

  // Calcul du niveau
  const getYearLevel = () => {
    return user?.year_level || user?.yearLevel || 'B1'
  }

  // Calcul de la spécialité
  const getSpecialty = () => {
    return user?.specialty || 'Spécialité non renseignée'
  }

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', padding: 40 }}>Chargement de votre profil...</div>
  }

  return (
    <div className="fade-up">
      <style>{ss}</style>

      <SectionHeader
        title="⚡ SkillShare"
        sub="Gérez et valorisez vos compétences"
        action={<Btn onClick={() => setShowAddForm(!showAddForm)}>{showAddForm ? 'Annuler' : '+ Ajouter une compétence'}</Btn>}
      />

      {showAddForm && (
        <Card style={{ marginBottom: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 10, alignItems: 'center' }}>
            <input className="input" placeholder="Nom de la compétence (ex: Python)" value={newSkill.name} onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })} />
            <select className="input" value={newSkill.category} onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}>
              {SKILL_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select className="input" value={newSkill.level} onChange={(e) => setNewSkill({ ...newSkill, level: e.target.value })}>
              {SKILL_LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
            <Btn onClick={addSkill}>Ajouter</Btn>
          </div>
        </Card>
      )}

      <div style={{ marginBottom: 18 }}>
        <Tabs items={['profil', 'explorer', 'certifications']} active={tab} onChange={setTab} />
      </div>

      {tab === 'profil' && (
        <div className="profile-grid">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Card>
              <AvatarUpload 
                currentAvatar={avatarUrl || user?.avatar_url} 
                onUploadSuccess={async (newAvatar) => {
                  setAvatarUrl(newAvatar)
                  if (refreshUser) {
                    await refreshUser()
                  }
                }}
                addToast={addToast}
              />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{getFullName()}</div>
                <div style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 6 }}>{getYearLevel()} · {getSpecialty()}</div>
                <div style={{ display: 'flex', gap: 5, justifyContent: 'center' }}>
                  <Tag color="blue">Disponible</Tag>
                  <Tag>{userSkills.length} compétences</Tag>
                </div>
              </div>
              <div className="completude-box" style={{ marginTop: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 8 }}>
                  <span style={{ color: 'var(--muted)', fontWeight: 600 }}>Complétude du profil</span>
                  <span style={{ fontWeight: 700 }}>{Math.min(100, 50 + userSkills.length * 5)}%</span>
                </div>
                <ProgressBar value={Math.min(100, 50 + userSkills.length * 5)} color="var(--accent)" />
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 7 }}>
                  Ajoutez {Math.max(0, 10 - userSkills.length)} compétences pour compléter votre profil
                </div>
              </div>
            </Card>

            <Card title="📊 Statistiques">
              <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                <RingChart value={Math.min(100, 50 + userSkills.length * 5)} color="var(--accent)" size={80} />
                <div>
                  <div style={{ fontWeight: 700, marginBottom: 3 }}>Profil à {Math.min(100, 50 + userSkills.length * 5)}%</div>
                  <div style={{ fontSize: 12 }}>🎯 {userSkills.length} compétences</div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>✅ {userSkills.filter(s => s.is_validated).length} validées</div>
                </div>
              </div>
            </Card>
          </div>

          <Card title="🛠️ Mes compétences">
            {categories.length > 0 ? categories.map(cat => (
              <div key={cat} style={{ marginBottom: 18 }}>
                <div style={{
                  fontSize: 10, fontWeight: 700, color: 'var(--muted)',
                  letterSpacing: '0.8px', textTransform: 'uppercase', marginBottom: 9
                }}>{cat}</div>
                {skillsByCategory(cat).map(s => (
                  <div key={s.id} className="skill-row">
                    <span className="skill-name">{s.name}</span>
                    <SkillDots level={s.level} />
                    <select
                      className="input"
                      style={{ width: 120, marginLeft: 'auto', fontSize: 10, padding: '4px 8px' }}
                      value={s.level}
                      onChange={(e) => updateSkillLevel(s.id, e.target.value)}
                    >
                      {SKILL_LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                    </select>
                    <button className="btn btn-ghost btn-sm" style={{ color: 'var(--orange)' }} onClick={() => deleteSkill(s.id, s.name)}>🗑️</button>
                  </div>
                ))}
              </div>
            )) : (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)' }}>
                Aucune compétence. Cliquez sur "+ Ajouter une compétence" pour commencer.
              </div>
            )}
            <Btn variant="secondary" style={{ width: '100%' }} onClick={handleExportPDF}>
              📥 Exporter PDF
            </Btn>
          </Card>
        </div>
      )}

      {tab === 'explorer' && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Input icon="🔍" placeholder="Rechercher un étudiant..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="student-grid">
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)', gridColumn: '1/-1' }}>
              🔍 La recherche d'étudiants sera disponible prochainement
            </div>
          </div>
        </div>
      )}

      {tab === 'certifications' && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--muted)' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🏅</div>
            <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text)' }}>Import de certifications</div>
            <div style={{ fontSize: 13, marginBottom: 18 }}>Importez vos certifications LinkedIn, Google, AWS... (bientôt disponible)</div>
          </div>
        </Card>
      )}
    </div>
  )
}