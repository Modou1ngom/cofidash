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
            <router-link to="/admin" class="aside-item" exact-active-class="is-active" active-class="">
              Tableau de bord
            </router-link>
            <router-link to="/admin/users" class="aside-item" active-class="is-active">
              Utilisateurs
            </router-link>
            <router-link to="/admin/profiles" class="aside-item" active-class="is-active">
              Profils
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
  background: #f4f6f8;
  color: #111827;
  font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif;
}

.topbar {
  display: flex;
  min-height: 84px;
  background: #163d2e;
  color: #fff;
  box-shadow: 0 8px 24px rgba(15, 40, 30, 0.18);
}

.logo-slab {
  width: 196px;
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
  width: 196px;
  background: #fff;
  border-right: 1px solid #eef2f6;
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
}

.aside-product {
  margin: 0 0 16px;
  color: #94a3b8;
  font-size: 13px;
}

.aside-item {
  display: block;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: #334155;
  font-size: 14px;
  margin-bottom: 4px;
}

.aside-item.is-active {
  background: #fff1f2;
  color: #111827;
  font-weight: 600;
}

.aside-item--back {
  color: #64748b;
}

.admin-main {
  flex: 1;
  min-width: 0;
  overflow: auto;
  padding: 28px 32px;
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
