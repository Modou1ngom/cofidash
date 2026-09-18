<template>
  <div class="pi-dash">
    <div v-if="piState.loading && !data" class="state-msg">Chargement du tableau de bord PI…</div>

    <template v-else>
      <header class="dash-head">
        <div class="head-copy">
          <h2>Tableau de bord</h2>
          <p class="sub">Enrôlement PI / SPI des nouveaux clients</p>
        </div>
        <div class="head-meta">
          <span v-if="periodLabel" class="chip">{{ periodLabel }}</span>
          <span v-if="lastUpdateLabel !== '—'" class="chip chip-time">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <circle cx="12" cy="12" r="8" />
              <path d="M12 8v4l2.5 1.5" stroke-linecap="round" />
            </svg>
            <span>
              <small>Mis à jour</small>
              {{ lastUpdateLabel }}
            </span>
          </span>
        </div>
      </header>

      <section class="kpi-grid">
        <article class="kpi">
          <div class="kpi-top">
            <span class="kpi-ico ico-green" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" stroke-linecap="round" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" stroke-linecap="round" />
              </svg>
            </span>
            <span>Nouveaux clients</span>
          </div>
          <strong>{{ formatNumber(kpis.total_clients) }}</strong>
          <div class="meter" aria-hidden="true">
            <i class="meter-green" :style="{ width: barWidth(kpis.rate_pi) }" />
          </div>
          <small>{{ formatRate(kpis.rate_pi) }} déjà enrôlés PI</small>
        </article>

        <article class="kpi">
          <div class="kpi-top">
            <span class="kpi-ico ico-blue" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" stroke-linejoin="round" />
              </svg>
            </span>
            <span>Enrôlés PI / SPI</span>
          </div>
          <strong>{{ formatNumber(kpis.enrolled_pi) }}</strong>
          <div class="meter" aria-hidden="true">
            <i class="meter-blue" :style="{ width: barWidth(kpis.rate_pi) }" />
          </div>
          <small>{{ formatNumber(kpis.active_pi) }} comptes PI actifs</small>
        </article>

        <article class="kpi">
          <div class="kpi-top">
            <span class="kpi-ico ico-orange" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <rect x="7" y="2" width="10" height="20" rx="2" />
                <path d="M11 18h2" stroke-linecap="round" />
              </svg>
            </span>
            <span>Enrôlés Mobile +</span>
          </div>
          <strong>{{ formatNumber(kpis.enrolled_mobile) }}</strong>
          <div class="meter" aria-hidden="true">
            <i class="meter-orange" :style="{ width: barWidth(kpis.rate_mobile) }" />
          </div>
          <small>{{ formatRate(kpis.rate_mobile) }} des nouveaux clients</small>
        </article>

        <article class="kpi">
          <div class="kpi-top">
            <span class="kpi-ico ico-red" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 8v5" stroke-linecap="round" />
                <circle cx="12" cy="16" r="0.8" fill="currentColor" />
              </svg>
            </span>
            <span>Non enrôlés PI</span>
          </div>
          <strong>{{ formatNumber(kpis.not_enrolled_pi) }}</strong>
          <div class="meter" aria-hidden="true">
            <i class="meter-red" :style="{ width: barWidth(kpis.rate_not_enrolled_pi) }" />
          </div>
          <small>{{ formatRate(kpis.rate_not_enrolled_pi) }} restant à traiter</small>
        </article>
      </section>

      <section class="chart-grid">
        <article class="card card-wide">
          <div class="card-head">
            <div>
              <h3>Volume quotidien</h3>
              <p>Nouveaux clients et enrôlements PI par jour</p>
            </div>
          </div>
          <PythonChart
            v-if="volumeChartData.labels.length"
            :key="`pi-vol-${periodLabel}`"
            chart-type="multiseries"
            :chart-data="volumeChartData"
            :height="280"
          />
          <p v-else class="empty">Aucune donnée sur la période.</p>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h3>Répartition par canal</h3>
              <p>Volume d’enrôlements PI, Mobile + et USSD</p>
            </div>
          </div>
          <div class="split">
            <PiDonut
              :segments="canals"
              :center-value="canalTotal"
              center-label="Enrôlements"
            />
            <ul class="legend">
              <li v-for="item in canals" :key="item.label">
                <span class="dot" :style="{ background: item.color }" />
                <div>
                  <span>{{ item.label }}</span>
                  <div class="legend-bar" aria-hidden="true">
                    <i :style="{ width: barWidth(item.percent), background: item.color }" />
                  </div>
                </div>
                <div class="legend-vals">
                  <strong>{{ formatNumber(item.value) }}</strong>
                  <small>{{ formatRate(item.percent) }}</small>
                </div>
              </li>
            </ul>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h3>Statut d’enrôlement PI</h3>
              <p>Part des nouveaux clients déjà enrôlés</p>
            </div>
          </div>
          <div class="split">
            <PiDonut
              :segments="statuts"
              :center-value="kpis.total_clients"
              center-label="Clients"
            />
            <ul class="legend">
              <li v-for="item in statuts" :key="item.label">
                <span class="dot" :style="{ background: item.color }" />
                <div>
                  <span>{{ item.label }}</span>
                  <div class="legend-bar" aria-hidden="true">
                    <i :style="{ width: barWidth(item.percent), background: item.color }" />
                  </div>
                </div>
                <div class="legend-vals">
                  <strong>{{ formatNumber(item.value) }}</strong>
                  <small>{{ formatRate(item.percent) }}</small>
                </div>
              </li>
            </ul>
          </div>
        </article>

        <article class="card card-wide card-cta">
          <div>
            <h3>Performance par agence</h3>
            <p>TOP / FLOP du jour par zone, avec le taux de réalisation.</p>
          </div>
          <router-link to="/pi/performance" class="cta-btn">Ouvrir le TOP / FLOP</router-link>
        </article>
      </section>
    </template>
  </div>
