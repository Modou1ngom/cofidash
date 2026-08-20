<template>
  <div class="comptes-ouverts">
    <div class="toolbar-row">
      <div class="view-tabs">
        <button
          type="button"
          class="view-tab"
          :class="{ active: viewMode === 'dashboard' }"
          @click="viewMode = 'dashboard'"
        >
          Dashboard
        </button>
        <button
          type="button"
          class="view-tab"
          :class="{ active: viewMode === 'performance' }"
          @click="viewMode = 'performance'"
        >
          Performance
        </button>
      </div>

      <div class="period-toolbar">
        <label class="filter-field">
          <select v-model.number="selectedMonth" @change="loadData">
            <option v-for="(month, index) in months" :key="month" :value="index + 1">
              {{ month }}
            </option>
          </select>
        </label>
        <label class="filter-field">
          <select v-model.number="selectedYear" @change="loadData">
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
          </select>
        </label>
        <button type="button" class="btn-refresh" :disabled="loading" @click="loadData">
          <span v-if="loading" class="btn-spinner" />
          {{ loading ? 'Chargement…' : 'Actualiser' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="state-msg">
      <span class="state-spinner" />
      Chargement des ouvertures de comptes…
    </div>
    <div v-else-if="errorMessage" class="state-msg error">{{ errorMessage }}</div>

    <template v-else>
      <!-- ── DASHBOARD EXÉCUTIF ── -->
      <div v-if="viewMode === 'dashboard'" class="dash-view">
        <section class="kpi-grid kpi-grid--5">
          <article class="kpi kpi-obj">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M12 3v18M3 12h18" stroke-linecap="round"/></svg>
            </span>
            <span class="kpi-label">Obj. annuel</span>
            <strong class="kpi-value">{{ formatObj(kpis.objAnnuel) }}</strong>
          </article>
          <article class="kpi kpi-ytd">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M4 19V5M4 19h16M8 15l3-3 3 2 4-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <span class="kpi-label">Obj. YTD</span>
            <strong class="kpi-value">{{ formatObj(kpis.objYtd) }}</strong>
          </article>
          <article class="kpi kpi-realise">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke-linecap="round"/></svg>
            </span>
            <span class="kpi-label">Réalisé YTD</span>
            <strong class="kpi-value">{{ formatNumber(kpis.realiseYtd) }}</strong>
            <span class="kpi-meta">{{ formatNumber(kpis.courantsYtd) }} courants · {{ formatNumber(kpis.epargneYtd) }} épargne</span>
          </article>
          <article class="kpi" :class="ecartClass(kpis.ecartYtd)">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M7 17l5-5 5 5M7 7l5 5 5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <span class="kpi-label">Écart YTD</span>
            <strong class="kpi-value">{{ kpis.tro === null ? '—' : formatSigned(kpis.ecartYtd) }}</strong>
          </article>
          <article class="kpi" :class="troTone(kpis.tro)">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2" stroke-linecap="round"/></svg>
            </span>
            <span class="kpi-label">TRO YTD</span>
            <strong class="kpi-value">{{ formatTro(kpis.tro) }}</strong>
          </article>
        </section>

        <div class="dash-row dash-row--chart">
          <section class="dash-card dash-card--chart">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent" />
                <h3>Évolution mensuelle</h3>
              </div>
              <span class="dash-card-meta">Ouvertures cumulées par mois</span>
            </div>
            <div class="dash-card-chart-body">
              <PythonChart
                :key="`co-bar-${selectedMonth}-${selectedYear}`"
                chart-type="bar"
                :chart-data="monthlyChartData"
                :height="180"
              />
            </div>
          </section>

          <div class="dash-col-stack">
            <section class="dash-card">
              <div class="dash-card-head">
                <div class="dash-card-title">
                  <span class="dash-card-accent" />
                  <h3>Performance territoire</h3>
                </div>
                <span class="dash-card-meta">{{ hasObjectives ? 'TRO YTD' : 'Réalisé YTD' }}</span>
              </div>
              <ul class="territory-rank">
                <li v-for="(row, idx) in dashboardTerritoryRows" :key="row.key">
                  <span class="territory-num">{{ idx + 1 }}</span>
                  <div class="territory-body">
                    <div class="territory-top">
                      <span class="name">{{ row.name }}</span>
                      <span v-if="hasObjectives" :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                      <span v-else class="badge good">{{ formatNumber(row.realise_ytd) }}</span>
                    </div>
                    <div class="territory-bar-track">
                      <div
                        class="territory-bar-fill"
                        :class="hasObjectives ? troBarClass(row.tro) : 'bar-good'"
                        :style="{ width: `${territoryBarWidth(row)}%` }"
                      />
                    </div>
                  </div>
                </li>
                <li v-if="!dashboardTerritoryRows.length" class="empty">Aucune donnée</li>
              </ul>
            </section>

            <section class="dash-card dash-card--alerts">
              <div class="dash-card-head">
                <div class="dash-card-title">
                  <span class="dash-card-accent dash-card-accent--warn" />
                  <h3>Alertes management</h3>
                </div>
              </div>
              <ul class="alerts-list">
                <li v-for="(alert, idx) in managementAlerts" :key="idx" :class="['alert-item', alert.type]">
                  <span class="alert-icon" aria-hidden="true">
                    <svg v-if="alert.type === 'good'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                  </span>
                  <p>{{ alert.text }}</p>
                </li>
                <li v-if="!managementAlerts.length" class="empty">Aucune alerte</li>
              </ul>
            </section>
          </div>
        </div>

        <div class="dash-row dash-row--2">
          <section class="dash-card dash-card--top">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent dash-card-accent--top" />
                <h3>Top 5 agences</h3>
              </div>
              <span class="dash-card-meta">{{ hasObjectives ? 'TRO YTD' : 'Ouvertures YTD' }}</span>
            </div>
            <ol class="agency-rank">
              <li v-for="(row, idx) in dashboardTopAgencies" :key="row.id">
                <span class="rank" :class="idx === 0 ? 'rank-gold' : idx === 1 ? 'rank-silver' : idx === 2 ? 'rank-bronze' : 'rank-top'">{{ idx + 1 }}</span>
                <div class="meta">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.territory }}</span>
                </div>
                <span v-if="hasObjectives" :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                <span v-else class="badge good">{{ formatNumber(row.realise_ytd) }}</span>
              </li>
              <li v-if="!dashboardTopAgencies.length" class="empty">Aucune donnée</li>
            </ol>
          </section>

          <section class="dash-card dash-card--flop">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent dash-card-accent--flop" />
                <h3>Bottom 5 agences</h3>
              </div>
              <span class="dash-card-meta">{{ hasObjectives ? 'TRO YTD' : 'Ouvertures YTD' }}</span>
            </div>
            <ol class="agency-rank">
              <li v-for="(row, idx) in dashboardFlopAgencies" :key="row.id">
                <span class="rank rank-flop">{{ idx + 1 }}</span>
                <div class="meta">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.territory }}</span>
                </div>
                <span v-if="hasObjectives" :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                <span v-else class="badge warn">{{ formatNumber(row.realise_ytd) }}</span>
              </li>
              <li v-if="!dashboardFlopAgencies.length" class="empty">Aucune donnée</li>
            </ol>
          </section>
        </div>
      </div>

      <!-- ── PERFORMANCE DÉTAILLÉE ── -->
      <div v-if="viewMode === 'performance'" class="perf-view">
        <section class="perf-kpi-grid">
          <article class="perf-kpi perf-kpi--month">
            <span class="perf-kpi-label">Réalisé du mois</span>
            <strong class="perf-kpi-value">{{ formatNumber(kpis.realiseM) }}</strong>
            <span class="perf-kpi-meta">{{ monthLabel }} {{ selectedYear }}</span>
          </article>
          <article class="perf-kpi perf-kpi--ytd">
            <span class="perf-kpi-label">Réalisé YTD</span>
            <strong class="perf-kpi-value">{{ formatNumber(kpis.realiseYtd) }}</strong>
            <span class="perf-kpi-meta">Jan. → {{ monthLabel }}</span>
          </article>
          <article class="perf-kpi perf-kpi--courants">
            <span class="perf-kpi-label">Courants</span>
            <strong class="perf-kpi-value">{{ formatNumber(kpis.courantsYtd) }}</strong>
            <span class="perf-kpi-meta">Mois : {{ formatNumber(kpis.courantsM) }}</span>
          </article>
          <article class="perf-kpi perf-kpi--epargne">
            <span class="perf-kpi-label">Épargne</span>
            <strong class="perf-kpi-value">{{ formatNumber(kpis.epargneYtd) }}</strong>
            <span class="perf-kpi-meta">Mois : {{ formatNumber(kpis.epargneM) }} · Mix {{ formatTro(kpis.mixCourants) }}</span>
          </article>
        </section>

        <div class="panels">
          <section class="panel panel--monthly">
            <div class="panel-head">
              <div class="panel-head-title">
                <h3>Suivi mensuel</h3>
                <span class="panel-head-meta">Cumul {{ selectedYear }} jusqu'à {{ monthLabel }}</span>
              </div>
            </div>
            <div class="table-wrap">
              <table class="perf-table">
                <thead>
                  <tr>
                    <th>Mois</th>
                    <th class="num col-highlight">Total</th>
                    <th class="num">Obj. YTD</th>
                    <th class="num">Courants</th>
                    <th class="num">Épargne</th>
                    <th class="num">TRO cumulé</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in monthlyRowsVisible"
                    :key="row.month"
                    :class="{ 'row-current': row.month === selectedMonth }"
                  >
                    <td>
                      <span class="month-tag" :class="{ 'month-tag--current': row.month === selectedMonth }">
                        {{ row.label }}
                      </span>
                    </td>
                    <td class="num col-highlight"><strong>{{ formatNumber(row.total) }}</strong></td>
                    <td class="num">{{ formatObj(row.objYtd) }}</td>
                    <td class="num">{{ formatNumber(row.courants) }}</td>
                    <td class="num">{{ formatNumber(row.epargne) }}</td>
                    <td class="num">
                      <span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="perf-tfoot">
                    <td><strong>Total période</strong></td>
                    <td class="num col-highlight"><strong>{{ formatNumber(kpis.realiseYtd) }}</strong></td>
                    <td class="num"><strong>{{ formatObj(kpis.objYtd) }}</strong></td>
                    <td class="num"><strong>{{ formatNumber(kpis.courantsYtd) }}</strong></td>
                    <td class="num"><strong>{{ formatNumber(kpis.epargneYtd) }}</strong></td>
                    <td class="num"><span :class="troBadge(kpis.tro)">{{ formatTro(kpis.tro) }}</span></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>

          <section class="panel panel--territory">
            <div class="panel-head panel-head--split">
              <div class="panel-head-title">
                <h3>Performance par territoire</h3>
                <span class="panel-head-meta">
                  {{ perfTableMode === 'ytd'
                    ? `Cumul ${selectedYear} jusqu'à ${monthLabel}`
                    : `${monthLabel} ${selectedYear}` }}
                </span>
              </div>
              <div class="perf-mode-toggle">
                <button
                  type="button"
                  :class="{ active: perfTableMode === 'ytd' }"
                  @click="perfTableMode = 'ytd'"
                >
                  YTD
                </button>
                <button
                  type="button"
                  :class="{ active: perfTableMode === 'month' }"
                  @click="perfTableMode = 'month'"
                >
                  Mois actuel
                </button>
              </div>
            </div>
            <div class="table-wrap">
              <table class="perf-table perf-table--territory">
                <thead>
                  <tr>
                    <th>Territoire</th>
                    <th class="num">{{ perfTableMode === 'ytd' ? 'Obj. YTD' : 'Obj. mensuel' }}</th>
                    <th class="num col-highlight">{{ perfTableMode === 'ytd' ? 'Réalisé YTD' : 'Réalisé mois' }}</th>
                    <th class="num">TRO</th>
                    <th class="num">Courants</th>
                    <th class="num">Épargne</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="territory in territories" :key="territory.key">
                    <tr
                      class="territory-row"
                      :class="{ 'territory-row--open': expanded[territory.key] }"
                      @click="toggleTerritory(territory.key)"
                    >
                      <td>
                        <div class="territory-cell">
                          <button
                            type="button"
                            class="expand-btn"
                            :class="{ open: expanded[territory.key] }"
                            @click.stop="toggleTerritory(territory.key)"
                          >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                              <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                          </button>
                          <strong>{{ territory.name }}</strong>
                        </div>
                      </td>
                      <td class="num">{{ formatObj(perfObjSecondary(territory)) }}</td>
                      <td class="num col-highlight"><strong>{{ formatNumber(perfRealise(territory)) }}</strong></td>
                      <td class="num"><span :class="troBadge(perfTro(territory))">{{ formatTro(perfTro(territory)) }}</span></td>
                      <td class="num">{{ formatNumber(perfCourants(territory)) }}</td>
                      <td class="num">{{ formatNumber(perfEpargne(territory)) }}</td>
                    </tr>
                    <template v-if="expanded[territory.key]">
                      <tr
                        v-for="agency in territory.agencies"
                        :key="`${agency.branch_code}-${agency.branch_name}`"
                        class="agency-row"
                      >
                        <td class="agency-name">{{ agency.branch_name }}</td>
                        <td class="num">{{ formatObj(perfObjSecondary(agency)) }}</td>
                        <td class="num col-highlight">{{ formatNumber(perfRealise(agency)) }}</td>
                        <td class="num"><span :class="troBadge(perfTro(agency))">{{ formatTro(perfTro(agency)) }}</span></td>
                        <td class="num">{{ formatNumber(perfCourants(agency)) }}</td>
                        <td class="num">{{ formatNumber(perfEpargne(agency)) }}</td>
                      </tr>
                    </template>
                  </template>
                </tbody>
                <tfoot>
                  <tr class="perf-tfoot">
                    <td><strong>TOTAL</strong></td>
                    <td class="num"><strong>{{ formatObj(perfTotals.objSecondary) }}</strong></td>
                    <td class="num col-highlight"><strong>{{ formatNumber(perfTotals.realise) }}</strong></td>
                    <td class="num"><span :class="troBadge(perfTotals.tro)">{{ formatTro(perfTotals.tro) }}</span></td>
                    <td class="num"><strong>{{ formatNumber(perfTotals.courants) }}</strong></td>
                    <td class="num"><strong>{{ formatNumber(perfTotals.epargne) }}</strong></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import PythonChart from './charts/PythonChart.vue';

