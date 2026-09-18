<template>
  <div class="pi-app">
    <header class="topbar">
      <router-link to="/modules" class="logo-slab" aria-label="Retour aux modules">
        <img src="/logo.png" alt="COFINA" class="logo" />
      </router-link>
      <div class="topbar-main">
        <h1>Paiement Instantané</h1>
        <div class="topbar-tools">
          <div class="period-box">
            <select v-model.number="selectedMonth" @change="loadData(false)">
              <option v-for="(month, index) in months" :key="month" :value="index + 1">{{ month }}</option>
            </select>
            <select v-model.number="selectedYear" @change="loadData(false)">
              <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
            </select>
            <button type="button" class="btn-refresh" :disabled="loading" @click="loadData(true)">
              {{ loading ? '…' : 'Actualiser' }}
            </button>
          </div>
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

    <div class="pi-body">
      <aside class="pi-aside">
        <div class="aside-brand">
          <span class="aside-badge">PI</span>
          <div>
            <strong>Menu</strong>
            <small>Paiement Instantané</small>
          </div>
        </div>
        <nav aria-label="Module PI">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="aside-item"
            :class="{ 'is-active': isActive(item.to) }"
          >
            <span class="aside-ico" aria-hidden="true">
              <svg v-if="item.icon === 'dash'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <rect x="3" y="3" width="7" height="7" rx="1.5" />
                <rect x="14" y="3" width="7" height="7" rx="1.5" />
                <rect x="3" y="14" width="7" height="7" rx="1.5" />
                <rect x="14" y="14" width="7" height="7" rx="1.5" />
              </svg>
              <svg v-else-if="item.icon === 'list'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M8 6h13M8 12h13M8 18h13" stroke-linecap="round" />
                <circle cx="4" cy="6" r="1.2" fill="currentColor" />
                <circle cx="4" cy="12" r="1.2" fill="currentColor" />
                <circle cx="4" cy="18" r="1.2" fill="currentColor" />
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M4 19V5M4 19h16" stroke-linecap="round" />
                <path d="M8 15v-4M12 15V8M16 15v-7" stroke-linecap="round" />
              </svg>
            </span>
            {{ item.label }}
          </router-link>
        </nav>
        <router-link to="/modules" class="aside-back">
          ← Modules
        </router-link>
      </aside>

      <main class="pi-main">
        <div v-if="errorMessage" class="state-banner">{{ errorMessage }}</div>
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { PROFILE_LABELS, ProfileManager } from '../utils/profiles.js';

const MONTHS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
];

export default {
  name: 'PiLayout',
  provide() {
    return {
      piState: this.piState,
    };
  },
  data() {
    const now = new Date();
    return {
      months: MONTHS,
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      loading: false,
      errorMessage: '',
      piState: {
        loading: false,
        error: '',
        data: null,
      },
      navItems: [
        { to: '/pi', label: 'Tableau de bord', icon: 'dash' },
        { to: '/pi/enrollements', label: 'Enrôlements', icon: 'list' },
        { to: '/pi/performance', label: 'Performance', icon: 'chart' },
      ],
    };
  },
  computed: {
    years() {
      const current = new Date().getFullYear();
      return [current - 1, current, current + 1];
    },
    currentUser() {
      return ProfileManager.getCurrentUser();
    },
    currentUserName() {
      return this.currentUser?.name || 'Utilisateur';
    },
    currentUserRole() {
      const code = this.currentUser?.profile?.code;
      return this.currentUser?.profile?.name || PROFILE_LABELS[code] || 'Utilisateur';
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
  async mounted() {
    await this.loadData();
  },
  methods: {
    isActive(to) {
      if (to === '/pi') {
        return this.$route.path === '/pi' || this.$route.path === '/pi/';
      }
      return this.$route.path.startsWith(to);
    },
    async loadData(refresh = false) {
      this.loading = true;
      this.errorMessage = '';
      this.piState.loading = true;
      this.piState.error = '';
      try {
        const { data } = await axios.get('/api/oracle/data/pi-dashboard', {
          params: {
            month: this.selectedMonth,
            year: this.selectedYear,
            refresh: refresh === true ? 1 : undefined,
          },
        });
        this.piState.data = data;
      } catch (error) {
        const message = error.response?.data?.message
          || error.response?.data?.detail
          || 'Impossible de charger le dashboard PI.';
        this.errorMessage = message;
        this.piState.error = message;
      } finally {
        this.loading = false;
        this.piState.loading = false;
      }
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
        this.$router.push('/');
      }
    },
  },
};
</script>

<style scoped>
.pi-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #eef2ef;
  color: #12231b;
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
  width: 228px;
  flex-shrink: 0;
  background: #f6f9f7;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
  border-right: 1px solid #dce5df;
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
  gap: 20px;
  padding: 0 28px;
  min-width: 0;
}

.topbar h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
  letter-spacing: -0.03em;
  white-space: nowrap;
}

.topbar-tools {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.period-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.period-box select,
.btn-refresh {
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
}

.period-box select option {
  color: #12231b;
}

.btn-refresh {
  cursor: pointer;
  font-weight: 600;
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: wait;
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

.pi-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.pi-aside {
  width: 228px;
  flex-shrink: 0;
  background: #f6f9f7;
  border-right: 1px solid #dce5df;
  padding: 20px 14px 16px;
  display: flex;
  flex-direction: column;
}

.aside-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 4px 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid #dce5df;
}

.aside-badge {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #163d2e;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 750;
  letter-spacing: 0.04em;
}

.aside-brand strong,
.aside-brand small {
  display: block;
}

.aside-brand strong {
  font-size: 13px;
  color: #12231b;
}

.aside-brand small {
  margin-top: 2px;
  color: #6b7c73;
  font-size: 11px;
}

.aside-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border-radius: 12px;
  text-decoration: none;
  color: #3d4f46;
  font-size: 14px;
  margin-bottom: 6px;
}

.aside-item:hover {
  background: #fff;
  color: #163d2e;
}

.aside-item.is-active {
  background: #163d2e;
  color: #fff;
  font-weight: 650;
  box-shadow: 0 8px 18px rgba(22, 61, 46, 0.16);
}

.aside-ico {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #fff;
  color: #163d2e;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.aside-item.is-active .aside-ico {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
}

.aside-ico svg {
  width: 15px;
  height: 15px;
}

.aside-back {
  margin-top: auto;
  display: block;
  padding: 11px 12px;
  border-radius: 12px;
  text-decoration: none;
  color: #5b6b63;
  font-size: 13px;
}

.aside-back:hover {
  background: #fff;
  color: #163d2e;
}

.pi-main {
  flex: 1;
  min-width: 0;
  overflow: auto;
  padding: 28px 32px 40px;
}

.state-banner {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fef2f2;
  color: #b91c1c;
}

@media (max-width: 980px) {
  .topbar-main,
  .topbar-tools,
  .pi-body {
    flex-direction: column;
    align-items: stretch;
  }

  .logo-slab,
  .pi-aside {
    width: 100%;
    border-right: 0;
  }

  .topbar-main {
    padding: 12px 18px;
  }

  .pi-main {
    padding: 20px 16px 32px;
  }
}
</style>
