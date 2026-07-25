<template>
  <header class="dashboard-header">
    <div class="header-brand">
      <div class="logo-area">
        <img src="/logo.png" alt="COFINA" class="logo-icon" />
      </div>
      <div class="user-bar">
        <span class="user-avatar">{{ userInitials }}</span>
        <div class="user-details">
          <span class="user-name">{{ currentUserName }}</span>
          <span class="user-role">{{ currentUserProfile?.code || 'Profil' }}</span>
        </div>
      </div>
    </div>

    <div class="header-main">
      <div class="header-top-row">
        <div class="date-chip">
          <svg class="date-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="4" width="18" height="18" rx="2" />
            <path d="M16 2v4M8 2v4M3 10h18" stroke-linecap="round" />
          </svg>
          <span>Date comptable <strong>{{ currentDate }}</strong></span>
        </div>
      </div>

      <nav class="horizontal-nav" aria-label="Navigation principale">
        <div
          v-for="item in visibleNavItems"
          :key="item.label"
          class="nav-item-wrapper"
        >
          <router-link
            :to="item.route"
            class="nav-pill"
            :class="{ 'nav-pill--active': isNavActive(item) }"
          >
            <span class="nav-pill-icon">{{ item.icon }}</span>
            <span class="nav-pill-label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>
    </div>

    <div class="header-actions">
      <div class="search-box">
        <label class="sr-only" for="header-client-search">Recherche client</label>
        <div class="search-field">
          <svg class="search-field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="7" />
            <path d="M20 20l-3.5-3.5" stroke-linecap="round" />
          </svg>
          <input
            id="header-client-search"
            v-model="clientName"
            type="text"
            class="client-input"
            placeholder="Nom, matricule, compte ou téléphone…"
            @keyup.enter="searchClient"
          />
        </div>
        <button type="button" class="search-submit" @click="searchClient">
          Rechercher
        </button>
      </div>
      <button class="logout-button" type="button" @click="logout" title="Déconnexion">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" stroke-linecap="round" />
          <path d="M16 17l5-5-5-5M21 12H9" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
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
      clientName: '',
      navItems: [
        { label: 'Accueil', icon: '🏠', route: '/dashboard' },
        { label: 'Client Vue 360°', icon: '🤝', route: '/vue360/recherche' },
        { label: 'Vue ensemble CAF', icon: '📊', route: '/vue360/caf' },
      ],
    };
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
    userInitials() {
      const name = this.currentUserName;
      return name
        .split(' ')
        .slice(0, 2)
        .map((p) => p[0])
        .join('')
        .toUpperCase() || 'U';
    },
    visibleNavItems() {
      if (ProfileManager.isCAF()) {
        return this.navItems
          .filter((item) => item.route !== '/vue360/caf')
          .map((item) => (
            item.route === '/dashboard'
              ? { ...item, route: '/vue360/caf' }
              : item
          ));
      }
      if (ProfileManager.isCC()) {
        return this.navItems.filter((item) => item.route === '/vue360/recherche');
      }
      return this.navItems;
    },
  },
  methods: {
    isNavActive(item) {
      if (!item.route) return false;
      if (item.route === '/vue360/recherche') {
        return this.$route.path.startsWith('/vue360/recherche')
          || this.$route.path.startsWith('/vue360/clients');
      }
      if (item.route === '/vue360/caf') {
        return this.$route.path.startsWith('/vue360/caf');
      }
      if (item.route === '/dashboard') {
        return this.$route.path === '/dashboard' || this.$route.path.startsWith('/dashboard/');
      }
      return this.$route.path === item.route || this.$route.path.startsWith(`${item.route}/`);
    },
    searchClient() {
      const query = this.clientName.trim();
      if (!query) {
        this.router.push('/vue360/recherche');
        return;
      }
      this.router.push({ path: '/vue360/recherche', query: { q: query } });
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
    },
  },
};
</script>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.dashboard-header {
  display: flex;
  align-items: stretch;
  width: 100%;
  min-height: 88px;
  background: linear-gradient(135deg, #1a4d3a 0%, #2d6a4f 55%, #3d7a5c 100%);
  box-shadow: 0 2px 12px rgba(26, 77, 58, 0.2);
}

/* ── Marque + utilisateur ── */
.header-brand {
  display: flex;
  flex-direction: column;
  width: var(--cofidash-sidebar-width);
  min-width: var(--cofidash-sidebar-width);
  max-width: var(--cofidash-sidebar-width);
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  box-sizing: border-box;
}

.logo-area {
  flex: 1;
  min-height: 72px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  box-sizing: border-box;
}

.logo-icon {
  height: 48px;
  width: auto;
  max-width: 100%;
  object-fit: contain;
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--cofidash-rail-bar-height);
  min-height: var(--cofidash-rail-bar-height);
  max-height: var(--cofidash-rail-bar-height);
  padding: 0 14px;
  background: linear-gradient(90deg, #b91c1c 0%, #dc2626 100%);
  color: #fff;
  box-sizing: border-box;
  width: 100%;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.user-name {
  font-size: 0.82rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 0.68rem;
  opacity: 0.85;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Centre : date + navigation ── */
.header-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 12px 24px;
  gap: 10px;
}

.header-top-row {
  display: flex;
  align-items: center;
}

.date-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.9);
}

