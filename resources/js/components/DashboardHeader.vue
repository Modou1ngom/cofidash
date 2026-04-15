<template>
  <header class="dashboard-header">
    <div class="header-left-section">
      <div class="logo-area">
        <div class="logo-container">
          <img src="/logo.png" alt="COFINA Logo" class="logo-icon" />
          <div class="logo-text-container">
            
          </div>
        </div>
        <!--<div class="red-arrow-button">→</div>-->
      </div>
      <div class="user-bar">
        <div class="user-info">
          <span class="calendar-icon">📅</span>
          <div class="user-name">{{ currentUserName }}</div>
        </div>
      </div>
    </div>
    <div class="header-center-section">
      <div class="accounting-date">Date comptable {{ currentDate }}</div>
      <nav class="horizontal-nav">
        <div 
          v-for="(item, index) in visibleNavItems" 
          :key="item.label" 
          class="nav-item-wrapper"
          @mouseenter="item.submenu ? showUserSubmenu = true : null"
          @mouseleave="item.submenu ? showUserSubmenu = false : null"
        >
          <router-link 
            v-if="item.route && !item.submenu"
            :to="item.route" 
            class="nav-item"
          >
            <div class="nav-icon">{{ item.icon }}</div>
            <span class="nav-text">{{ item.label }}</span>
            <span class="nav-arrow">▼</span>
          </router-link>
          <a 
            v-else
            href="#" 
            class="nav-item"
            @click.prevent="item.submenu ? null : null"
          >
            <div class="nav-icon">{{ item.icon }}</div>
            <span class="nav-text">{{ item.label }}</span>
            <span class="nav-arrow">▼</span>
          </a>
          <div v-if="item.submenu && showUserSubmenu" class="nav-submenu">
            <router-link 
              v-for="subitem in item.submenu" 
              :key="subitem.label"
              :to="subitem.route" 
              class="nav-submenu-item"
              @click="showUserSubmenu = false"
            >
              {{ subitem.label }}
            </router-link>
          </div>
        </div>
      </nav>
    </div>
    <div class="header-right-section">
      <div class="search-container">
        <div class="search-label">Nom client</div>
        <input type="text" v-model="clientName" class="client-input" />
        <button class="search-button">🔍</button>
      </div>
      <button class="logout-button" @click="logout" title="Déconnexion">
        <span class="icon">⏻</span>
      </button>
    </div>
  </header>
</template>

<script>
import { useRouter } from 'vue-router';
import { ProfileManager } from '../utils/profiles.js';
import axios from 'axios';

export default {
  name: 'DashboardHeader',
  setup() {
    const router = useRouter();
    return { router };
  },
  data() {
    return {
      clientName: ' ',
      navItems: [
        { label: 'Accueil', icon: '🏠', route: '/dashboard' },
        { label: 'Utilisateur', icon: '👤', route: null, adminOnly: true, submenu: [
          { label: 'Gestion Utilisateurs', route: '/admin/users' },
          { label: 'Gestion Profils', route: '/admin/profiles' }
        ]},
        { label: 'Client VUE 360', icon: '🤝', route: '/dashboard' }
      ],
      showUserSubmenu: false
    }
  },
  computed: {
    currentDate() {
      const d = new Date();
      const day = String(d.getDate()).padStart(2, '0');
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const year = d.getFullYear();
      return `${day}/${month}/${year}`;
    },
    currentUser() {
      return ProfileManager.getCurrentUser();
    },
    currentUserName() {
      return this.currentUser?.name || 'Utilisateur';
    },
    currentUserProfile() {
      return ProfileManager.getCurrentProfileData();
    },
    isAdmin() {
      return ProfileManager.isAdmin();
    },
    visibleNavItems() {
      return this.navItems.filter(item => {
        if (item.adminOnly) {
          return this.isAdmin;
        }
        return true;
      });
    }
  },
  methods: {
    goHome() {
      this.router.push('/');
    },
    async logout() {
      try {
        await axios.post('/api/logout');
      } catch (error) {
        console.error('Erreur lors de la déconnexion:', error);
      } finally {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('userProfile');
        this.router.push('/');
      }
    }
  }
}
</script>

<style scoped>
.dashboard-header {
  background: #6E8B7A;
  color: white;
  display: flex;
  align-items: stretch;
  width: 100%;
  min-height: 100px;
  flex-wrap: wrap;
}

.header-left-section {
  display: flex;
  flex-direction: column;
  width: 260px;
  min-width: 260px;
  flex-shrink: 0;
}

