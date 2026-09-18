<template>
  <div class="hub">
    <header class="topbar">
      <div class="logo-slab">
        <img src="/logo.png" alt="COFINA" class="logo" />
      </div>
      <div class="topbar-main">
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

    <main class="hub-main">
      <section class="intro">
        <h2>Sélectionnez un module</h2>
        <p>Accédez à l’espace correspondant à votre activité.</p>
      </section>

      <section class="cards" aria-label="Modules disponibles">
        <article
          v-for="module in visibleModules"
          :key="module.id"
          class="card"
          :class="`card--${module.tone}`"
          role="link"
          tabindex="0"
          @click="openModule(module.route)"
          @keydown.enter.prevent="openModule(module.route)"
        >
          <div class="card-icon" aria-hidden="true" v-html="module.icon" />
          <h3>{{ module.title }}</h3>
          <p>{{ module.description }}</p>
          <ul>
            <li v-for="item in module.points" :key="item">{{ item }}</li>
          </ul>
          <span class="card-cta">Ouvrir le module</span>
        </article>
      </section>

      <p v-if="!visibleModules.length" class="empty">
        Aucun module n’est disponible pour votre profil.
      </p>
    </main>
  </div>
</template>

<script>
import axios from 'axios';
import { PERMISSIONS, PROFILE_LABELS, ProfileManager } from '../utils/profiles.js';

const ICONS = {
  admin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 12a4 4 0 100-8 4 4 0 000 8z" stroke-linecap="round"/><path d="M4 20a8 8 0 0116 0" stroke-linecap="round"/></svg>',
  cofidash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 19V5M4 19h16" stroke-linecap="round"/><path d="M8 15l4-5 3 3 5-7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  pi: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" stroke-linejoin="round"/></svg>',
};

export default {
  name: 'ModulesPage',
  computed: {
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
      return this.currentUserName
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0])
        .join('')
        .toUpperCase();
    },
    visibleModules() {
      return [
        {
          id: 'administration',
          title: 'Administration',
          description: 'Gérez les comptes, les profils et les droits d’accès à la plateforme.',
          points: ['Utilisateurs', 'Profils', 'Permissions'],
          route: '/admin',
          tone: 'red',
          icon: ICONS.admin,
          visible: ProfileManager.isAdmin(),
        },
        {
          id: 'cofidash',
          title: 'Cofidash',
          description: 'Pilotez l’activité commerciale, les clients, les performances et les objectifs.',
          points: ['Tableau de bord', 'Vue 360', 'CAF'],
          route: this.cofidashRoute,
          tone: 'navy',
          icon: ICONS.cofidash,
          visible: this.canOpenCofidash,
        },
        {
          id: 'pi',
          title: 'Paiement Instantané',
          description: 'Suivez les enrôlements PI / SPI, Mobile + et USSD.',
          points: ['Dashboard PI', 'Enrôlements', 'Mobile +'],
          route: '/pi',
          tone: 'green',
          icon: ICONS.pi,
          visible: ProfileManager.canAccessSection('pi'),
        },
      ].filter((module) => module.visible);
    },
    canOpenCofidash() {
      return ProfileManager.hasDashboardMenuAccess()
        || ProfileManager.hasPermission(PERMISSIONS.VIEW_DASHBOARD)
        || ProfileManager.canViewVue360()
        || ProfileManager.canAccessSection('caf-overview');
    },
    cofidashRoute() {
      if (ProfileManager.hasDashboardMenuAccess() || ProfileManager.hasPermission(PERMISSIONS.VIEW_DASHBOARD)) {
        return '/dashboard';
      }
      if (ProfileManager.canAccessSection('caf-overview')) {
        return '/vue360/caf';
      }
      if (ProfileManager.canViewVue360()) {
        return '/vue360/recherche';
      }
      return '/dashboard';
    },
  },
  async mounted() {
    await ProfileManager.refreshCurrentUser();
  },
  methods: {
    openModule(route) {
      this.$router.push(route);
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
.hub {
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

.hub-main {
  flex: 1;
  width: min(1120px, calc(100% - 64px));
  margin: 0 auto;
  padding: 48px 0 56px;
}

.intro {
  margin-bottom: 28px;
}

.intro h2 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 650;
  letter-spacing: -0.03em;
}

.intro p {
  margin: 0;
  color: #5b6b63;
  font-size: 15px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
}

.card {
  background: #fff;
  border: 1px solid #dce5df;
  border-radius: 16px;
  padding: 28px 26px 24px;
  min-height: 292px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(18, 35, 27, 0.04);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.card:hover,
.card:focus-visible {
  transform: translateY(-3px);
  border-color: #c5d2ca;
  box-shadow: 0 16px 32px rgba(18, 35, 27, 0.1);
  outline: none;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.card-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.card--red .card-icon {
  background: #fde8ea;
  color: #c81e2d;
}

.card--navy .card-icon {
  background: #e8eef5;
  color: #12355b;
}

.card--green .card-icon {
  background: #e5f4ea;
  color: #15803d;
}

.card h3 {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: 650;
}

.card p {
  margin: 0 0 18px;
  color: #5b6b63;
  font-size: 14px;
  line-height: 1.55;
}

.card ul {
  margin: 0 0 22px;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.card li {
  padding: 4px 9px;
  border-radius: 999px;
  background: #f4f7f5;
  color: #3d5248;
  font-size: 12px;
  font-weight: 600;
}

.card-cta {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  border-radius: 10px;
  padding: 11px 14px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.card--red .card-cta { background: #c81e2d; }
.card--navy .card-cta { background: #12355b; }
.card--green .card-cta { background: #15803d; }

.empty {
  color: #5b6b63;
}

@media (max-width: 980px) {
  .cards {
    grid-template-columns: 1fr;
  }

  .logo-slab {
    width: 140px;
  }

  .topbar-main {
    padding: 12px 18px;
  }

  .hub-main {
    width: calc(100% - 32px);
    padding-top: 28px;
  }
}

@media (max-width: 720px) {
  .topbar {
    flex-direction: column;
    min-height: 0;
  }

  .logo-slab {
    width: 100%;
  }

  .topbar-user {
    width: 100%;
    justify-content: space-between;
  }

  .user-chip {
    min-width: 0;
  }
}
</style>
