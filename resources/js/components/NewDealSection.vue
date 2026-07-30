<template>
  <div class="new-deal-section">
    <div class="section-header">
      <div class="section-title-block">
        <h2 class="section-title">New Deal</h2>
        <p class="section-sub">
          New Deal — hors clients NAFA / déjà en prêt
          <span v-if="count !== null" class="meta">— {{ formatCount(count) }} dossier(s)</span>
          <span v-if="refreshedAt" class="meta"> · maj {{ refreshedAt }}</span>
        </p>
      </div>
      <div class="actions">
        <input
          v-model.trim="search"
          type="search"
          class="search-input"
          placeholder="Rechercher agence, client, prêt…"
        />
        <button type="button" class="btn" :disabled="loading" @click="loadData(true)">
          Actualiser
        </button>
        <button type="button" class="btn btn-primary" :disabled="refreshing || loading" @click="rebuildTable">
          {{ refreshing ? 'Reconstruction…' : 'Reconstruire la table' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="state-msg">Chargement des données New Deal…</div>
    <div v-else-if="errorMessage" class="state-msg error">{{ errorMessage }}</div>
    <div v-else-if="warning" class="state-msg warn">{{ warning }}</div>

    <div v-if="!loading && !errorMessage" class="summary">
      <div class="summary-card">
        <span class="label">Dossiers</span>
        <strong>{{ formatCount(filteredRows.length) }}</strong>
      </div>
      <div class="summary-card">
        <span class="label">Montant total</span>
        <strong>{{ formatMoney(filteredTotal) }}</strong>
      </div>
    </div>

    <div v-if="!loading && !errorMessage && !filteredRows.length" class="state-msg">
      Aucun New Deal à afficher.
    </div>

    <div v-else-if="!loading && !errorMessage" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Agence</th>
            <th>N° prêt</th>
            <th>Client</th>
            <th>Matricule</th>
            <th class="num">Montant</th>
            <th>Date</th>
            <th>Compte</th>
            <th>CAF</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in filteredRows" :key="row.no_pret + '-' + idx">
            <td>
              <span class="agency-code">{{ row.code_agence }}</span>
              {{ row.nom_agence }}
            </td>
            <td>{{ row.no_pret }}</td>
            <td>{{ row.nom_client }}</td>
            <td>{{ row.matricule_client }}</td>
            <td class="num">{{ formatMoney(row.amount_financed) }}</td>
            <td>{{ formatDate(row.trn_dt) }}</td>
            <td>{{ row.compte || '—' }}</td>
            <td>{{ row.field_char_2 || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NewDealSection',
  data() {
    return {
      loading: false,
      refreshing: false,
      errorMessage: '',
      warning: '',
      rows: [],
      count: null,
      totalAmount: 0,
      refreshedAt: '',
      search: '',
    };
  },
  computed: {
    filteredRows() {
      const q = (this.search || '').toLowerCase();
      if (!q) return this.rows;
      return this.rows.filter((r) => {
        const hay = [
          r.code_agence,
          r.nom_agence,
          r.no_pret,
          r.nom_client,
          r.matricule_client,
          r.compte,
          r.field_char_2,
        ]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return hay.includes(q);
      });
    },
    filteredTotal() {
      return this.filteredRows.reduce((sum, r) => {
        const v = Number(r.amount_financed);
        return sum + (Number.isFinite(v) ? v : 0);
      }, 0);
    },
  },
  mounted() {
    this.loadData(false);
  },
  methods: {
    formatCount(n) {
      if (n === null || n === undefined) return '—';
      return new Intl.NumberFormat('fr-FR').format(n);
    },
    formatMoney(v) {
      if (v === null || v === undefined || v === '') return '—';
      const n = Number(v);
      if (!Number.isFinite(n)) return '—';
      return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'XOF',
        maximumFractionDigits: 0,
      }).format(n);
    },
    formatDate(v) {
      if (!v) return '—';
      const s = String(v);
      if (/^\d{4}-\d{2}-\d{2}/.test(s)) {
        const [y, m, d] = s.slice(0, 10).split('-');
        return `${d}/${m}/${y}`;
      }
      return s;
    },
    async loadData(forceRefresh) {
      this.loading = true;
      this.errorMessage = '';
      this.warning = '';
      try {
        const params = forceRefresh ? { refresh: 1 } : {};
        const response = await window.axios.get('/api/oracle/data/new-deal', { params });
        const payload = response.data || {};
        this.rows = Array.isArray(payload.data) ? payload.data : [];
        this.count = payload.count ?? this.rows.length;
        this.totalAmount = payload.total_amount ?? 0;
        this.warning = payload.warning || '';
        this.refreshedAt = payload.refreshed_at
          ? String(payload.refreshed_at).replace('T', ' ').replace('Z', '')
          : '';
      } catch (err) {
        const msg =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          'Impossible de charger le New Deal';
        this.errorMessage = msg;
        this.rows = [];
        this.count = 0;
      } finally {
        this.loading = false;
      }
    },
    async rebuildTable() {
      this.refreshing = true;
      this.errorMessage = '';
      try {
        await window.axios.post('/api/oracle/backup/new-deal');
        await this.loadData(true);
      } catch (err) {
        const msg =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          'Échec de la reconstruction';
        this.errorMessage = msg;
      } finally {
        this.refreshing = false;
      }
    },
  },
};
</script>

<style scoped>
.new-deal-section {
  padding: 1rem 1.25rem 2rem;
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.section-title {
  margin: 0;
  font-size: 1.35rem;
  color: #111827;
}

.section-sub {
  margin: 0.25rem 0 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.meta {
  color: #374151;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.search-input {
  min-width: 220px;
  padding: 0.45rem 0.7rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.btn {
  padding: 0.45rem 0.85rem;
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #0f766e;
  border-color: #0f766e;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #0d9488;
}

.summary {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.summary-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  min-width: 140px;
}

.summary-card .label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.2rem;
}

.summary-card strong {
  font-size: 1.05rem;
  color: #111827;
}

.state-msg {
  padding: 1rem;
  color: #4b5563;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.state-msg.error {
  color: #b91c1c;
  background: #fef2f2;
}

.state-msg.warn {
  color: #92400e;
  background: #fffbeb;
}

.table-wrap {
  overflow: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

th,
td {
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}

th {
  background: #f3f4f6;
  font-weight: 600;
  color: #374151;
  position: sticky;
  top: 0;
}

td.num,
th.num {
  text-align: right;
}

tbody tr:hover {
  background: #f9fafb;
}

.agency-code {
  display: inline-block;
  margin-right: 0.35rem;
  padding: 0.1rem 0.35rem;
  background: #ecfdf5;
  color: #065f46;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

@media (max-width: 768px) {
  .search-input {
    min-width: 100%;
  }
}
</style>
