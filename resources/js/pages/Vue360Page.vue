<template>
  <div class="vue360-page" :class="{ 'vue360-page--centered': !hasSearched && !loading && !results.length }">
    <section class="vue360-main">
      <div class="landing-panel">
        <div class="panel-header">
          <div class="hero-badge">Vue client unifiée</div>
          <h1>Client Vue 360°</h1>
          <p class="hero-sub">Synthèse, KYC, banque et crédits en un clic</p>
        </div>

        <div class="panel-body">
          <form class="search-form" @submit.prevent="runSearch">
            <div class="search-input-wrap">
              <span class="search-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="7" />
                  <path d="M20 20l-3.5-3.5" stroke-linecap="round" />
                </svg>
              </span>
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                placeholder="Nom, matricule, n° de compte ou téléphone…"
                autofocus
              />
              <button
                v-if="searchQuery"
                type="button"
                class="clear-btn"
                aria-label="Effacer"
                @click="clearSearch"
              >
                ×
              </button>
            </div>
            <button type="submit" class="search-btn" :disabled="loading">
              <span v-if="loading" class="btn-spinner"></span>
              {{ loading ? 'Recherche…' : 'Rechercher' }}
            </button>
          </form>

          <p v-if="!hasSearched && !loading" class="search-helper">
            La recherche détecte automatiquement le type de saisie
          </p>

          <div v-if="!hasSearched && !loading" class="welcome-tips">
            <div v-for="tip in welcomeTips" :key="tip.title" class="tip-card" :class="`tip-card--${tip.id}`">
              <span class="tip-icon" aria-hidden="true">
                <svg v-if="tip.id === 'speed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else-if="tip.id === 'scope'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
              <div class="tip-content">
                <strong>{{ tip.title }}</strong>
                <span>{{ tip.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <p v-if="error" class="error-banner">
        <span class="error-icon">!</span>
        {{ error }}
      </p>

      <div v-if="loading" class="loading-state">
        <div v-for="n in 3" :key="n" class="skeleton-card">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-lines">
            <div class="skeleton-line wide"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
          </div>
        </div>
      </div>

      <!-- Aucun résultat -->
      <div v-if="hasSearched && !loading && results.length === 0" class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>Aucun client trouvé</h3>
        <p>
          Aucun résultat pour « <strong>{{ lastQuery }}</strong> ».
          Vérifiez l'orthographe ou essayez un matricule / n° de compte.
        </p>
      </div>

      <!-- Résultats -->
      <div v-if="results.length" class="results-section">
        <div class="results-header">
          <div class="results-header-main">
            <h2>Résultats</h2>
            <span class="results-count">{{ results.length }}</span>
          </div>
          <span class="results-query">Recherche « {{ lastQuery }} »</span>
        </div>
        <ul class="results-list">
          <li
            v-for="client in results"
            :key="client.id"
            class="result-card"
            @click="openClient(client.id)"
          >
            <div class="result-avatar" :style="{ background: avatarColor(client.full_name) }">
              {{ initials(client.full_name) }}
            </div>
            <div class="result-body">
              <strong class="result-name">{{ client.full_name }}</strong>
              <p v-if="clientDetailParts(client).length" class="result-meta">
                <template v-for="(part, i) in clientDetailParts(client)" :key="part.key">
                  <span v-if="i > 0" class="meta-dot" aria-hidden="true">·</span>
                  <span class="meta-part" :class="`meta-part--${part.key}`">{{ part.value }}</span>
                </template>
              </p>
              <div class="result-footer">
                <div class="result-tags">
                  <span class="tag" :class="client.status">{{ statusLabel(client.status) }}</span>
                  <span class="tag segment" :title="client.segment">{{ segmentLabel(client.segment) }}</span>
                </div>
                <div class="result-stats">
                  <span>Comptes <strong>{{ client.accounts_count ?? 0 }}</strong></span>
                  <span>Crédits <strong>{{ clientCreditsCount(client) }}</strong></span>
                </div>
              </div>
            </div>
            <span class="result-arrow" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<script>
const AVATAR_COLORS = ['#1a4d3a', '#2563eb', '#7c3aed', '#b45309', '#be123c', '#0d9488'];

export default {
  name: 'Vue360Page',
  data() {
    return {
      searchQuery: '',
      lastQuery: '',
      results: [],
      loading: false,
      error: '',
      hasSearched: false,
      welcomeTips: [
        { id: 'speed', title: 'Recherche rapide', desc: 'Résultats en temps réel depuis Flexcube' },
        { id: 'scope', title: 'Périmètre agence', desc: 'Clients filtrés selon votre profil' },
        { id: 'profile', title: 'Fiche complète', desc: 'Synthèse, KYC, banque et crédits' },
      ],
    };
  },
  watch: {
    '$route.query.q'(value) {
      if (value && value !== this.searchQuery) {
        this.searchQuery = value;
        this.runSearch();
      }
    },
  },
  mounted() {
    const q = this.$route.query.q;
    if (q) {
      this.searchQuery = String(q);
      this.runSearch();
    }
  },
  methods: {
    async runSearch() {
      const query = this.searchQuery.trim();
      if (!query) {
        this.error = 'Saisissez un nom, matricule, numéro de compte ou téléphone.';
        return;
      }

      this.loading = true;
      this.error = '';
      this.hasSearched = true;
      this.lastQuery = query;

      if (this.$route.query.q !== query) {
        this.$router.replace({ path: '/vue360/recherche', query: { q: query } });
      }

      try {
        const response = await window.axios.get('/api/v1/clients', {
          params: { query },
        });
        this.results = response.data?.data || [];
      } catch (err) {
        this.results = [];
        this.error = err.response?.data?.message || 'Erreur lors de la recherche client.';
      } finally {
        this.loading = false;
      }
    },
    clearSearch() {
      this.searchQuery = '';
      this.results = [];
      this.hasSearched = false;
      this.error = '';
      if (this.$route.query.q) {
        this.$router.replace({ path: '/vue360/recherche' });
      }
    },
    openClient(id) {
      this.$router.push(`/vue360/clients/${encodeURIComponent(id)}`);
    },
    initials(name) {
      return (name || '?')
        .split(' ')
        .slice(0, 2)
        .map((p) => p[0])
        .join('')
        .toUpperCase();
    },
    avatarColor(name) {
      const code = (name || '').split('').reduce((a, c) => a + c.charCodeAt(0), 0);
      return AVATAR_COLORS[code % AVATAR_COLORS.length];
    },
    statusLabel(status) {
      if (status === 'active') return 'Actif';
      if (status === 'at_risk') return 'À risque';
      if (status === 'inactive') return 'Inactif';
      return status || '—';
    },
    clientDetailParts(client) {
      const parts = [];
      if (client.matricule) {
        parts.push({ key: 'matricule', label: '', value: client.matricule });
      }
      if (client.phone) {
        parts.push({ key: 'phone', label: '', value: this.formatPhone(client.phone) });
      }
      const agency = client.agency || client.branch_code;
      if (agency) {
        parts.push({ key: 'agency', label: '', value: agency });
      }
      return parts;
    },
    formatPhone(value) {
      const digits = String(value || '').replace(/\D/g, '');
      if (digits.length === 9) {
        return `${digits.slice(0, 2)} ${digits.slice(2, 5)} ${digits.slice(5)}`;
      }
      return value || '';
    },
    segmentLabel(segment) {
      const label = segment || 'Standard';
      return label.length > 22 ? `${label.slice(0, 20)}…` : label;
    },
    clientCreditsCount(client) {
      return client.credits_count ?? client.active_credits_count ?? 0;
    },
  },
};
</script>

<style scoped>
.vue360-page {
  min-height: 100%;
  background: transparent;
}

.vue360-page--centered {
  display: flex;
  flex-direction: column;
  justify-content: stretch;
  min-height: calc(100vh - 100px);
}

.vue360-main {
  max-width: none;
  width: 100%;
  margin: 0;
  padding: 20px 28px 32px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.vue360-page--centered .vue360-main {
  padding-top: 20px;
  padding-bottom: 28px;
}

.landing-panel {
  background: #fff;
  border-radius: 24px;
  overflow: hidden;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 20px 56px rgba(26, 77, 58, 0.14);
  border: 1px solid rgba(26, 77, 58, 0.08);
  margin-bottom: 24px;
  width: 100%;
}

.vue360-page--centered .landing-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.vue360-page--centered .panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-header {
  text-align: center;
  padding: 40px 48px 36px;
  background: linear-gradient(135deg, #1a4d3a 0%, #2d6a4f 50%, #40916c 100%);
  position: relative;
  flex-shrink: 0;
}

.panel-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 15% 90%, rgba(255, 255, 255, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 85% 10%, rgba(255, 255, 255, 0.05) 0%, transparent 40%);
  pointer-events: none;
}

.panel-header > * {
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-block;
  padding: 7px 16px;
  margin-bottom: 14px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #d8f3dc;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
}

.panel-header h1 {
  margin: 0 0 12px;
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
}

.hero-sub {
  margin: 0;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
}

.panel-body {
  padding: 36px 48px 40px;
  max-width: 780px;
  margin: 0 auto;
  width: 100%;
}

/* ── Recherche ── */
.search-form {
  display: flex;
  gap: 14px;
  align-items: stretch;
}

.search-input-wrap {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 20px;
  width: 22px;
  height: 22px;
  color: #9ca3af;
  pointer-events: none;
}

.search-icon svg {
  width: 100%;
  height: 100%;
}

.search-input {
  width: 100%;
  padding: 20px 52px 20px 56px;
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  font-size: 1.05rem;
  color: #111827;
  background: #fff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #1a4d3a;
  box-shadow: 0 0 0 4px rgba(26, 77, 58, 0.1);
}

.search-input::placeholder {
  color: #9ca3af;
}

.clear-btn {
  position: absolute;
  right: 16px;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 50%;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 1.15rem;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.clear-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.search-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 36px;
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: #fff;
  border: none;
  border-radius: 16px;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  min-width: 150px;
  box-shadow: 0 4px 16px rgba(220, 38, 38, 0.28);
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.search-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 22px rgba(220, 38, 38, 0.35);
}

.search-btn:disabled {
  opacity: 0.75;
  cursor: wait;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search-helper {
  margin: 14px 0 0;
  text-align: center;
  font-size: 0.88rem;
  color: #9ca3af;
}

/* ── Erreur ── */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  color: #b91c1c;
  font-size: 0.9rem;
}

.error-icon {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #dc2626;
  color: #fff;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}

/* ── Conseils intégrés ── */
.welcome-tips {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 32px;
}

.tip-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  text-align: center;
  padding: 18px 14px;
  background: #f9fafb;
  border-radius: 12px;
  border: none;
  transition: background 0.15s;
}

.tip-card:hover {
  background: #f3f4f6;
}

.tip-card--speed .tip-icon {
  background: #dcfce7;
  color: #166534;
}

.tip-card--scope .tip-icon {
  background: #dbeafe;
  color: #1d4ed8;
}

.tip-card--profile .tip-icon {
  background: #ede9fe;
  color: #6d28d9;
}

.tip-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.tip-icon svg {
  width: 18px;
  height: 18px;
}

.tip-content strong {
  display: block;
  font-size: 0.88rem;
  color: #111827;
  margin-bottom: 3px;
}

.tip-content span {
  font-size: 0.78rem;
  color: #6b7280;
  line-height: 1.4;
}

/* ── Skeleton ── */
.loading-state {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
  flex-shrink: 0;
}

.skeleton-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 4px;
}

.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

.skeleton-line.wide { width: 70%; }
.skeleton-line.short { width: 40%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Vide ── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  background: #fff;
  border-radius: 16px;
  border: 1px dashed #d1d5db;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  opacity: 0.6;
}

.empty-state h3 {
  margin: 0 0 8px;
  color: #374151;
  font-size: 1.1rem;
}

.empty-state p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* ── Résultats ── */
.results-section {
  animation: fadeIn 0.3s ease;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px 24px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

.results-header-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.results-header h2 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #1a4d3a;
}

.results-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  border-radius: 999px;
  background: #f0fdf4;
  color: #1a4d3a;
  font-size: 0.82rem;
  font-weight: 700;
}

.results-query {
  font-size: 0.84rem;
  color: #9ca3af;
}

.results-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-card {
  display: grid;
  grid-template-columns: 48px 1fr 24px;
  align-items: start;
  gap: 16px;
  width: 100%;
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  border: 1px solid #eef0f2;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.result-card:hover {
  border-color: #b7dfc9;
  box-shadow: 0 2px 12px rgba(26, 77, 58, 0.07);
}

.result-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  color: #fff;
  letter-spacing: 0.02em;
}

