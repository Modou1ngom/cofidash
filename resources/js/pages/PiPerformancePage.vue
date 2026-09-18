<template>
  <div class="perf">
    <header class="page-head">
      <div>
        <p class="eyebrow">Classement quotidien</p>
        <h2>Performance par agence</h2>
        <p class="sub">Enrôlements du jour et taux de réalisation — {{ dateLabel }}</p>
      </div>
      <label class="date-field">
        <span>Date</span>
        <input v-model="selectedDay" type="date" :min="minDay" :max="maxDay" />
      </label>
    </header>

    <div v-if="piState.loading && !rows.length" class="sheet empty">
      Chargement de la performance…
    </div>

    <section v-else class="sheet">
      <div class="metrics">
        <div class="metric metric-top">
          <span>TOP</span>
          <strong>{{ topCount }}</strong>
          <small>agences actives</small>
        </div>
        <div class="metric metric-flop">
          <span>FLOP</span>
          <strong>{{ flopCount }}</strong>
          <small>sans enrôlement</small>
        </div>
        <div class="metric">
          <span>Enrôlés du jour</span>
          <strong>{{ formatNumber(totals.enrolled_day) }}</strong>
          <small>{{ formatPercent(dayRate) }} de l’objectif</small>
        </div>
        <div class="metric">
          <span>Tx réel mois</span>
          <strong>{{ formatPercent(totals.rate_month) }}</strong>
          <small>{{ formatNumber(totals.cumul_month) }} / {{ formatNumber(totals.obj_month) }}</small>
        </div>
      </div>

      <nav class="tabs" aria-label="Zones">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          :class="{ on: selectedZone === tab.id }"
          @click="selectedZone = tab.id"
        >
          {{ tab.label }}
        </button>
      </nav>

      <div v-if="activeBlock" class="table-wrap">
        <table>
          <caption>
            {{ activeBlock.label }}
            <span>{{ activeBlock.topCount }} TOP · {{ activeBlock.flopCount }} FLOP</span>
          </caption>
          <thead>
            <tr>
              <th class="col-rank">Rang</th>
              <th>Agence</th>
              <th v-if="selectedZone === 'ALL'">Zone</th>
              <th class="col-num">Enrol. jour</th>
              <th class="col-vol">Volume</th>
              <th class="col-num">Tx réel</th>
              <th class="col-status">Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(agency, index) in activeBlock.agencies"
              :key="agency.branch_name"
              :class="{ flop: agency.enrolled_day <= 0 }"
            >
              <td class="col-rank">
                <em :class="['rank', index < 3 ? `rank-${index + 1}` : '']">
                  {{ String(index + 1).padStart(2, '0') }}
                </em>
              </td>
              <td class="col-name">{{ formatAgencyName(agency.branch_name) }}</td>
              <td v-if="selectedZone === 'ALL'" class="col-zone">{{ zoneLabel(agency) }}</td>
              <td class="col-num">{{ formatNumber(agency.enrolled_day) }}</td>
              <td class="col-vol">
                <div class="track" aria-hidden="true">
                  <i :style="{ width: barWidth(agency.enrolled_day, globalMaxDay) }" />
                </div>
              </td>
              <td class="col-num" :class="rateClass(agency.rate_month)">
                {{ formatPercent(agency.rate_month) }}
              </td>
              <td class="col-status">
                <span :class="agency.enrolled_day > 0 ? 'st-top' : 'st-flop'">
                  {{ agency.enrolled_day > 0 ? 'TOP' : 'FLOP' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer v-if="activeBlock" class="note">
        <p v-if="activeBlock.best">
          <strong>Meilleure agence</strong>
          {{ formatAgencyName(activeBlock.best.branch_name) }}
          — {{ formatNumber(activeBlock.best.enrolled_day) }} enrôl.
          · {{ formatPercent(activeBlock.best.rate_month) }}
        </p>
        <p>
          <strong>À relancer</strong>
          <template v-if="activeBlock.flops.length">
            {{ activeBlock.flops.map((row) => formatAgencyName(row.branch_name)).join(' · ') }}
          </template>
          <template v-else>aucune agence</template>
        </p>
      </footer>
    </section>
  </div>
</template>

<script>
const ZONE_ORDER = ['DAKAR VILLE', 'DAKAR BANLIEUE', 'PROVINCE CENTRE', 'PROVINCE NORD'];

export default {
  name: 'PiPerformancePage',
  inject: ['piState'],
  data() {
    return {
      selectedDay: '',
      selectedZone: 'ALL',
    };
  },
  computed: {
    fiche() {
      return this.piState.data?.fiche || { rows: [], as_of: '', label: '' };
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
        };
      }).filter((row) => !this.isIgnored(row));
    },
    totals() {
      const enrolledDay = this.rows.reduce((sum, row) => sum + (Number(row.enrolled_day) || 0), 0);
      const objDaily = this.rows.reduce((sum, row) => sum + (Number(row.obj_daily) || 0), 0);
      const cumul = this.rows.reduce((sum, row) => sum + (Number(row.cumul_month) || 0), 0);
      const objMonth = this.rows.reduce((sum, row) => sum + (Number(row.obj_month) || 0), 0);
      return {
        enrolled_day: enrolledDay,
        obj_daily: objDaily,
        cumul_month: cumul,
        obj_month: objMonth,
        rate_month: objMonth ? Math.round((cumul / objMonth) * 1000) / 10 : 0,
      };
    },
    dayRate() {
      return this.totals.obj_daily
        ? Math.round((this.totals.enrolled_day / this.totals.obj_daily) * 1000) / 10
        : 0;
    },
    blocks() {
      const groups = {};
      this.rows.forEach((row) => {
        const name = this.isGrandCompte(row) ? 'GRAND COMPTE' : row.zone;
        if (!groups[name]) groups[name] = [];
        groups[name].push(row);
      });
      const names = [
        ...ZONE_ORDER.filter((name) => groups[name]),
        ...(groups['GRAND COMPTE'] ? ['GRAND COMPTE'] : []),
      ];
      return names.map((name) => this.toBlock(name, groups[name] || []));
    },
    tabs() {
      return [
        { id: 'ALL', label: 'National' },
        ...this.blocks.map((block) => ({
          id: block.name,
          label: this.formatAgencyName(block.name),
        })),
      ];
    },
    activeBlock() {
      if (this.selectedZone === 'ALL') {
        return this.toBlock('National', this.rows);
      }
      return this.blocks.find((block) => block.name === this.selectedZone) || this.blocks[0] || null;
    },
    topCount() {
      return this.rows.filter((row) => Number(row.enrolled_day) > 0).length;
    },
    flopCount() {
      return this.rows.filter((row) => Number(row.enrolled_day) <= 0).length;
    },
    globalMaxDay() {
      return Math.max(...this.rows.map((row) => Number(row.enrolled_day) || 0), 1);
    },
  },
  watch: {
    'fiche.as_of': {
      immediate: true,
      handler(value) {
        if (value) this.selectedDay = value;
      },
    },
  },
  methods: {
    toBlock(name, list) {
      const agencies = [...list].sort(
        (a, b) => (b.enrolled_day - a.enrolled_day) || (b.rate_month - a.rate_month),
      );
      const flops = agencies.filter((row) => Number(row.enrolled_day) <= 0);
      return {
        name,
        label: name === 'National' ? 'Classement national' : this.formatAgencyName(name),
        agencies,
        topCount: agencies.filter((row) => Number(row.enrolled_day) > 0).length,
        flopCount: flops.length,
        best: agencies.find((row) => Number(row.enrolled_day) > 0) || null,
        flops,
      };
    },
    isGrandCompte(row) {
      return /grand\s*compte/i.test(row.branch_name || '') || row.zone === 'GRAND COMPTE';
    },
    isIgnored(row) {
      const name = String(row.branch_name || '').toUpperCase();
      if (/DIGITALE|SIEGE|SIÈGE|TOUBA\s*OCAS|\bOCAS\b|\bFINA\b/.test(name)) {
        return true;
      }
      if (this.isGrandCompte(row)) return false;
      return !ZONE_ORDER.includes(String(row.zone || '').trim());
    },
    zoneLabel(row) {
      if (this.isGrandCompte(row)) return 'Grand compte';
      return this.formatAgencyName(row.zone);
    },
    formatNumber(value) {
      return new Intl.NumberFormat('fr-FR').format(Number(value) || 0);
    },
    formatPercent(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      return `${Number(value).toFixed(1)}%`;
    },
    formatAgencyName(name) {
      return String(name || '')
        .replace(/\b(AGENCE|C-E|C E|CE|PRINCIPALE)\b/gi, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .toLowerCase()
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
    },
    rateClass(value) {
      const rate = Number(value) || 0;
      if (rate >= 100) return 'rate-high';
      if (rate >= 20) return 'rate-mid';
      return 'rate-low';
    },
    barWidth(value, max) {
      const current = Number(value) || 0;
      const limit = Number(max) || 1;
      return `${Math.round((current / limit) * 100)}%`;
    },
  },
};
</script>