const MONTH_BAR_COLORS = [
  '#c8ddd4', '#b5d0c4', '#a2c3b4', '#8fb6a4', '#7ca994',
  '#5f9478', '#1a4d3a', '#174434', '#143b2e', '#153528',
  '#122e22', '#0f271c',
];

function barColorForMonth(month, selectedMonth) {
  if (month === selectedMonth) return '#1a4d3a';
  const idx = month - 1;
  return MONTH_BAR_COLORS[idx] || '#94a3b8';
}

export default {
  name: 'CompteOuvertSection',
  components: { PythonChart },
  data() {
    const now = new Date();
    return {
      loading: false,
      errorMessage: '',
      viewMode: 'dashboard',
      perfTableMode: 'ytd',
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
      ],
      payload: null,
      objectivesByCode: {},
      objectivesByName: {},
      expanded: {},
    };
  },
  computed: {
    years() {
      const current = new Date().getFullYear();
      const years = [];
      for (let y = current + 1; y >= 2024; y -= 1) years.push(y);
      return years;
    },
    monthLabel() {
      return this.months[this.selectedMonth - 1] || '';
    },
    rawKpis() {
      return this.payload?.kpis || {};
    },
    kpis() {
      const realiseYtd = Number(this.rawKpis.realise_ytd || 0);
      const realiseM = Number(this.rawKpis.realise_m || 0);
      const courantsYtd = Number(this.rawKpis.realise_ytd_251 || 0);
      const epargneYtd = Number(this.rawKpis.realise_ytd_253 || 0);
      const objMensuel = this.totalObjMensuel;
      const hasObj = objMensuel > 0;
      const objAnnuel = hasObj ? objMensuel * 12 : 0;
      const objYtd = hasObj ? objMensuel * this.selectedMonth : 0;
      const tro = hasObj ? (realiseYtd / objYtd) * 100 : null;
      const courantsM = Number(this.rawKpis.realise_m_251 || 0);
      const epargneM = Number(this.rawKpis.realise_m_253 || 0);
      const troM = hasObj ? (realiseM / objMensuel) * 100 : null;
      return {
        realiseM,
        realiseYtd,
        courantsYtd,
        epargneYtd,
        courantsM,
        epargneM,
        objMensuel,
        objAnnuel,
        objYtd,
        ecartYtd: hasObj ? realiseYtd - objYtd : 0,
        tro,
        troM,
        mixCourants: realiseYtd > 0 ? (courantsYtd / realiseYtd) * 100 : null,
      };
    },
    totalObjMensuel() {
      return this.territories.reduce((sum, t) => sum + (Number(t.objMensuel) || 0), 0);
    },
    hasObjectives() {
      return this.totalObjMensuel > 0;
    },
    monthlyRows() {
      const rows = this.payload?.monthly || [];
      const objMensuel = this.kpis.objMensuel;
      return rows.map((row) => {
        const objYtd = row.month <= this.selectedMonth ? objMensuel * row.month : 0;
        const tro = objYtd > 0 ? (Number(row.ytd || 0) / objYtd) * 100 : null;
        return {
          ...row,
          objMensuel: row.month <= this.selectedMonth ? objMensuel : 0,
          objYtd,
          tro,
        };
      });
    },
    monthlyRowsVisible() {
      return this.monthlyRows.filter((r) => r.month <= this.selectedMonth);
    },
    perfTotals() {
      if (this.perfTableMode === 'ytd') {
        return {
          objSecondary: this.kpis.objYtd,
          realise: this.kpis.realiseYtd,
          tro: this.kpis.tro,
          courants: this.kpis.courantsYtd,
          epargne: this.kpis.epargneYtd,
        };
      }
      return {
        objSecondary: this.kpis.objMensuel,
        realise: this.kpis.realiseM,
        tro: this.kpis.troM,
        courants: this.kpis.courantsM,
        epargne: this.kpis.epargneM,
      };
    },
    territories() {
      const list = this.payload?.territories || [];
      return list.map((territory) => {
        const agencies = (territory.agencies || []).map((agency) => {
          const objMensuel = this.objectiveForAgency(agency);
          return {
            ...agency,
            objMensuel,
            objYtd: objMensuel * this.selectedMonth,
            objAnnuel: objMensuel * 12,
            tro: this.tro(agency.realise_ytd, objMensuel * this.selectedMonth),
          };
        });
        const objMensuel = agencies.reduce((sum, a) => sum + a.objMensuel, 0);
        return {
          ...territory,
          agencies,
          objMensuel,
          objYtd: objMensuel * this.selectedMonth,
          objAnnuel: objMensuel * 12,
          tro: this.tro(territory.realise_ytd, objMensuel * this.selectedMonth),
        };
      });
    },
    allAgencies() {
      const list = [];
      for (const t of this.territories) {
        for (const a of t.agencies || []) {
          list.push({
            id: `${a.branch_code}-${a.branch_name}`,
            name: a.branch_name,
            territory: t.name,
            realise_ytd: a.realise_ytd,
            objYtd: a.objYtd,
            tro: a.tro,
          });
        }
      }
      return list;
    },
    rankedAgenciesByTro() {
      return [...this.allAgencies]
        .filter((a) => a.tro !== null && a.objYtd > 0)
        .sort((a, b) => b.tro - a.tro);
    },
    rankedAgenciesByRealise() {
      return [...this.allAgencies]
        .filter((a) => Number(a.realise_ytd) > 0)
        .sort((a, b) => b.realise_ytd - a.realise_ytd);
    },
    dashboardTopAgencies() {
      const list = this.hasObjectives ? this.rankedAgenciesByTro : this.rankedAgenciesByRealise;
      return list.slice(0, 5);
    },
    dashboardFlopAgencies() {
      const list = this.hasObjectives ? this.rankedAgenciesByTro : this.rankedAgenciesByRealise;
      return [...list].reverse().slice(0, 5);
    },
    dashboardTerritoryRows() {
      const rows = this.territories.filter((t) => Number(t.realise_ytd) > 0);
      if (this.hasObjectives) {
        return rows
          .filter((t) => t.tro !== null)
          .sort((a, b) => b.tro - a.tro);
      }
      return rows.sort((a, b) => b.realise_ytd - a.realise_ytd);
    },
    monthlyChartData() {
      const rows = this.monthlyRowsVisible;
      return {
        labels: rows.map((r) => r.label),
        values: rows.map((r) => r.total),
        title: '',
        xlabel: 'Mois',
        ylabel: 'Ouvertures',
        colors: rows.map((r) => barColorForMonth(r.month, this.selectedMonth)),
      };
    },
    managementAlerts() {
      const alerts = [];
      if (this.hasObjectives && this.kpis.tro !== null && this.kpis.ecartYtd < 0) {
        alerts.push({
          type: 'bad',
          text: `Déficit YTD de ${this.formatSigned(this.kpis.ecartYtd)} comptes ouverts`,
        });
      }
      const sortedTerritories = this.hasObjectives
        ? [...this.territories].filter((t) => t.tro !== null).sort((a, b) => a.tro - b.tro)
        : [...this.dashboardTerritoryRows].reverse();
      const worst = sortedTerritories[0];
      const best = this.dashboardTerritoryRows[0];
      if (this.hasObjectives) {
        if (worst && worst.tro < 75) {
          alerts.push({
            type: 'bad',
            text: `${worst.name} en sous-performance (${this.formatTro(worst.tro)})`,
          });
        }
        const flop = this.dashboardFlopAgencies[0];
        if (flop && flop.tro < 60) {
          alerts.push({
            type: 'bad',
            text: `${flop.name} — TRO ${this.formatTro(flop.tro)}`,
          });
        }
        if (best && best.tro >= 90) {
          alerts.push({
            type: 'good',
            text: `${best.name} performant (${this.formatTro(best.tro)})`,
          });
        }
      } else if (best) {
        alerts.push({
          type: 'good',
          text: `${best.name} — leader avec ${this.formatNumber(best.realise_ytd)} ouvertures YTD`,
        });
        if (worst && worst.key !== best.key) {
          alerts.push({
            type: 'bad',
            text: `${worst.name} — ${this.formatNumber(worst.realise_ytd)} ouvertures YTD`,
          });
        }
      }
      const months = this.monthlyRowsVisible.filter((r) => r.total > 0);
      if (months.length >= 2) {
        const last = months[months.length - 1].total;
        const prev = months[months.length - 2].total;
        if (last >= prev) {
          alerts.push({ type: 'good', text: 'Tendance mensuelle en amélioration depuis janvier' });
        } else {
          alerts.push({ type: 'bad', text: 'Baisse des ouvertures sur le dernier mois' });
        }
      }
      return alerts;
    },
  },
  mounted() {
    this.loadData();
  },
  methods: {
    formatNumber(value) {
      const n = Number(value || 0);
      return new Intl.NumberFormat('fr-FR').format(Math.round(n));
    },
    formatObj(value) {
      const n = Number(value || 0);
      if (!n) return '—';
      return this.formatNumber(n);
    },
    formatSigned(value) {
      const n = Number(value || 0);
      const formatted = this.formatNumber(Math.abs(n));
      if (n > 0) return `+${formatted}`;
      if (n < 0) return `−${formatted}`;
      return formatted;
    },
    formatTro(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      return `${Number(value).toFixed(1)} %`;
    },
    tro(realise, objectif) {
      const obj = Number(objectif || 0);
      if (obj <= 0) return null;
      return (Number(realise || 0) / obj) * 100;
    },
    troTone(value) {
      if (value === null || value === undefined) return 'kpi-neutral';
      if (value >= 100) return 'kpi-good';
      if (value >= 75) return 'kpi-warn';
      return 'kpi-bad';
    },
    troBadge(value) {
      if (value === null || value === undefined) return 'badge muted';
      if (value >= 100) return 'badge good';
      if (value >= 75) return 'badge mid';
      if (value >= 50) return 'badge warn';
      return 'badge bad';
    },
    ecartClass(value) {
      if (value > 0) return 'kpi-good';
      if (value < 0) return 'kpi-bad';
      return 'kpi-neutral';
    },
    perfObjSecondary(row) {
      return this.perfTableMode === 'ytd' ? row.objYtd : row.objMensuel;
    },
    perfRealise(row) {
      return this.perfTableMode === 'ytd' ? row.realise_ytd : row.realise_m;
    },
    perfTro(row) {
      if (this.perfTableMode === 'ytd') return row.tro;
      return this.tro(row.realise_m, row.objMensuel);
    },
    perfCourants(row) {
      return this.perfTableMode === 'ytd' ? row.realise_ytd_251 : row.realise_m_251;
    },
    perfEpargne(row) {
      return this.perfTableMode === 'ytd' ? row.realise_ytd_253 : row.realise_m_253;
    },
    territoryBarWidth(row) {
      const rows = this.dashboardTerritoryRows;
      if (!rows.length) return 0;
      if (this.hasObjectives) {
        const max = Math.max(...rows.map((r) => Number(r.tro) || 0), 100);
        return Math.min(100, Math.round(((Number(row.tro) || 0) / max) * 100));
      }
      const max = Number(rows[0]?.realise_ytd) || 1;
      return Math.min(100, Math.round((Number(row.realise_ytd) / max) * 100));
    },
    troBarClass(value) {
      if (value === null || value === undefined) return 'bar-neutral';
      if (value >= 100) return 'bar-good';
      if (value >= 75) return 'bar-warn';
      return 'bar-bad';
    },
    toggleTerritory(key) {
      this.expanded = { ...this.expanded, [key]: !this.expanded[key] };
    },
    objectiveForAgency(agency) {
      const code = String(agency.branch_code || '').trim();
      if (code && this.objectivesByCode[code] != null) {
        return Number(this.objectivesByCode[code]) || 0;
      }
      const name = String(agency.branch_name || '').toUpperCase().trim();
      if (name && this.objectivesByName[name] != null) {
        return Number(this.objectivesByName[name]) || 0;
      }
      return 0;
    },
    async loadData() {
      this.loading = true;
      this.errorMessage = '';
      try {
        const [oracleRes] = await Promise.all([
          window.axios.get('/api/oracle/data/comptes-ouverts', {
            params: { month: this.selectedMonth, year: this.selectedYear },
            timeout: 180000,
          }),
          this.loadObjectives(),
        ]);
        this.payload = oracleRes.data || {};
      } catch (err) {
        this.errorMessage =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          'Impossible de charger les ouvertures de comptes.';
      } finally {
        this.loading = false;
      }
    },
    async loadObjectives() {
      try {
        const token = localStorage.getItem('token');
        const response = await window.axios.get('/api/objectives', {
          params: {
            type: 'CLIENT',
            period: 'month',
            month: this.selectedMonth,
            year: this.selectedYear,
          },
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const list = response.data?.success ? response.data.data : [];
        const byCode = {};
        const byName = {};
        (Array.isArray(list) ? list : []).forEach((obj) => {
          const value = Number(obj.value || 0);
          if (obj.agency_code) byCode[String(obj.agency_code).trim()] = value;
          if (obj.agency_name) byName[String(obj.agency_name).toUpperCase().trim()] = value;
        });
        this.objectivesByCode = byCode;
        this.objectivesByName = byName;
      } catch {
        this.objectivesByCode = {};
        this.objectivesByName = {};
      }
    },
  },
};
</script>

<style scoped>
.comptes-ouverts {
  --ink: #0f172a;
  --muted: #64748b;
  --line: #e2e8f0;
  --green: #1a4d3a;
  --green-light: #ecfdf5;
  --surface: #f8fafc;
  --card-shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 4px 16px rgba(15, 23, 42, 0.04);
  padding: 0 0 2rem;
  color: var(--ink);
}

/* ── Barre outils (onglets + filtres) ── */
.toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 0.85rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line);
}