</template>

<script>
import PythonChart from '../components/charts/PythonChart.vue';
import PiDonut from '../components/pi/PiDonut.vue';

export default {
  name: 'PiDashboardPage',
  components: { PythonChart, PiDonut },
  inject: ['piState'],
  computed: {
    data() {
      return this.piState.data;
    },
    kpis() {
      return this.data?.kpis || {
        total_clients: 0,
        enrolled_pi: 0,
        enrolled_mobile: 0,
        enrolled_ussd: 0,
        not_enrolled_pi: 0,
        active_pi: 0,
        rate_pi: 0,
        rate_mobile: 0,
        rate_not_enrolled_pi: 0,
      };
    },
    periodLabel() {
      return this.data?.period?.label || '';
    },
    lastUpdateLabel() {
      const raw = this.data?.updated_at;
      if (!raw) return '—';
      const date = new Date(raw);
      if (Number.isNaN(date.getTime())) return raw;
      const day = date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
      const time = date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return `${day} · ${time}`;
    },
    canals() {
      const rows = this.data?.canals || [];
      const total = rows.reduce((sum, row) => sum + (Number(row.value) || 0), 0);
      return rows.map((row) => ({
        ...row,
        percent: total ? (Number(row.value) / total) * 100 : 0,
      }));
    },
    canalTotal() {
      return this.canals.reduce((sum, row) => sum + (Number(row.value) || 0), 0);
    },
    statuts() {
      const rows = this.data?.statuts || [];
      const total = rows.reduce((sum, row) => sum + (Number(row.value) || 0), 0);
      return rows.map((row) => ({
        ...row,
        percent: total ? (Number(row.value) / total) * 100 : 0,
      }));
    },
    volumeChartData() {
      const rows = this.data?.volume || [];
      return {
        labels: rows.map((row) => row.label),
        series: {
          Clients: rows.map((row) => Number(row.clients) || 0),
          'Enrôlés PI': rows.map((row) => Number(row.enrolled_pi) || 0),
        },
        title: '',
        xlabel: 'Jour',
        ylabel: 'Nombre',
        colors: ['#163d2e', '#2563EB'],
      };
    },
  },
  methods: {
    formatNumber(value) {
      return new Intl.NumberFormat('fr-FR').format(Number(value) || 0);
    },
    formatRate(value) {
      return `${(Number(value) || 0).toLocaleString('fr-FR', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })} %`;
    },
    barWidth(value) {
      const rate = Math.max(0, Number(value) || 0);
      return `${Math.min(100, rate)}%`;
    },
  },
};
</script>

