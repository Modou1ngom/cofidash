<template>
  <div class="admin-home">
    <div v-if="loading" class="state">Chargement de l’administration…</div>
    <div v-else-if="error" class="state error">{{ error }}</div>

    <template v-else>
      <section class="kpi-grid">
        <article class="kpi">
          <span>Utilisateurs</span>
          <strong>{{ users.length }}</strong>
        </article>
        <article class="kpi">
          <span>Profils</span>
          <strong>{{ profiles.length }}</strong>
        </article>
        <article class="kpi">
          <span>Profils actifs</span>
          <strong>{{ activeProfiles }}</strong>
        </article>
      </section>

      <section class="cards">
        <article class="card">
          <h2>Utilisateurs</h2>
          <p>Créer, modifier et supprimer les comptes de la plateforme.</p>
          <button type="button" class="open-btn" @click="$router.push('/admin/users')">
            Gérer les utilisateurs
          </button>
        </article>
        <article class="card">
          <h2>Profils</h2>
          <p>Définir les droits, menus et accès de chaque profil.</p>
          <button type="button" class="open-btn" @click="$router.push('/admin/profiles')">
            Gérer les profils
          </button>
        </article>
      </section>

      <section class="table-card">
        <div class="table-head">
          <h2>Derniers utilisateurs</h2>
          <button type="button" class="link-btn" @click="$router.push('/admin/users')">
            Voir tout
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Profil</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in recentUsers" :key="user.id">
              <td>{{ user.name }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.profile?.name || '—' }}</td>
            </tr>
            <tr v-if="!recentUsers.length">
              <td colspan="3" class="empty">Aucun utilisateur</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AdminModulePage',
  data() {
    return {
      loading: true,
      error: '',
      users: [],
      profiles: [],
    };
  },
  computed: {
    activeProfiles() {
      return this.profiles.filter((profile) => profile.is_active).length;
    },
    recentUsers() {
      return this.users.slice(0, 8);
    },
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    async loadData() {
      this.loading = true;
      this.error = '';
      try {
        const [usersRes, profilesRes] = await Promise.all([
          axios.get('/api/admin/users'),
          axios.get('/api/admin/profiles'),
        ]);
        this.users = usersRes.data?.data || usersRes.data || [];
        this.profiles = profilesRes.data?.data || profilesRes.data || [];
      } catch (error) {
        this.error = error.response?.data?.message || 'Impossible de charger l’administration.';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.kpi-grid,
.cards {
  display: grid;
  gap: 16px;
}

.kpi-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 16px;
}

.cards {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 16px;
}

.kpi,
.card,
.table-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.kpi {
  padding: 16px 18px;
}

.kpi span {
  display: block;
  color: #64748b;
  font-size: 13px;
  margin-bottom: 6px;
}

.kpi strong {
  font-size: 28px;
}

.card {
  padding: 22px;
  border-top: 4px solid #e11d2e;
}

.card h2,
.table-head h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.card p {
  margin: 0 0 18px;
  color: #64748b;
  line-height: 1.45;
}

.open-btn {
  border: 0;
  background: #e11d2e;
  color: #fff;
  border-radius: 999px;
  padding: 10px 16px;
  font-weight: 600;
  cursor: pointer;
}

.table-card {
  overflow: hidden;
}

.table-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px 0;
}

.link-btn {
  border: 0;
  background: none;
  color: #1a4d3a;
  font-weight: 600;
  cursor: pointer;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

th,
td {
  padding: 11px 18px;
  text-align: left;
  border-bottom: 1px solid #eef2f6;
  font-size: 14px;
}

th {
  color: #64748b;
  font-weight: 600;
}

.state,
.empty {
  color: #64748b;
  padding: 20px 0;
}

.state.error {
  color: #b91c1c;
}

@media (max-width: 900px) {
  .kpi-grid,
  .cards {
    grid-template-columns: 1fr;
  }
}
</style>