.period-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: flex-end;
  gap: 0.65rem;
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.filter-field span {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}

.filter-field select,
.btn-refresh {
  min-height: 38px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  padding: 0 0.75rem;
  font-size: 0.88rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.filter-field select:focus {
  outline: none;
  border-color: var(--green);
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.12);
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
  font-weight: 600;
  background: var(--green);
  color: #fff;
  border-color: var(--green);
  padding: 0 1.1rem;
}

.btn-refresh:hover:not(:disabled) {
  background: #153d2a;
  border-color: #153d2a;
}

.btn-refresh:disabled {
  opacity: 0.65;
  cursor: default;
}

.btn-spinner,
.state-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

.state-spinner {
  border-color: rgba(26, 77, 58, 0.2);
  border-top-color: var(--green);
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Tabs ── */
.view-tabs {
  display: inline-flex;
  gap: 4px;
  margin-bottom: 0;
  padding: 4px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
}

.view-tab {
  padding: 0.55rem 1.25rem;
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--muted);
  background: transparent;
  border: none;
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.view-tab:hover {
  color: var(--green);
  background: rgba(26, 77, 58, 0.06);
}

.view-tab.active {
  color: #fff;
  font-weight: 600;
  background: var(--green);
  box-shadow: 0 2px 6px rgba(26, 77, 58, 0.25);
}

.state-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.state-msg.error {
  color: #b91c1c;
  background: #fef2f2;
  border-radius: 10px;
  border: 1px solid #fecaca;
}

/* ── KPIs ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  margin-bottom: 1.1rem;
}

.kpi-grid--5 {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.kpi {
  position: relative;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.95rem 1rem 0.95rem 1.1rem;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  transition: box-shadow 0.18s, transform 0.18s;
}

.kpi:hover {
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.kpi-icon {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  width: 1.65rem;
  height: 1.65rem;
  color: rgba(26, 77, 58, 0.18);
}

.kpi-icon svg {
  width: 100%;
  height: 100%;
}

.kpi-label {
  display: block;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.3rem;
  font-weight: 600;
}

.kpi-value {
  display: block;
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.kpi-meta {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.72rem;
  color: var(--muted);
}

.kpi-obj { border-top: 3px solid #2563eb; }
.kpi-ytd { border-top: 3px solid #0f766e; }
.kpi-realise { border-top: 3px solid #1a4d3a; }
.kpi-good { border-top: 3px solid #059669; }
.kpi-warn { border-top: 3px solid #d97706; }
.kpi-bad { border-top: 3px solid #dc2626; }
.kpi-neutral { border-top: 3px solid #94a3b8; }

.kpi-good .kpi-value { color: #047857; }
.kpi-bad .kpi-value { color: #b91c1c; }

/* ── Dashboard layout ── */
.dash-row {
  display: grid;
  gap: 0.85rem;
  margin-bottom: 0.85rem;
}

.dash-row--2,
.dash-row--chart {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
}

.dash-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--card-shadow);
}