<style scoped>
.pi-dash {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dash-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 18px 22px;
  background: #fff;
  border: 1px solid #dce5df;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(18, 35, 27, 0.04);
}

.head-copy h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: #12231b;
}

.sub {
  margin: 4px 0 0;
  color: #5b6b63;
  font-size: 13px;
}

.head-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #dce5df;
  border-radius: 12px;
  background: #f7faf8;
  color: #163d2e;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}

.chip-time {
  font-weight: 600;
  color: #3d4f46;
}

.chip-time svg {
  width: 16px;
  height: 16px;
  color: #163d2e;
}

.chip-time span {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.chip-time small {
  color: #6b7c73;
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.kpi-grid,
.chart-grid {
  display: grid;
  gap: 16px;
}

.kpi-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.chart-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.kpi,
.card {
  background: #fff;
  border: 1px solid #dce5df;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(18, 35, 27, 0.04);
}

.kpi {
  padding: 18px 20px 16px;
}

.kpi-top {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5b6b63;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 14px;
}

.kpi-ico {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-ico svg {
  width: 18px;
  height: 18px;
}

.ico-green { background: #e8f5ee; color: #15803d; }
.ico-blue { background: #e8eefc; color: #1d4ed8; }
.ico-orange { background: #fef3e2; color: #c2410c; }
.ico-red { background: #fdecec; color: #b91c1c; }

.kpi strong {
  display: block;
  font-size: 32px;
  line-height: 1.05;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.meter {
  height: 6px;
  margin: 14px 0 8px;
  border-radius: 999px;
  background: #eef3f0;
  overflow: hidden;
}

.meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.meter-green { background: #15803d; }
.meter-blue { background: #1d4ed8; }
.meter-orange { background: #d97706; }
.meter-red { background: #dc2626; }

.kpi small {
  color: #7b8a82;
  font-size: 12px;
}

.card {
  padding: 20px 22px 18px;
}

.card-wide {
  grid-column: 1 / -1;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.card-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}

.card-head p {
  margin: 4px 0 0;
  color: #7b8a82;
  font-size: 13px;
}

.split {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 230px;
  padding: 8px 0 4px;
}

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  min-width: 180px;
}

.legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 10px;
  align-items: center;
  font-size: 13px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.legend-bar {
  height: 4px;
  margin-top: 6px;
  border-radius: 999px;
  background: #eef3f0;
  overflow: hidden;
}

.legend-bar i {
  display: block;
  height: 100%;
}

.legend-vals {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.legend-vals strong {
  display: block;
  font-size: 14px;
}

.legend-vals small {
  color: #7b8a82;
  font-size: 12px;
}

.card-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-cta h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
}

.card-cta p {
  margin: 4px 0 0;
  color: #7b8a82;
  font-size: 13px;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border-radius: 10px;
  background: #163d2e;
  color: #fff;
  text-decoration: none;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}

.cta-btn:hover {
  background: #1f4d3a;
}

.state-msg,
.empty {
  color: #64748b;
  padding: 24px 0;
  text-align: center;
}

@media (max-width: 1100px) {
  .kpi-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .split {
    flex-direction: column;
  }
}

@media (max-width: 900px) {
  .dash-head,
  .card-cta,
  .head-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .kpi-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
