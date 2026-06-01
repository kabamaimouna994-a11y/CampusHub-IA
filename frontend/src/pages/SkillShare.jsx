import { useState, useEffect, useRef } from 'react'
import { Card, Tag, Btn, ProgressBar, SkillDots, Tabs, RingChart, SectionHeader, Input } from '../components/UI.jsx'
import { skills, certifications } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { exportSkillsToPDF } from '../utils/pdfExport'

const ss = `
  .profile-grid { display: grid; grid-template-columns: 1fr 1.6fr; gap: 14px; }
  .student-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); gap: 16px; margin-top: 16px; }
  .student-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 18px;
    transition: all .2s;
  }
  .student-card:hover { border-color: var(--border2); transform: translateY(-2px); }
  .student-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .student-name { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
  .student-meta { font-size: 11px; color: var(--muted); }
  .student-skills { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
  .student-bio { font-size: 11px; color: var(--muted); margin: 8px 0; line-height: 1.4; }
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
  .filter-row {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    align-items: center;
  }
  .search-row {
    display: flex;
    gap: 10px;
    margin-bottom: 16px;
  }
  .loading-spinner {
    text-align: center;
    padding: 40px;
    color: var(--muted);
  }
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .cert-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-bottom: 1px solid var(--border);
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  @media (max-width: 820px) { 
    .profile-grid { grid-template-columns: 1fr; }
    .student-grid { grid-template-columns: 1fr; }
    .form-row { grid-template-columns: 1fr; }
  }
`

const SKILL_CATEGORIES = ['Développement', 'Data & IA', 'Design', 'Business', 'Langues', 'Soft Skills', 'Autre']
const SKILL_LEVELS = ['débutant', 'intermédiaire', 'avancé', 'expert']
const YEAR_LEVELS = ['Tous', 'B1', 'B2', 'B3', 'M1', 'M2']

// Avatar par défaut
const DEFAULT_AVATAR = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Crect width='80' height='80' fill='%234f7cff'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='white' font-size='32'%3E👤%3C/text%3E%3C/svg%3E"