.dash-card--chart {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.dash-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  background: linear-gradient(135deg, #1a4d3a 0%, #236b4e 100%);
  color: #fff;
  border-bottom: none;
}

.dash-card--alerts .dash-card-head {
  background: linear-gradient(135deg, #b45309 0%, #d97706 100%);
}

.dash-card--top .dash-card-head {
  background: linear-gradient(135deg, #047857 0%, #059669 100%);
}

.dash-card--flop .dash-card-head {
  background: linear-gradient(135deg, #991b1b 0%, #b91c1c 100%);
}

.dash-card-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.dash-card-accent {
  display: none;
}

.dash-card-head h3 {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #fff;
}

.dash-card-meta {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.82);
  white-space: nowrap;
}

.dash-card-chart-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 0.25rem 0.5rem 0.5rem;
  background: var(--surface);
}

.dash-card-chart-body :deep(.python-chart-container) {
  flex: 1;
  min-height: 0 !important;
  height: auto !important;
}

.dash-card-chart-body :deep(.chart-wrapper) {
  min-height: 0 !important;
  height: 100% !important;
}

.dash-card-chart-body :deep(.chart-loading),
.dash-card-chart-body :deep(.chart-error) {
  min-height: 9rem !important;
  height: 100% !important;
}

.dash-col-stack {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  min-height: 100%;
}

/* ── Territoire ── */
.territory-rank {
  list-style: none;
  margin: 0;
  padding: 0.65rem 1rem 0.75rem;
}

.territory-rank li {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.territory-rank li:last-child {
  border-bottom: none;
}

.territory-num {
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 6px;
  background: var(--surface);
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.territory-body {
  flex: 1;
  min-width: 0;
}

.territory-top {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.territory-top .name {
  flex: 1;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--ink);
  min-width: 0;
}

.territory-bar-track {
  height: 4px;
  background: #f1f5f9;
  border-radius: 999px;
  overflow: hidden;
}

.territory-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.bar-good { background: linear-gradient(90deg, #34d399, #059669); }
.bar-warn { background: linear-gradient(90deg, #fbbf24, #d97706); }
.bar-bad { background: linear-gradient(90deg, #f87171, #dc2626); }
.bar-neutral { background: #94a3b8; }

/* ── Alertes ── */
.alerts-list {
  list-style: none;
  margin: 0;
  padding: 0.65rem 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.55rem 0.65rem;
  border-radius: 8px;
  font-size: 0.82rem;
  line-height: 1.45;
}

.alert-item p {
  margin: 0;
}

.alert-item.good {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.alert-item.bad {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.alert-icon {
  width: 1.1rem;
  height: 1.1rem;
  flex-shrink: 0;
  margin-top: 0.05rem;
}

.alert-icon svg {
  width: 100%;
  height: 100%;
}

.alert-item.good .alert-icon { color: #059669; }
.alert-item.bad .alert-icon { color: #dc2626; }

/* ── Agences ── */
.agency-rank {
  list-style: none;
  margin: 0;
  padding: 0.5rem 0.75rem 0.65rem;
  counter-reset: none;
}

.agency-rank li {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.5rem;
  border-radius: 8px;
  transition: background 0.15s;
}

.agency-rank li:hover {
  background: var(--surface);
}

.agency-rank li + li {
  border-top: 1px solid #f1f5f9;
}

.agency-rank .meta {
  flex: 1;
  min-width: 0;
}

.agency-rank .meta strong {
  display: block;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agency-rank .meta span {
  font-size: 0.73rem;
  color: var(--muted);
}

.rank {
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
}

.rank-top {
  background: var(--green-light);
  color: #047857;
}

.rank-gold {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #92400e;
  box-shadow: 0 0 0 1px #fcd34d;
}

.rank-silver {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  color: #475569;
  box-shadow: 0 0 0 1px #cbd5e1;
}

.rank-bronze {
  background: linear-gradient(135deg, #ffedd5, #fed7aa);
  color: #9a3412;
  box-shadow: 0 0 0 1px #fdba74;
}

.rank-flop {
  background: #fef2f2;
  color: #b91c1c;
}

.empty {
  color: var(--muted);
  font-size: 0.84rem;
  padding: 0.75rem 0.5rem;
  text-align: center;
}

/* ── Badges ── */
.badge {
  display: inline-flex;
  min-width: 3.5rem;
  justify-content: center;
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.74rem;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.badge.good { background: #d1fae5; color: #047857; }
.badge.mid { background: #fef3c7; color: #b45309; }
.badge.warn { background: #ffedd5; color: #c2410c; }
.badge.bad { background: #fee2e2; color: #b91c1c; }
.badge.muted, .muted { color: #94a3b8; }

/* ── Performance view ── */
.perf-view {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.perf-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}

.perf-kpi {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.95rem 1.05rem;
  box-shadow: var(--card-shadow);
  transition: box-shadow 0.18s, transform 0.18s;
}

.perf-kpi:hover {
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
}

.perf-kpi-label {
  display: block;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.35rem;
}

.perf-kpi-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
  color: var(--ink);
}

.perf-kpi-meta {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.72rem;
  color: var(--muted);
}

.perf-kpi--month { border-top: 3px solid #1a4d3a; }
.perf-kpi--ytd { border-top: 3px solid #0f766e; }
.perf-kpi--courants { border-top: 3px solid #2563eb; }
.perf-kpi--epargne { border-top: 3px solid #7c3aed; }

.panels {
  display: grid;
  gap: 0.85rem;
}

.panel {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: var(--card-shadow);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  background: linear-gradient(135deg, #1a4d3a 0%, #236b4e 100%);
  color: #fff;
}

.panel--territory .panel-head {
  background: linear-gradient(135deg, #047857 0%, #059669 100%);
}

.panel-head-title {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.panel-head h3 {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.panel-head-meta {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.82);
}

.panel-head--split {
  flex-wrap: wrap;
  gap: 0.65rem;
}

.perf-mode-toggle {
  display: inline-flex;
  padding: 3px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  gap: 2px;
  flex-shrink: 0;
}

.perf-mode-toggle button {
  padding: 0.35rem 0.85rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.perf-mode-toggle button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.perf-mode-toggle button.active {
  color: var(--green);
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.table-wrap {
  overflow-x: auto;
}

.perf-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.perf-table th,
.perf-table td {
  padding: 0.62rem 0.85rem;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
}

.perf-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f8fafc;
  font-size: 0.67rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 700;
  white-space: nowrap;
}

.perf-table tbody tr:nth-child(even) {
  background: #fafbfc;
}

.perf-table tbody tr:hover {
  background: #f1f5f9;
}

.perf-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.perf-table .col-highlight {
  background: rgba(26, 77, 58, 0.04);
}

.perf-table thead .col-highlight {
  background: #eef6f2;
  color: #1a4d3a;
}

.perf-table .row-current {
  background: #ecfdf5 !important;
  box-shadow: inset 3px 0 0 #1a4d3a;
}

.perf-table .row-current:hover {
  background: #d1fae5 !important;
}

.month-tag {
  display: inline-flex;
  min-width: 2.4rem;
  justify-content: center;
  padding: 0.15rem 0.45rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #475569;
  background: #f1f5f9;
}

.month-tag--current {
  color: #fff;
  background: #1a4d3a;
}

.perf-table--territory tbody tr:nth-child(even) {
  background: transparent;
}

.perf-table--territory .territory-row td {
  background: #e8f5ef;
  color: #0f172a;
  font-weight: 600;
  font-size: 0.84rem;
  border-bottom: 1px solid #c6e0d4;
  box-shadow: inset 4px 0 0 #1a4d3a;
}

.perf-table--territory .territory-row:hover td {
  background: #d8efe4;
}

.perf-table--territory .territory-row--open td {
  background: #d1fae5;
  border-bottom-color: #a7d4bc;
}

.territory-row {
  cursor: pointer;
  transition: background 0.15s;
}

.territory-row td:first-child {
  min-width: 14rem;
}

.territory-cell {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.territory-cell strong {
  min-width: 0;
  color: #1a4d3a;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  font-size: 0.8rem;
}

.perf-table--territory .territory-row .col-highlight {
  background: rgba(26, 77, 58, 0.12);
  color: #1a4d3a;
}

.perf-table--territory .agency-row .col-highlight {
  background: #f8fafc;
  font-weight: 500;
  color: #64748b;
}

.perf-table--territory .agency-row td {
  background: #fff;
  color: #64748b;
  font-weight: 400;
  font-size: 0.78rem;
  border-bottom: 1px solid #eef2f6;
  box-shadow: none;
}

.perf-table--territory .agency-row:hover td {
  background: #f8fafc;
  color: #475569;
}

.perf-table--territory .agency-row td:first-child {
  background: #fafbfc;
  border-left: 3px solid #d1fae5;
}

.agency-name {
  padding-left: 2.75rem !important;
  position: relative;
  font-style: normal;
}

.agency-name::before {
  content: '';
  position: absolute;
  left: 1.5rem;
  top: 50%;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #94a3b8;
  transform: translateY(-50%);
}

.agency-name::after {
  content: '';
  position: absolute;
  left: 1.83rem;
  top: 0;
  bottom: 50%;
  width: 1px;
  background: #cbd5e1;
}

.perf-tfoot {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #fff;
}

.perf-tfoot td {
  border-bottom: none;
  padding: 0.75rem 0.85rem;
  font-variant-numeric: tabular-nums;
}

.perf-tfoot .col-highlight {
  background: rgba(255, 255, 255, 0.06);
}

.expand-btn {
  width: 1.5rem;
  height: 1.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid #cbd5e1;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s;
  padding: 0;
}

.expand-btn svg {
  width: 0.85rem;
  height: 0.85rem;
  transition: transform 0.2s;
}

.expand-btn.open svg {
  transform: rotate(90deg);
}

.expand-btn.open {
  background: #1a4d3a;
  border-color: #1a4d3a;
  color: #fff;
}

.expand-btn:hover {
  border-color: #1a4d3a;
  color: #1a4d3a;
}

/* Legacy table styles (dashboard) */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

th, td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
}

th {
  background: var(--surface);
  font-size: 0.68rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #475569;
  font-weight: 600;
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

tr.current {
  background: var(--green-light);
  font-weight: 600;
}

tr.future {
  color: #94a3b8;
}

.total-row {
  background: var(--ink);
  color: #fff;
}

@media (max-width: 1100px) {
  .kpi-grid--5 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .dash-row--2,
  .dash-row--chart {
    grid-template-columns: 1fr;
  }
  .kpi-mini,
  .perf-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .toolbar-row {
    flex-direction: column;
    align-items: stretch;
  }
  .period-toolbar {
    justify-content: stretch;
  }
  .period-toolbar .filter-field,
  .period-toolbar .btn-refresh {
    flex: 1;
    min-width: 0;
  }
  .view-tabs {
    width: 100%;
    display: flex;
  }
  .view-tab {
    flex: 1;
    text-align: center;
  }
  .kpi-grid--5,
  .kpi-mini,
  .perf-kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
