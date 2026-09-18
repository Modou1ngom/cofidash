<template>
  <div class="client-section">
    <div class="section-header">
      <h2 class="section-title">Enrôlements PI — {{ dateLabel }}</h2>
      <div class="period-selector">
        <input
          v-model="selectedDay"
          type="date"
          class="date-select"
          :min="minDay"
          :max="maxDay"
        />
        <input
          v-model="search"
          type="search"
          class="date-select search-input"
          placeholder="Rechercher une agence…"
        />
      </div>
    </div>

    <div v-if="piState.loading && !rows.length" class="state-msg">Chargement des enrôlements…</div>

    <div v-else class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Obj journalier</th>
              <th>Enrôl. du jour</th>
              <th>Cumul mois</th>
              <th>Obj mensuel</th>
              <th>% obj mensuel</th>
            </tr>
          </thead>
          <tbody>
            <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" type="button" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expanded.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>{{ formatNumber(territoireTotals.obj_daily) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotals.enrolled_day) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotals.cumul_month) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotals.obj_month) }}</strong></td>
              <td :class="achievementClass(territoireTotals.rate_month)">
                <strong>{{ formatPercent(territoireTotals.rate_month) }}</strong>
              </td>
            </tr>

            <template v-if="expanded.TERRITOIRE">
              <template v-for="zone in zones" :key="zone.name">
                <tr class="level-2-row" @click="toggleExpand(zone.name)">
                  <td class="level-2">
                    <button class="expand-btn" type="button" @click.stop="toggleExpand(zone.name)">
                      {{ expanded[zone.name] ? '−' : '+' }}
                    </button>
                    {{ zone.name }}
                  </td>
                  <td><strong>{{ formatNumber(zone.totals.obj_daily) }}</strong></td>
                  <td><strong>{{ formatNumber(zone.totals.enrolled_day) }}</strong></td>
                  <td><strong>{{ formatNumber(zone.totals.cumul_month) }}</strong></td>
                  <td><strong>{{ formatNumber(zone.totals.obj_month) }}</strong></td>
                  <td :class="achievementClass(zone.totals.rate_month)">
                    <strong>{{ formatPercent(zone.totals.rate_month) }}</strong>
                  </td>
                </tr>

                <tr
                  v-for="agency in zone.agencies"
                  v-show="expanded[zone.name]"
                  :key="agency.branch_name"
                  class="level-3-row"
                >
                  <td class="level-3">{{ agency.branch_name }}</td>
                  <td>{{ formatNumber(agency.obj_daily) }}</td>
                  <td>{{ formatNumber(agency.enrolled_day) }}</td>
                  <td>{{ formatNumber(agency.cumul_month) }}</td>
                  <td>{{ formatNumber(agency.obj_month) }}</td>
                  <td :class="achievementClass(agency.rate_month)">
                    {{ formatGrowthRate(agency.rate_month, agency.ahead) }}
                  </td>
                </tr>
              </template>
            </template>

            <tr v-if="grandCompte" class="level-1-row grand-compte-row">
              <td class="level-1">
                <strong>GRAND COMPTE</strong>
              </td>
              <td><strong>{{ formatNumber(grandCompte.obj_daily) }}</strong></td>
              <td><strong>{{ formatNumber(grandCompte.enrolled_day) }}</strong></td>
              <td><strong>{{ formatNumber(grandCompte.cumul_month) }}</strong></td>
              <td><strong>{{ formatNumber(grandCompte.obj_month) }}</strong></td>
              <td :class="achievementClass(grandCompte.rate_month)">
                <strong>{{ formatPercent(grandCompte.rate_month) }}</strong>
              </td>
            </tr>

            <tr v-if="!rows.length">
              <td colspan="6" class="empty">Aucune agence pour cette période.</td>
            </tr>

            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ formatNumber(totals.obj_daily) }}</strong></td>
              <td><strong>{{ formatNumber(totals.enrolled_day) }}</strong></td>
              <td><strong>{{ formatNumber(totals.cumul_month) }}</strong></td>
              <td><strong>{{ formatNumber(totals.obj_month) }}</strong></td>
              <td :class="achievementClass(totals.rate_month)">
                <strong>{{ formatPercent(totals.rate_month) }}</strong>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
const ZONE_ORDER = ['DAKAR VILLE', 'DAKAR BANLIEUE', 'PROVINCE CENTRE', 'PROVINCE NORD'];