.result-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.result-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.35;
  letter-spacing: -0.01em;
}

.result-meta {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-dot {
  margin: 0 8px;
  color: #d1d5db;
}

.meta-part--matricule,
.meta-part--phone {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
  color: #4b5563;
}

.meta-part--agency {
  color: #6b7280;
}

.result-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.result-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.result-stats {
  display: flex;
  gap: 18px;
  font-size: 0.78rem;
  color: #9ca3af;
  margin-left: auto;
  white-space: nowrap;
}

.result-stats strong {
  color: #1a4d3a;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-left: 3px;
}

.tag {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
}

.tag.segment {
  background: #eff6ff;
  color: #1d4ed8;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag.active {
  background: #dcfce7;
  color: #166534;
}

.tag.at_risk {
  background: #fef3c7;
  color: #92400e;
}

.tag.inactive {
  background: #f3f4f6;
  color: #6b7280;
}

.result-arrow {
  align-self: center;
  color: #d1d5db;
  transition: color 0.15s, transform 0.15s;
}

.result-arrow svg {
  width: 18px;
  height: 18px;
}

.result-card:hover .result-arrow {
  color: #1a4d3a;
  transform: translateX(2px);
}

@media (max-width: 720px) {
  .welcome-tips {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .vue360-main {
    padding: 20px 14px 48px;
  }

  .panel-header {
    padding: 24px 20px 22px;
  }

  .panel-body {
    padding: 20px 16px 20px;
  }

  .search-form {
    flex-direction: column;
  }

  .search-btn {
    width: 100%;
    padding: 14px;
  }

  .result-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .result-stats {
    margin-left: 0;
  }

  .result-meta {
    white-space: normal;
  }

  .result-card {
    grid-template-columns: 44px 1fr;
    padding: 14px;
    gap: 12px;
  }

  .result-arrow {
    display: none;
  }
}
</style>
