<template>
  <div class="caf-objectives-section">
    <header class="section-header">
      <div>
        <h1 class="section-title">Mes objectifs</h1>
        <p class="section-subtitle">Objectifs fixés par votre Chef d'Agence</p>
      </div>
      <div class="filters">
        <label class="filter-field">
          <span>Mois</span>
          <select v-model.number="selectedMonth" @change="loadObjectives">
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </label>
        <label class="filter-field">
          <span>Année</span>
          <select v-model.number="selectedYear" @change="loadObjectives">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </label>
        <button type="button" class="refresh-btn" :disabled="loading" @click="loadObjectives">
          {{ loading ? 'Chargement…' : 'Actualiser' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="loading && !objectives.length" class="loading-state">Chargement des objectifs…</div>

    <div v-else-if="!objectives.length" class="empty-state">
      Aucun objectif fixé pour {{ periodLabel }}.
    </div>

    <div v-else class="objectives-panel">
      <div class="objectives-table-wrap">
        <table class="objectives-table">
          <thead>
            <tr>
              <th>Type</th>
              <th class="num">Nombres</th>
              <th class="num">Volume / Valeur</th>
              <th>Période</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="obj in objectives" :key="obj.id || obj.type">
              <td><strong>{{ objectiveTypeLabel(obj.type) }}</strong></td>
              <td class="num">
                <template v-if="obj.type === 'PRODUCTION' && obj.value_nombres != null">
                  {{ formatCount(obj.value_nombres) }}
                </template>
                <template v-else-if="isCountObjectiveType(obj.type)">
                  {{ formatCount(obj.value) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="num">
                <template v-if="obj.type === 'PRODUCTION' && obj.value_volume != null">
                  {{ formatMoney(obj.value_volume) }}
                </template>
                <template v-else-if="isMoneyObjectiveType(obj.type)">
                  {{ formatMoney(obj.value) }}
                </template>
                <template v-else-if="!isCountObjectiveType(obj.type)">
                  {{ formatCount(obj.value) }}
                </template>
                <template v-else>—</template>
              </td>
              <td>{{ objectivePeriodLabel(obj) }}</td>
              <td>
                <span class="obj-status" :class="`obj-status--${obj.status}`">
                  {{ objectiveStatusLabel(obj.status) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
const MONTH_LABELS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
];

export default {
  name: 'CafObjectivesSection',
  data() {
    const now = new Date();
    return {
      loading: false,
      error: '',
      objectives: [],
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
    };
  },
  computed: {
    monthOptions() {
      return MONTH_LABELS.map((label, index) => ({
        value: index + 1,
        label,
      }));
    },
    yearOptions() {
      const current = new Date().getFullYear();
      return [current - 2, current - 1, current, current + 1];
    },
    periodLabel() {
      const month = MONTH_LABELS[(this.selectedMonth || 1) - 1] || '';
      return `${month} ${this.selectedYear}`;
    },
  },
  mounted() {
    this.loadObjectives();
  },
  methods: {
    async loadObjectives() {
      this.loading = true;
      this.error = '';
      try {
        const response = await window.axios.get('/api/objectives/my-caf', {
          params: {
            month: this.selectedMonth,
            year: this.selectedYear,
          },
        });
        this.objectives = Array.isArray(response.data?.data) ? response.data.data : [];
      } catch (err) {
        this.error = err.response?.data?.message || 'Impossible de charger vos objectifs.';
        this.objectives = [];
      } finally {
        this.loading = false;
      }
    },
    formatMoney(value) {
      const n = Number(value) || 0;
      return `${n.toLocaleString('fr-FR')} FCFA`;
    },
    formatCount(value) {
      const n = Number(value) || 0;
      return n.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
    },
    objectiveTypeLabel(type) {
      const map = {
        CLIENT: 'Client',
        PRODUCTION: 'Production',
        NEW_DEAL: 'New Deal',
        ENCOURS_CREDIT: 'Encours crédit',
        COLLECT: 'Collecte',
        DEPOT_GARANTIE: 'Dépôt de garantie',
        EPARGNE_SIMPLE: 'Épargne simple',
        EPARGNE_PROJET: 'Épargne projet',
        VOLUME_DAT: 'Volume DAT',
      };
      return map[type] || type;
    },
    isCountObjectiveType(type) {
      return ['CLIENT', 'NEW_DEAL'].includes(type);
    },
    isMoneyObjectiveType(type) {
      return ['COLLECT', 'DEPOT_GARANTIE', 'EPARGNE_SIMPLE', 'EPARGNE_PROJET', 'VOLUME_DAT', 'ENCOURS_CREDIT'].includes(type);
    },
    objectivePeriodLabel(obj) {
      if (!obj) return '—';
      if (obj.period === 'month' && obj.month) {
        const label = MONTH_LABELS[(obj.month || 1) - 1] || '';
        return `${label} ${obj.year}`;
      }
      if (obj.period === 'quarter' && obj.quarter) {
        return `T${obj.quarter} ${obj.year}`;
      }
      if (obj.period === 'year') {
        return `Année ${obj.year}`;
      }
      return String(obj.year || '—');
    },
    objectiveStatusLabel(status) {
      const map = {
        validated: 'Validé',
        pending_validation: 'En attente',
        draft: 'Brouillon',
        rejected: 'Rejeté',
      };
      return map[status] || status || '—';
    },
  },
};
</script>

<style scoped>
.caf-objectives-section {
  padding: 1.5rem 1.75rem 2.5rem;
  min-height: 100%;
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.section-title {
  margin: 0;
  font-size: 1.5rem;
  color: #0f172a;
  font-weight: 650;
}

.section-subtitle {
  margin: 0.35rem 0 0;
  font-size: 0.9rem;
  color: #64748b;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: flex-end;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.filter-field select {
  min-width: 8rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.45rem;
  background: #fff;
  color: #0f172a;
  font-size: 0.88rem;
}

.refresh-btn {
  padding: 0.5rem 0.9rem;
  border: 1px solid #1a4d3a;
  border-radius: 0.45rem;
  background: #1a4d3a;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.65;
  cursor: wait;
}

.error-banner {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  background: #fef2f2;
  color: #b91c1c;
  margin-bottom: 1rem;
}

.loading-state,
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #64748b;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
}

.objectives-panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 0.5rem 0.25rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.objectives-table-wrap {
  overflow-x: auto;
}

.objectives-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.objectives-table th,
.objectives-table td {
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  vertical-align: middle;
}

.objectives-table th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #64748b;
  font-weight: 600;
  background: #f8fafc;
}

.objectives-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.objectives-table tbody tr:last-child td {
  border-bottom: none;
}

.obj-status {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.obj-status--validated {
  background: #ecfdf5;
  color: #047857;
}

.obj-status--pending_validation {
  background: #fffbeb;
  color: #b45309;
}

.obj-status--draft {
  background: #f1f5f9;
  color: #475569;
}

.obj-status--rejected {
  background: #fef2f2;
  color: #b91c1c;
}
</style>
