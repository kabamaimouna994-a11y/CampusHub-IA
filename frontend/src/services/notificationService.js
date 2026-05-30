// Service de notifications push
class NotificationService {
  constructor() {
    this.permission = false
    this.registration = null
  }

  // Demander la permission
  async requestPermission() {
    if (!('Notification' in window)) {
      console.log('Ce navigateur ne supporte pas les notifications')
      return false
    }

    const permission = await Notification.requestPermission()
    this.permission = permission === 'granted'
    
    if (this.permission) {
      console.log('✅ Notifications activées')
      this.registerServiceWorker()
    }
    
    return this.permission
  }

  // Enregistrer le Service Worker
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.registration = await navigator.serviceWorker.register('/sw.js')
        console.log('✅ Service Worker enregistré')
      } catch (error) {
        console.error('❌ Erreur Service Worker:', error)
      }
    }
  }

  // Afficher une notification
  showNotification(title, body, icon = '/logo.png') {
    if (!this.permission) return
    
    const options = {
      body: body,
      icon: icon,
      badge: '/badge.png',
      vibrate: [200, 100, 200],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1,
        url: window.location.origin
      },
      actions: [
        { action: 'open', title: 'Ouvrir' },
        { action: 'close', title: 'Fermer' }
      ]
    }

    if (this.registration && this.registration.showNotification) {
      this.registration.showNotification(title, options)
    } else if (Notification.permission === 'granted') {
      new Notification(title, options)
    }
  }

  // Notification pour nouveau message
  notifyNewMessage(senderName, messageContent) {
    this.showNotification(
      `📨 Nouveau message de ${senderName}`,
      messageContent.substring(0, 100),
      '/avatar.png'
    )
  }

  // Notification pour rappel de session
  notifySessionReminder(mentorName, sessionTime) {
    this.showNotification(
      '🧑‍🏫 Rappel de session',
      `Votre session avec ${mentorName} commence bientôt (${sessionTime})`,
      '/calendar.png'
    )
  }

  // Notification pour nouvelle demande de mentorat
  notifyNewMentorshipRequest(studentName) {
    this.showNotification(
      '🔔 Nouvelle demande de mentorat',
      `${studentName} souhaite devenir votre mentoré`,
      '/mentor.png'
    )
  }

  // Notification pour validation de compétence
  notifySkillValidated(skillName) {
    this.showNotification(
      '✅ Compétence validée',
      `Votre compétence "${skillName}" a été validée`,
      '/skill.png'
    )
  }

  // Notification pour nouvel événement
  notifyNewEvent(eventTitle, eventDate) {
    this.showNotification(
      '🎉 Nouvel événement',
      `${eventTitle} - ${new Date(eventDate).toLocaleDateString('fr-FR')}`,
      '/event.png'
    )
  }
}

export default new NotificationService()