.date-chip strong {
  font-weight: 600;
  color: #fff;
}

.date-icon {
  width: 14px;
  height: 14px;
  opacity: 0.85;
}

.horizontal-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.nav-item-wrapper {
  position: relative;
}

.nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.15s, box-shadow 0.2s;
  white-space: nowrap;
}

.nav-pill:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
}

.nav-pill--active {
  background: #fff;
  color: #1a4d3a;
  border-color: #fff;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  font-weight: 600;
}

.nav-pill-icon {
  font-size: 1rem;
  line-height: 1;
}

.nav-pill-label {
  line-height: 1.2;
}

/* ── Recherche + déconnexion ── */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  flex-shrink: 0;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.search-box {
  display: flex;
  align-items: stretch;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  min-width: 280px;
  max-width: 380px;
}

.search-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  min-width: 0;
}

.search-field-icon {
  width: 18px;
  height: 18px;
  color: #9ca3af;
  flex-shrink: 0;
}

.client-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 11px 0;
  font-size: 0.85rem;
  color: #111827;
  min-width: 0;
  background: transparent;
}

.client-input::placeholder {
  color: #9ca3af;
}

.search-submit {
  padding: 0 18px;
  border: none;
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.15s;
}

.search-submit:hover {
  opacity: 0.92;
}

.logout-button {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
  flex-shrink: 0;
}

.logout-button svg {
  width: 20px;
  height: 20px;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

@media (max-width: 1200px) {
  .logo-icon {
    height: 44px;
  }

  .search-box {
    min-width: 220px;
    max-width: 300px;
  }

  .search-submit {
    padding: 0 14px;
    font-size: 0.75rem;
  }
}

@media (max-width: 992px) {
  .dashboard-header {
    flex-wrap: wrap;
  }

  .header-brand {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    flex-direction: row;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .logo-area {
    flex: 0 0 auto;
    min-height: 56px;
    padding: 8px 16px;
  }

  .user-bar {
    flex: 1;
    justify-content: flex-end;
    max-width: none;
  }

  .header-actions {
    width: 100%;
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    justify-content: stretch;
  }

  .search-box {
    flex: 1;
    max-width: none;
  }
}

@media (max-width: 640px) {
  .header-main {
    padding: 10px 14px;
  }

  .nav-pill {
    padding: 8px 12px;
    font-size: 0.78rem;
  }

  .header-actions {
    padding: 10px 14px;
    gap: 8px;
  }

  .search-submit span {
    display: none;
  }
}
</style>