export default {
  name: 'PiEnrollementsPage',
  inject: ['piState'],
  data() {
    return {
      search: '',
      selectedDay: '',
      expanded: { TERRITOIRE: true },
    };
  },
  computed: {
    fiche() {
      return this.piState.data?.fiche || { rows: [], totals: {}, as_of: '', label: '' };
    },
    clients() {
      return this.piState.data?.clients || [];
    },
    period() {
      return this.piState.data?.period || {};
    },
    minDay() {
      return this.period.date_debut || '';
    },
    maxDay() {
      return this.period.date_fin || '';
    },
    dateLabel() {
      if (!this.selectedDay) return this.fiche.label || '—';
      const [year, month, day] = this.selectedDay.split('-');
      return `${day}/${month}/${year}`;
    },
    rows() {
      const day = this.selectedDay || this.fiche.as_of;
      const query = this.search.trim().toLowerCase();
      return (this.fiche.rows || []).map((row) => {
        const codes = row.branch_codes || [row.branch_code, row.branch_name];
        const enrolledDay = this.clients.filter((client) => (
          (codes.includes(client.branch_code) || codes.includes(client.branch_name))
          && client.statut_pi === 'Enrôlé'
          && (client.dt_cre_pi || client.ac_open_date || client.date_creation) === day
        )).length;
        const cumul = Number(row.cumul_month) || 0;
        const objMonth = Number(row.obj_month) || 0;
        return {
          ...row,
          enrolled_day: enrolledDay,
          rate_month: objMonth ? Math.round((cumul / objMonth) * 1000) / 10 : 0,
          ahead: objMonth ? cumul >= objMonth : false,
        };
      }).filter((row) => {
        if (this.isIgnored(row)) return false;
        if (!query) return true;
        return `${row.branch_name} ${row.zone}`.toLowerCase().includes(query);
      });
    },
    territoryRows() {
      return this.rows.filter((row) => !this.isGrandCompte(row));
    },
    grandCompte() {
      return this.rows.find((row) => this.isGrandCompte(row)) || null;
    },
    zones() {
      const grouped = {};
      this.territoryRows.forEach((row) => {
        const name = row.zone;
        if (!grouped[name]) {
          grouped[name] = [];
        }
        grouped[name].push(row);
      });
      const names = ZONE_ORDER.filter((name) => grouped[name]);
      return names.map((name) => {
        const agencies = grouped[name];
        return { name, agencies, totals: this.sumRows(agencies) };
      });
    },
    territoireTotals() {
      return this.sumRows(this.territoryRows);
    },
    totals() {
      return this.sumRows(this.rows);
    },
  },
  watch: {
    'fiche.as_of': {
      immediate: true,
      handler(value) {
        if (value) {
          this.selectedDay = value;
        }
      },
    },
    zones: {
      immediate: true,
      handler(zones) {
        zones.forEach((zone) => {
          if (this.expanded[zone.name] === undefined) {
            this.expanded[zone.name] = true;
          }
        });
      },
    },
  },
  methods: {
    isGrandCompte(row) {
      return /grand\s*compte/i.test(row.branch_name || '') || row.zone === 'GRAND COMPTE';
    },
    isIgnored(row) {
      const name = String(row.branch_name || '').toUpperCase();
      if (/DIGITALE|SIEGE|SIÈGE|TOUBA\s*OCAS|\bOCAS\b|\bFINA\b/.test(name)) {
        return true;
      }
      if (this.isGrandCompte(row)) return false;
      const zone = String(row.zone || '').trim();
      return !ZONE_ORDER.includes(zone);
    },
    sumRows(rows) {
      const objDaily = rows.reduce((sum, row) => sum + (Number(row.obj_daily) || 0), 0);
      const enrolledDay = rows.reduce((sum, row) => sum + (Number(row.enrolled_day) || 0), 0);
      const cumul = rows.reduce((sum, row) => sum + (Number(row.cumul_month) || 0), 0);
      const objMonth = rows.reduce((sum, row) => sum + (Number(row.obj_month) || 0), 0);
      return {
        obj_daily: objDaily,
        enrolled_day: enrolledDay,
        cumul_month: cumul,
        obj_month: objMonth,
        rate_month: objMonth ? Math.round((cumul / objMonth) * 1000) / 10 : 0,
      };
    },
    toggleExpand(key) {
      this.expanded[key] = !this.expanded[key];
    },
    formatNumber(value) {
      return new Intl.NumberFormat('fr-FR').format(Number(value) || 0);
    },
    formatPercent(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      return `${Number(value).toFixed(1)}%`;
    },
    formatGrowthRate(value, ahead) {
      const rate = Number(value) || 0;
      const formatted = `${Math.abs(rate).toFixed(1)}%`;
      return ahead ? `▲ ${formatted}` : `▼ ${formatted}`;
    },
    achievementClass(value) {
      const rate = Number(value) || 0;
      if (rate >= 100) return 'achievement-high';
      if (rate >= 70) return 'achievement-medium';
      return 'achievement-low';
    },
  },
};
</script>

<style scoped>
.client-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.period-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.date-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  color: #333;
}

.search-input {
  min-width: 240px;
}

.zone-agencies-section {
  margin-top: 10px;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agencies-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.agencies-table thead {
  background: #dc2626;
  color: white;
}

.agencies-table th {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  border-right: 1px solid #444;
  white-space: nowrap;
}

.agencies-table th:first-child {
  text-align: left;
  padding-left: 16px;
}

.agencies-table td {
  padding: 10px 8px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #eee;
  border-right: 1px solid #f0f0f0;
}

.agencies-table td:first-child {
  text-align: left;
  padding-left: 16px;
}

.level-1-row {
  background: #2a2a2a;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.grand-compte-row {
  cursor: default;
  border-top: 2px solid #111;
}

.level-1 {
  font-size: 16px;
  padding-left: 16px !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-2-row {
  background: #4a4a4a;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.level-2 {
  font-size: 14px;
  padding-left: 32px !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-3-row {
  background: white;
}

.level-3 {
  padding-left: 48px !important;
  color: #333;
}

.level-3-row:hover {
  background: #f5f5f5;
}

.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.total-row {
  background: #f5f5f5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
}

.achievement-high {
  color: #10b981;
  font-weight: 500;
}

.achievement-medium {
  color: #f59e0b;
  font-weight: 500;
}

.achievement-low {
  color: #ef4444;
  font-weight: 500;
}

.level-1-row .achievement-high,
.level-2-row .achievement-high {
  color: #6ee7b7;
}

.level-1-row .achievement-medium,
.level-2-row .achievement-medium {
  color: #fcd34d;
}

.level-1-row .achievement-low,
.level-2-row .achievement-low {
  color: #fca5a5;
}

.state-msg,
.empty {
  text-align: center;
  color: #64748b;
  padding: 24px 0;
}

@media (max-width: 900px) {
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
