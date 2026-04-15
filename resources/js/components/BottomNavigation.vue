<template>
  <div class="bottom-navigation">
    <div class="nav-left">
      <div class="red-arrow-icon">→</div>
      <div class="accounting-date">Date comptable {{ currentDate }}</div>
    </div>
    <nav class="horizontal-nav">
      <a href="#" v-for="(item, index) in navItems" :key="item.label" class="nav-item">
        <div class="nav-icon-wrapper">
          <div class="nav-icon">{{ item.icon }}</div>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          <span class="nav-arrow-top">▼</span>
        </div>
        <span class="nav-text">{{ item.label }}</span>
      </a>
    </nav>
    <div class="nav-right">
      <div class="search-container">
        <div class="search-label">Nom client</div>
        <input type="text" v-model="clientName" class="client-input" />
        <button class="search-button">🔍</button>
      </div>
      <span class="icon search-plus">🔍</span>
      <span class="icon plus-icon">➕</span>
      <span class="icon">⭐</span>
      <span class="icon">📁</span>
      <span class="icon">←</span>
      <span class="icon">🔄</span>
      <span class="transaction-text">Transaction</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BottomNavigation',
  data() {
    return {
      clientName: 'DENIS',
      navItems: [
        { label: 'Accueil', icon: '🏠', badge: null },
        { label: 'Utilisateur', icon: '👤', badge: null },
        { label: 'Client', icon: '🤝', badge: null },
        { label: 'Recouvrement', icon: '🏦', badge: null },
        { label: 'Marketing', icon: '💰', badge: null },
        { label: 'Editions', icon: '🖨️', badge: null },
        { label: 'Consultations', icon: '📅', badge: '17' },
        { label: 'Actions', icon: '👆', badge: null },
        { label: 'Analytiques', icon: '📈', badge: null }
      ]
    }
  },
  computed: {
    currentDate() {
      const d = new Date();
      const day = String(d.getDate()).padStart(2, '0');
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = d.getFullYear();
      return `${day}/${month}/${year}`;
    }
  }
}
</script>

<style scoped>
.bottom-navigation {
  background: #6E8B7A;
  color: white;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 80px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.red-arrow-icon {
  width: 32px;
  height: 32px;
  background: #DC2626;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
}

.accounting-date {
  font-size: 14px;
  color: white;
}

.horizontal-nav {
  display: flex;
  gap: 20px;
  align-items: center;
  flex: 1;
  overflow-x: auto;
}

.nav-item {
  color: white;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.2s;
  min-width: 70px;
  position: relative;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon {
  font-size: 24px;
}

.nav-arrow-top {
  font-size: 10px;
  position: absolute;
  top: -8px;
  right: -8px;
  color: white;
}

.nav-badge {
  position: absolute;
  top: -6px;
  left: -6px;
  background: #DC2626;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
  border: 2px solid white;
}

.nav-text {
  font-size: 12px;
  white-space: nowrap;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-container {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 4px;
  overflow: hidden;
}

.search-label {
  background: #F5F5F5;
  padding: 8px 12px;
  font-size: 13px;
  color: #666;
  border-right: 1px solid #E0E0E0;
}

.client-input {
  border: none;
  outline: none;
  padding: 8px 12px;
  font-size: 13px;
  color: #333;
  min-width: 150px;
}

.search-button {
  background: #F97316;
  border: none;
  padding: 8px 12px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.icon {
  cursor: pointer;
  font-size: 18px;
  color: white;
  transition: transform 0.2s;
}

.icon:hover {
  transform: scale(1.2);
}

.search-plus {
  position: relative;
}

.search-plus::after {
  content: '➕';
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 12px;
}

.transaction-text {
  font-size: 12px;
  color: white;
  margin-left: 5px;
}
</style>

