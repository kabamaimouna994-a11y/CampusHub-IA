import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

export const exportSkillsToPDF = (user, skills) => {
  const doc = new jsPDF()
  
  // Utiliser une police standard
  doc.setFont('helvetica')
  
  doc.setFontSize(20)
  doc.setTextColor(79, 124, 255)
  doc.text('CampusHub IA - Mes competences', 105, 20, { align: 'center' })
  
  doc.setFontSize(12)
  doc.setTextColor(0, 0, 0)
  doc.text(`Nom: ${user?.fullName || 'Non renseigne'}`, 20, 50)
  doc.text(`Email: ${user?.email || 'Non renseigne'}`, 20, 60)
  doc.text(`Date: ${new Date().toLocaleDateString('fr-FR')}`, 20, 70)
  
  // Tableau sans emojis
  autoTable(doc, {
    startY: 90,
    head: [['Competence', 'Categorie', 'Niveau', 'Validee']],
    body: skills.map(skill => [
      skill.name,
      skill.category,
      skill.level,
      skill.is_validated ? 'Oui' : 'Non'
    ]),
    headStyles: { fillColor: [79, 124, 255], textColor: [255, 255, 255] }
  })
  
  doc.save(`competences_${user?.fullName?.replace(/\s/g, '_') || 'profil'}.pdf`)
}