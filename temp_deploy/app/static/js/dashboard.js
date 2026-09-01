document.addEventListener('DOMContentLoaded', function() {
    // ===== BOUTONS D'HUMEUR =====
    const moodBtns = document.querySelectorAll('.mood-btn');
    moodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            moodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const mood = this.textContent.trim();
            showNotification('🔍 Filtrage pour : ' + mood);
        });
    });

    // ===== SURPRENDS-MOI =====
    const surpriseBtn = document.querySelector('.btn-surprise');
    if (surpriseBtn) {
        surpriseBtn.addEventListener('click', function() {
            const suggestions = [
                'Dîner romantique au bord du Wouri 🌅',
                'Visite guidée du Musée Maritime ⚓',
                'Balade en bateau sur le fleuve 🚤',
                'Dégustation de fruits de mer à la plage 🦐',
                'Concert de musique traditionnelle 🎵',
                'Safari photo dans les quartiers historiques 📸'
            ];
            const random = suggestions[Math.floor(Math.random() * suggestions.length)];
            showNotification('✨ Surprise ! ' + random);
        });
    }

    // ===== FAVORIS =====
    const favBtn = document.querySelector('.btn-favorite');
    if (favBtn) {
        favBtn.addEventListener('click', function() {
            if (this.textContent.includes('❤️')) {
                this.textContent = '✅ Ajouté aux favoris';
                this.classList.add('added');
                showNotification('❤️ Ajouté aux favoris !');
            } else {
                this.textContent = '❤️ Ajouter aux favoris';
                this.classList.remove('added');
            }
        });
    }
});

// ===== NOTIFICATION =====
function showNotification(message) {
    const old = document.querySelector('.custom-notification');
    if (old) old.remove();
    
    const notif = document.createElement('div');
    notif.className = 'custom-notification';
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notif.remove(), 300);
    }, 3000);
}