<template>
  <div class="admin-app">
    <header class="topbar">
      <div class="logo-slab">
        <img src="/logo.png" alt="COFINA" class="logo" />
      </div>
      <div class="topbar-main">
        <h1>Administration</h1>
        <div class="topbar-user">
          <div class="user-chip">
            <span class="avatar">{{ userInitials }}</span>
            <div class="user-meta">
              <strong>{{ currentUserName }}</strong>
              <span>{{ currentUserRole }}</span>
            </div>
          </div>
          <button type="button" class="logout-btn" @click="logout">Déconnexion</button>
        </div>
      </div>
    </header>

    <div class="admin-body">
      <aside class="admin-aside">
        <div class="aside-top">
          <p class="aside-product">Navigation</p>
          <nav aria-label="Administration">
            <router-link v-if="isAdmin" to="/admin" class="aside-item" exact-active-class="is-active" active-class="">
              <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
              Tableau de bord
            </router-link>
            <router-link v-if="canManageData" to="/admin/organisation" class="aside-item" active-class="is-active">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10" stroke-linecap="round"/></svg>
              Données
            </router-link>
            <router-link v-if="canManageEnvironments" to="/admin/environnements" class="aside-item" active-class="is-active">
              <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.2 2.4 3.3 5.1 3.3 8S14.2 17.6 12 20c-2.2-2.4-3.3-5.1-3.3-8S9.8 6.4 12 4z"/></svg>
              Environnements
            </router-link>
          </nav>
        </div>
        <router-link to="/modules" class="aside-item aside-item--back">
          ← Modules
        </router-link>
      </aside>

      <main class="admin-main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { PROFILE_LABELS, ProfileManager } from '../utils/profiles.js';

export default {
  name: 'AdminLayout',
  computed: {
    currentUser() {
      return ProfileManager.getCurrentUser();
    },
    currentUserName() {
      return this.currentUser?.name || 'Utilisateur';
    },
    currentUserRole() {
      const code = this.currentUser?.profile?.code;
      return this.currentUser?.profile?.name || PROFILE_LABELS[code] || 'Administrateur';
    },
    userInitials() {
      return (this.currentUserName || '')
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0])
        .join('')
        .toUpperCase();
    },
    isAdmin() {
      return ProfileManager.isAdmin();
    },
    canManageData() {
      return ProfileManager.isAdmin() || ProfileManager.canAccessSection('management');
    },
    canManageEnvironments() {
      return ProfileManager.isAdmin() || ProfileManager.canAccessSection('environments');
    },
  },
  methods: {
    async logout() {
      try {
        await axios.post('/api/logout');
      } catch (error) {
        console.error('Erreur lors de la déconnexion:', error);
      } finally {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('userProfile');
        this.$router.push('/');
      }
    },
  },
};
</script>

<style scoped>
.admin-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f3f6f4;
  color: #1c2430;
  font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;
}

.topbar {
  display: flex;
  min-height: 76px;
  background: linear-gradient(135deg, #1a4d3a 0%, #2d6a4f 55%, #3d7a5c 100%);
  color: #fff;
  box-shadow: 0 1px 0 rgba(15, 40, 30, 0.12);
}

.logo-slab {
  width: 228px;
  flex-shrink: 0;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
}

.logo {
  height: 46px;
  width: auto;
  max-width: 100%;
  object-fit: contain;
}

.topbar-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 36px;
}

.topbar h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
  letter-spacing: -0.03em;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #fff;
  color: #163d2e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.user-meta strong {
  font-size: 13px;
}

.user-meta span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.logout-btn {
  border: 1px solid rgba(255, 255, 255, 0.28);
  background: transparent;
  color: #fff;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.admin-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.admin-aside {
  width: 228px;
  background: #fff;
  border-right: 1px solid #e6ece8;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
}

.aside-product {
  margin: 0 0 14px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.aside-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: #334155;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  transition: background 0.15s, color 0.15s;
}

.aside-item svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.aside-item:hover {
  background: #f3f6f4;
  color: #1a4d3a;
}

.aside-item.is-active {
  background: #e7f2ec;
  color: #1a4d3a;
  font-weight: 650;
}

.aside-item--back {
  color: #64748b;
  font-size: 13px;
}

.aside-item--back:hover {
  background: transparent;
  color: #1a4d3a;
}

.admin-main {
  flex: 1;
  min-width: 0;
  overflow: auto;
  padding: 28px 36px 40px;
}

@media (max-width: 900px) {
  .admin-body {
    flex-direction: column;
  }

  .admin-aside {
    width: 100%;
  }
}
</style>
