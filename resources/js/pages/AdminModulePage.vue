<template>
  <div class="admin-home">
    <header class="page-head">
      <h1>Vue d’ensemble</h1>
      <p>Comptes, droits et organisation de la plateforme.</p>
    </header>

    <div v-if="loading" class="state">Chargement de l’administration…</div>
    <div v-else-if="error" class="state error">{{ error }}</div>

    <template v-else>
      <section class="kpi-grid">
        <article class="kpi">
          <span class="kpi-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="3"/><path d="M22 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
          </span>
          <div>
            <strong>{{ users.length }}</strong>
            <span>Utilisateurs</span>
          </div>
        </article>
        <article class="kpi">
          <span class="kpi-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.2-2.8 7.4-7 9-4.2-1.6-7-4.8-7-9V6l7-3z"/></svg>
          </span>
          <div>
            <strong>{{ profiles.length }}</strong>
            <span>Profils <em>{{ activeProfiles }} actifs</em></span>
          </div>
        </article>
        <article class="kpi">
          <span class="kpi-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M3 10l9-7 9 7v10a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1V10z"/></svg>
          </span>
          <div>
            <strong>{{ territories.length }}</strong>
            <span>Territoires</span>
          </div>
        </article>
        <article class="kpi">
          <span class="kpi-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 20V9M10 20V4M16 20v-7M22 20H2"/></svg>
          </span>
          <div>
            <strong>{{ agencies.length }}</strong>
            <span>Agences</span>
          </div>
        </article>
      </section>

      <section class="cards">
        <button type="button" class="card" @click="$router.push('/admin/organisation')">
          <span class="card-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h10" stroke-linecap="round"/></svg>
          </span>
          <span class="card-copy">
            <strong>Données</strong>
            <span>Territoires, agences, utilisateurs et profils</span>
          </span>
          <span class="card-go" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </span>
        </button>
        <button type="button" class="card" @click="$router.push('/admin/environnements')">
          <span class="card-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.2 2.4 3.3 5.1 3.3 8S14.2 17.6 12 20c-2.2-2.4-3.3-5.1-3.3-8S9.8 6.4 12 4z"/></svg>
          </span>
          <span class="card-copy">
            <strong>Environnements</strong>
            <span>Pays et agences rattachées</span>
          </span>
          <span class="card-go" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </span>
        </button>
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
      territories: [],
      agencies: [],
    };
  },
  computed: {
    activeProfiles() {
      return this.profiles.filter((profile) => profile.is_active).length;
    },
  },
  async mounted() {
    await this.loadData();
  },
  methods: {
    asList(payload) {
      if (Array.isArray(payload)) return payload;
      if (Array.isArray(payload?.data)) return payload.data;
      return [];
    },
    async loadData() {
      this.loading = true;
      this.error = '';
      try {
        const [usersRes, profilesRes, territoriesRes, agenciesRes] = await Promise.all([
          axios.get('/api/admin/users'),
          axios.get('/api/admin/profiles'),
          axios.get('/api/territories'),
          axios.get('/api/agencies'),
        ]);
        this.users = this.asList(usersRes.data);
        this.profiles = this.asList(profilesRes.data);
        this.territories = this.asList(territoriesRes.data);
        this.agencies = this.asList(agenciesRes.data);
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
.admin-home {
  max-width: 980px;
}

.page-head {
  margin-bottom: 20px;
}

.page-head h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: #14261e;
}

.page-head p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 14px;
}

.kpi-grid,
.cards {
  display: grid;
  gap: 12px;
}

.kpi-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 12px;
}

.cards {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kpi,
.card {
  background: #fff;
  border: 1px solid #e4ebe7;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(20, 38, 30, 0.04);
}

.kpi {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 88px;
  padding: 16px 18px;
}

.kpi-mark,
.card-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 12px;
  background: #e8f3ed;
  color: #1a4d3a;
}

.kpi-mark {
  width: 42px;
  height: 42px;
}

.kpi-mark svg,
.card-mark svg,
.card-go svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.kpi strong {
  display: block;
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.03em;
  line-height: 1;
  color: #14261e;
}

.kpi > div > span {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
}

.kpi em {
  margin-left: 6px;
  font-style: normal;
  font-weight: 600;
  font-size: 12px;
  color: #1a4d3a;
}

.card {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-height: 84px;
  padding: 16px 16px 16px 18px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}

.card:hover {
  border-color: #b7d0c4;
  box-shadow: 0 8px 18px rgba(26, 77, 58, 0.08);
}

.card-mark {
  width: 44px;
  height: 44px;
}

.card-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.card-copy strong {
  font-size: 16px;
  color: #14261e;
}

.card-copy span {
  color: #64748b;
  font-size: 13px;
  line-height: 1.35;
}

.card-go {
  display: inline-flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f3f6f4;
  color: #1a4d3a;
  flex-shrink: 0;
}

.card:hover .card-go {
  background: #1a4d3a;
  color: #fff;
}

.state {
  color: #64748b;
  padding: 12px 0;
}

.state.error {
  color: #b91c1c;
}

@media (max-width: 900px) {
  .kpi-grid,
  .cards {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-grid,
  .cards {
    grid-template-columns: 1fr;
  }
}
</style>