.logo-area {
  background: rgb(255, 253, 253);
  padding: 15px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.logo-icon {
  width: auto;
  height: 110px;
  max-width: 180px;
  object-fit: contain;
  border-radius: 4px;
}

.logo-text-container {
  display: flex;
  flex-direction: column;
}

.logo-main {
  font-size: 16px;
  font-weight: 600;
  color: #000;
  line-height: 1.2;
}

.logo-sub {
  font-size: 11px;
  color: #666;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.user-bar {
  background: hsl(0, 93%, 40%);
  color: rgb(255, 255, 255);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  font-size: 14px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.calendar-icon {
  font-size: 18px;
}

.red-arrow-button {
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

.header-center-section {
  flex: 1;
  min-width: 0;
  background: #6E8B7A;
  display: flex;
  flex-direction: column;
  padding: 12px 20px;
}

.accounting-date {
  font-size: 14px;
  color: white;
  margin-bottom: 8px;
}

.horizontal-nav {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.nav-item {
  color: white;
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.2s;
  min-width: 70px;
  position: relative;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.router-link-active {
  background: rgba(255, 255, 255, 0.15);
}

.nav-item-wrapper {
  position: relative;
}

.nav-submenu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  background: white;
  border: 1px solid #DDD;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
}

.nav-submenu-item {
  display: block;
  padding: 12px 16px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
  transition: background 0.2s;
  border-bottom: 1px solid #F0F0F0;
}

.nav-submenu-item:last-child {
  border-bottom: none;
}

.nav-submenu-item:hover {
  background: #F5F5F5;
}

.nav-submenu-item.router-link-active {
  background: #E8F5E9;
  color: #1A4D3A;
  font-weight: 500;
}

.nav-icon {
  font-size: 24px;
  margin-bottom: 2px;
}

.nav-text {
  font-size: 11px;
  white-space: nowrap;
}

.nav-arrow {
  font-size: 9px;
  position: absolute;
  top: 4px;
  right: 4px;
  color: white;
}

.header-right-section {
  background: #6E8B7A;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  flex-shrink: 0;
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
  min-width: 120px;
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

.logout-button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, opacity 0.2s;
  border-radius: 4px;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}

.logout-button .icon {
  font-size: 20px;
  color: white;
}

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .header-left-section {
    width: 220px;
    min-width: 220px;
  }
  
  .logo-icon {
    height: 90px;
    max-width: 150px;
  }
  
  .horizontal-nav {
    gap: 15px;
  }
  
  .nav-item {
    min-width: 60px;
    padding: 6px 10px;
  }
  
  .nav-icon {
    font-size: 20px;
  }
  
  .nav-text {
    font-size: 10px;
  }
  
  .search-container {
    min-width: 100px;
  }
  
  .client-input {
    min-width: 100px;
    padding: 6px 10px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    min-height: auto;
  }
  
  .header-left-section {
    width: 100%;
    min-width: 100%;
  }
  
  .logo-area {
    padding: 10px 15px;
  }
  
  .logo-icon {
    height: 70px;
    max-width: 120px;
  }
  
  .user-bar {
    padding: 10px 15px;
    font-size: 12px;
  }
  
  .header-center-section {
    padding: 10px 15px;
  }
  
  .accounting-date {
    font-size: 12px;
    margin-bottom: 6px;
  }
  
  .horizontal-nav {
    gap: 10px;
    flex-wrap: wrap;
  }
  
  .nav-item {
    min-width: 50px;
    padding: 6px 8px;
  }
  
  .nav-icon {
    font-size: 18px;
  }
  
  .nav-text {
    font-size: 9px;
  }
  
  .header-right-section {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    padding: 10px 15px;
  }
  
  .search-container {
    width: 100%;
    min-width: 100%;
  }
  
  .search-label {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .client-input {
    flex: 1;
    min-width: 0;
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .search-button {
    padding: 6px 10px;
    font-size: 14px;
  }
  
  .logout-button {
    align-self: flex-end;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .logo-area {
    padding: 8px 12px;
  }
  
  .logo-icon {
    height: 60px;
    max-width: 100px;
  }
  
  .user-bar {
    padding: 8px 12px;
    font-size: 11px;
  }
  
  .calendar-icon {
    font-size: 16px;
  }
  
  .header-center-section {
    padding: 8px 12px;
  }
  
  .accounting-date {
    font-size: 11px;
    margin-bottom: 4px;
  }
  
  .horizontal-nav {
    gap: 8px;
  }
  
  .nav-item {
    min-width: 45px;
    padding: 5px 6px;
  }
  
  .nav-icon {
    font-size: 16px;
  }
  
  .nav-text {
    font-size: 8px;
  }
  
  .header-right-section {
    padding: 8px 12px;
  }
  
  .search-label {
    padding: 5px 8px;
    font-size: 11px;
  }
  
  .client-input {
    padding: 5px 8px;
    font-size: 11px;
  }
  
  .search-button {
    padding: 5px 8px;
    font-size: 12px;
  }
}
</style>