<style scoped>
.perf {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #6b7c73;
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-head h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: #12231b;
}

.sub {
  margin: 6px 0 0;
  color: #5b6b63;
  font-size: 14px;
}

.date-field {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px 8px 14px;
  background: #fff;
  border: 1px solid #dce5df;
  border-radius: 999px;
  box-shadow: 0 8px 18px rgba(18, 35, 27, 0.04);
}

.date-field span {
  color: #6b7c73;
  font-size: 12px;
  font-weight: 650;
}

.date-field input {
  border: 0;
  background: transparent;
  color: #12231b;
  font-size: 13px;
  font-weight: 600;
  outline: none;
}

.sheet {
  background: #fff;
  border: 1px solid #dce5df;
  border-radius: 20px;
  box-shadow: 0 16px 36px rgba(18, 35, 27, 0.06);
  overflow: hidden;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: linear-gradient(180deg, #f8fbf9 0%, #fff 100%);
  border-bottom: 1px solid #e8eee9;
}

.metric {
  position: relative;
  padding: 20px 22px 18px;
}

.metric + .metric::before {
  content: '';
  position: absolute;
  left: 0;
  top: 18px;
  bottom: 18px;
  width: 1px;
  background: #e4ece7;
}

.metric span,
.metric small {
  display: block;
  color: #6b7c73;
  font-size: 12px;
}

.metric strong {
  display: block;
  margin: 8px 0 6px;
  font-size: 30px;
  line-height: 1;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
  color: #12231b;
}

.metric-top strong { color: #15803d; }
.metric-flop strong { color: #b91c1c; }

.tabs {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  background: #f4f8f6;
  border-bottom: 1px solid #e8eee9;
  overflow-x: auto;
}

.tabs button {
  border: 0;
  background: transparent;
  padding: 8px 13px;
  border-radius: 999px;
  font-size: 13px;
  color: #5b6b63;
  cursor: pointer;
  white-space: nowrap;
}

.tabs button:hover {
  background: #fff;
  color: #163d2e;
}

.tabs .on {
  background: #163d2e;
  color: #fff;
  font-weight: 650;
  box-shadow: 0 6px 14px rgba(22, 61, 46, 0.18);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

caption {
  caption-side: top;
  text-align: left;
  padding: 18px 22px 10px;
  font-size: 16px;
  font-weight: 650;
  color: #12231b;
}

caption span {
  margin-left: 10px;
  padding: 3px 8px;
  border-radius: 999px;
  background: #eef5f1;
  color: #4b6358;
  font-size: 12px;
  font-weight: 600;
}

th,
td {
  padding: 12px 16px;
  font-size: 13px;
  border-bottom: 1px solid #eef3f0;
  font-variant-numeric: tabular-nums;
}

th {
  background: #163d2e;
  color: #fff;
  font-size: 11px;
  font-weight: 650;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-align: left;
}

tbody tr:hover {
  background: #f6fbf8;
}

.col-num,
.col-vol,
.col-status {
  text-align: right;
}

.col-rank {
  width: 72px;
}

th.col-rank {
  color: rgba(255, 255, 255, 0.72);
}

.rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  padding: 0 6px;
  border-radius: 999px;
  background: #eef3f0;
  color: #5b6b63;
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.rank-1 { background: #163d2e; color: #fff; }
.rank-2 { background: #2d6a4f; color: #fff; }
.rank-3 { background: #d8e8df; color: #163d2e; }

.col-name {
  font-weight: 650;
  color: #12231b;
}

.col-zone {
  color: #5b6b63;
}

.col-vol {
  width: 22%;
}

.track {
  height: 7px;
  border-radius: 999px;
  background: #eef3f0;
  overflow: hidden;
}

.track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #1b4d38, #2d8a5a);
}

.flop {
  background: #fff8f8;
}

.flop:hover {
  background: #fff1f1;
}

.flop .track i {
  background: #e2e8e4;
  min-width: 6px;
}

.rate-high { color: #15803d; font-weight: 700; }
.rate-mid { color: #b45309; font-weight: 700; }
.rate-low { color: #be123c; font-weight: 700; }

.st-top,
.st-flop {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 54px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.05em;
}

.st-top {
  background: #e8f6ee;
  color: #15803d;
}

.st-flop {
  background: #fdecec;
  color: #b91c1c;
}

.note {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
  background: #f4f8f6;
  border-top: 1px solid #e8eee9;
  color: #334155;
  font-size: 13px;
}

.note p {
  margin: 0;
  padding: 12px 14px;
  line-height: 1.5;
  background: #fff;
  border: 1px solid #e4ece7;
  border-radius: 12px;
}

.note strong {
  display: block;
  margin-bottom: 4px;
  color: #163d2e;
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.empty {
  padding: 40px 16px;
  text-align: center;
  color: #7b8a82;
}

@media (max-width: 900px) {
  .page-head,
  .metrics,
  .note {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }

  .date-field {
    align-self: flex-start;
  }

  .metric + .metric::before {
    display: none;
  }

  .metric {
    border-bottom: 1px solid #e8eee9;
  }
}
</style>