// Composant d'upload d'avatar
const AvatarUpload = ({ currentAvatar, onUploadSuccess, addToast }) => {
  const [uploading, setUploading] = useState(false)
  const [avatarSrc, setAvatarSrc] = useState(DEFAULT_AVATAR)
  const fileInputRef = useRef(null)

  const getFullAvatarUrl = (avatar) => {
    if (!avatar) return DEFAULT_AVATAR
    if (avatar.startsWith('http')) return avatar
    if (avatar.startsWith('/')) return `http://localhost:8000${avatar}`
    return `http://localhost:8000/static/${avatar}`
  }

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
      <div className="avatar-upload-container" onClick={() => fileInputRef.current?.click()}>
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
        <div className="avatar-upload-overlay">📷</div>
      </div>
      <input ref={fileInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleUpload} />
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
  
  // États pour la recherche d'étudiants
  const [students, setStudents] = useState([])
  const [searchingStudents, setSearchingStudents] = useState(false)
  const [yearFilter, setYearFilter] = useState('Tous')
  const [skillFilter, setSkillFilter] = useState('')
  const [searchTimeout, setSearchTimeout] = useState(null)
  
  // États pour les certifications
  const [certifications, setCertifications] = useState([])
  const [showCertForm, setShowCertForm] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [newCert, setNewCert] = useState({
    title: '',
    issuer: '',
    issue_date: '',
    credential_id: '',
    credential_url: ''
  })
  const [selectedFile, setSelectedFile] = useState(null)

  useEffect(() => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      const userData = JSON.parse(savedUser)
      if (userData.avatar_url) {
        setAvatarUrl(userData.avatar_url)
      }
    }
    fetchSkills()
    fetchCertifications()
  }, [])

  useEffect(() => {
    if (user?.avatar_url) {
      setAvatarUrl(user.avatar_url)
    }
  }, [user])

  // Recherche d'étudiants avec debounce
  useEffect(() => {
    if (tab === 'explorer') {
      if (searchTimeout) clearTimeout(searchTimeout)
      const timeout = setTimeout(() => {
        searchStudents()
      }, 500)
      setSearchTimeout(timeout)
      return () => clearTimeout(timeout)
    }
  }, [search, yearFilter, skillFilter, tab])

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

  const fetchCertifications = async () => {
    try {
      const res = await certifications.getAll()
      setCertifications(res.data || [])
    } catch (error) {
      console.error('Erreur chargement certifications:', error)
    }
  }

  const searchStudents = async () => {
    setSearchingStudents(true)
    try {
      const token = localStorage.getItem('access_token')
      let url = 'http://localhost:8000/api/users/search?'
      if (search) url += `q=${encodeURIComponent(search)}&`
      if (yearFilter !== 'Tous') url += `year_level=${yearFilter}&`
      if (skillFilter) url += `skill=${encodeURIComponent(skillFilter)}&`
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      setStudents(data)
    } catch (error) {
      console.error('Erreur recherche:', error)
      if (addToast) addToast('❌', 'Erreur', 'Impossible de rechercher des étudiants')
    } finally {
      setSearchingStudents(false)
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

  // Gestion des certifications
  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    setSelectedFile(file)
  }

  const addCertification = async () => {
    if (!newCert.title.trim()) {
      addToast('⚠️', 'Erreur', 'Le titre est requis')
      return
    }
    
    setUploading(true)
    try {
      await certifications.create({
        title: newCert.title,
        issuer: newCert.issuer,
        issue_date: newCert.issue_date || null,
        credential_id: newCert.credential_id,
        credential_url: newCert.credential_url
      })
      
      if (selectedFile) {
        await certifications.uploadFile(selectedFile)
      }
      
      addToast('✅', 'Certification ajoutée', `${newCert.title} a été ajoutée`)
      setShowCertForm(false)
      setNewCert({ title: '', issuer: '', issue_date: '', credential_id: '', credential_url: '' })
      setSelectedFile(null)
      fetchCertifications()
    } catch (error) {
      console.error('Erreur:', error)
      addToast('❌', 'Erreur', error.response?.data?.detail || "Impossible d'ajouter la certification")
    } finally {
      setUploading(false)
    }
  }

  const deleteCertification = async (id, title) => {
    if (window.confirm(`Supprimer la certification "${title}" ?`)) {
      try {
        await certifications.delete(id)
        addToast('🗑️', 'Supprimée', `La certification a été supprimée`)
        fetchCertifications()
      } catch (error) {
        addToast('❌', 'Erreur', "Impossible de supprimer")
      }
    }
  }

  const skillsByCategory = (category) => {
    return userSkills.filter(s => s.category === category)
  }

  const categories = SKILL_CATEGORIES.filter(cat => skillsByCategory(cat).length > 0)

  const getFullName = () => {
    if (user?.full_name) return user.full_name
    if (user?.first_name && user?.last_name) return `${user.first_name} ${user.last_name}`
    return 'Utilisateur'
  }

  const getYearLevel = () => user?.year_level || user?.yearLevel || 'B1'
  const getSpecialty = () => user?.specialty || 'Spécialité non renseignée'

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
                  if (refreshUser) await refreshUser()
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
          <Card>
            <div className="search-row">
              <Input 
                icon="🔍" 
                placeholder="Rechercher un étudiant par nom..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ flex: 1 }}
              />
            </div>
            
            <div className="filter-row">
              <select className="input" value={yearFilter} onChange={e => setYearFilter(e.target.value)} style={{ width: 'auto' }}>
                {YEAR_LEVELS.map(level => (
                  <option key={level} value={level}>{level === 'Tous' ? '📚 Tous niveaux' : `🎓 ${level}`}</option>
                ))}
              </select>
              
              <input 
                className="input" 
                placeholder="Filtrer par compétence..." 
                value={skillFilter}
                onChange={e => setSkillFilter(e.target.value)}
                style={{ width: 200 }}
              />
            </div>

            {searchingStudents ? (
              <div className="loading-spinner">
                <div className="spinner"></div>
                <div>Recherche d'étudiants...</div>
              </div>
            ) : students.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 60, color: 'var(--muted)' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
                <div>Aucun étudiant trouvé</div>
                <div style={{ fontSize: 12, marginTop: 8 }}>Essayez de modifier vos critères de recherche</div>
              </div>
            ) : (
              <div className="student-grid">
                {students.map(student => (
                  <div key={student.id} className="student-card">
                    <div className="student-header">
                      <div style={{
                        width: 48, height: 48, borderRadius: '50%',
                        background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20, color: 'white', fontWeight: 'bold',
                        flexShrink: 0
                      }}>
                        {student.full_name?.charAt(0) || '?'}
                      </div>
                      <div>
                        <div className="student-name">{student.full_name}</div>
                        <div className="student-meta">{student.year_level} · {student.specialty || 'Spécialité non renseignée'}</div>
                      </div>
                    </div>
                    
                    {student.bio && (
                      <div className="student-bio">{student.bio.substring(0, 80)}...</div>
                    )}
                    
                    <div className="student-skills">
                      {student.skills?.slice(0, 4).map((skill, idx) => (
                        <Tag key={idx} color="blue" size="sm">{skill.name}</Tag>
                      ))}
                      {student.skills?.length > 4 && (
                        <Tag color="muted" size="sm">+{student.skills.length - 4}</Tag>
                      )}
                    </div>
                    
                    <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                      <Btn size="sm" variant="primary" style={{ flex: 1 }} onClick={() => {
                        addToast('💬', 'Contacter', `Envoyer un message à ${student.full_name}`)
                      }}>
                        💬 Contacter
                      </Btn>
                      <Btn size="sm" variant="secondary" style={{ flex: 1 }} onClick={() => {
                        addToast('👥', 'Voir profil', `Profil de ${student.full_name}`)
                      }}>
                        👤 Voir
                      </Btn>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {tab === 'certifications' && (
        <div>
          <SectionHeader
            title="🏅 Certifications"
            sub="Gérez vos certifications professionnelles"
            action={<Btn onClick={() => setShowCertForm(!showCertForm)}>{showCertForm ? 'Annuler' : '+ Ajouter une certification'}</Btn>}
          />

          {showCertForm && (
            <Card style={{ marginBottom: 20 }}>
              <div style={{ marginBottom: 15, fontWeight: 700, fontSize: 14 }}>📜 Nouvelle certification</div>
              <div className="form-group">
                <label>Titre *</label>
                <input className="input" placeholder="Ex: AWS Certified Developer" value={newCert.title} onChange={e => setNewCert({...newCert, title: e.target.value})} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Émetteur</label>
                  <select className="input" value={newCert.issuer} onChange={e => setNewCert({...newCert, issuer: e.target.value})}>
                    <option value="">-- Sélectionner --</option>
                    <option value="LinkedIn">LinkedIn Learning</option>
                    <option value="Google">Google</option>
                    <option value="AWS">AWS</option>
                    <option value="Microsoft">Microsoft</option>
                    <option value="Coursera">Coursera</option>
                    <option value="Udemy">Udemy</option>
                    <option value="Autre">Autre</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Date d'obtention</label>
                  <input type="date" className="input" value={newCert.issue_date} onChange={e => setNewCert({...newCert, issue_date: e.target.value})} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>ID du certificat</label>
                  <input className="input" placeholder="Ex: 123456789" value={newCert.credential_id} onChange={e => setNewCert({...newCert, credential_id: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Lien de vérification</label>
                  <input className="input" placeholder="https://..." value={newCert.credential_url} onChange={e => setNewCert({...newCert, credential_url: e.target.value})} />
                </div>
              </div>
              <div className="form-group">
                <label>Fichier (PDF/Image)</label>
                <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileUpload} />
                {selectedFile && <div style={{ fontSize: 11, marginTop: 5, color: 'var(--green)' }}>✓ Fichier sélectionné: {selectedFile.name}</div>}
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <Btn variant="secondary" onClick={() => setShowCertForm(false)}>Annuler</Btn>
                <Btn onClick={addCertification} disabled={uploading}>{uploading ? 'Envoi...' : '💾 Enregistrer'}</Btn>
              </div>
            </Card>
          )}

          <Card title="📜 Mes certifications">
            {certifications.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🏅</div>
                <div>Aucune certification pour le moment</div>
                <Btn variant="secondary" style={{ marginTop: 16 }} onClick={() => setShowCertForm(true)}>
                  + Ajouter ma première certification
                </Btn>
              </div>
            ) : (
              certifications.map(cert => (
                <div key={cert.id} className="cert-card">
                  <div style={{ fontSize: 28 }}>🏅</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{cert.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                      {cert.issuer && `${cert.issuer} • `}
                      {cert.issue_date && new Date(cert.issue_date).toLocaleDateString('fr-FR')}
                    </div>
                    {cert.credential_id && <div style={{ fontSize: 10, color: 'var(--muted)' }}>ID: {cert.credential_id}</div>}
                  </div>
                  {cert.is_verified ? (
                    <Tag color="green">✓ Vérifiée</Tag>
                  ) : (
                    <Tag color="orange">En attente</Tag>
                  )}
                  <Btn size="sm" variant="secondary" onClick={() => deleteCertification(cert.id, cert.title)}>🗑️</Btn>
                </div>
              ))
            )}
          </Card>
        </div>
      )}
    </div>
  )
}