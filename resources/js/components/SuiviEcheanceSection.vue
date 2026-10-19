<template>
  <section class="echeance">
    <header class="head">
      <div class="head-top">
        <h2>Suivi échéance</h2>
        <div class="segment" role="tablist" aria-label="Affichage">
          <button type="button" :class="{ on: view === 'dashboard' }" @click="view = 'dashboard'">Dashboard</button>
          <button type="button" :class="{ on: view === 'detail' }" @click="view = 'detail'">Détail</button>
        </div>
        <label class="chip chip-year">
          <span>Année</span>
          <select v-model.number="year" @change="load">
            <option v-for="item in years" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="chip chip-month">
          <span>Mois</span>
          <select v-model.number="month" @change="load">
            <option v-for="item in monthOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>
        <button type="button" class="refresh" :disabled="loading" title="Actualiser" @click="load">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M20 12a8 8 0 1 1-2.2-5.5" stroke-linecap="round" />
            <path d="M20 4v5h-5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
      <div v-if="view !== 'objectif'" class="filters">
        <label class="chip">
          <span>Agence</span>
          <select v-model="agence" @change="page = 1">
            <option value="">Toutes</option>
            <option v-for="item in agencyOptions" :key="item.code" :value="item.code">{{ item.label }}</option>
          </select>
        </label>
        <label class="chip">
          <span>CAF</span>
          <select v-model="caf" @change="page = 1">
            <option value="">Tous</option>
            <option v-for="item in cafOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Semaine</span>
          <select v-model="week" @change="page = 1">
            <option value="">Toutes</option>
            <option v-for="item in weekCards" :key="item.key" :value="item.key">{{ item.label }} · {{ item.range }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Statut</span>
          <select v-model="status" @change="page = 1">
            <option value="">Tous</option>
            <option value="I">Impayé</option>
            <option value="R">Remboursé</option>
            <option value="A">Échéance A</option>
            <option value="none">Sans échéance du mois</option>
          </select>
        </label>
      </div>
    </header>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-else-if="warning" class="banner warn">{{ warning }}</p>
    <p v-else-if="loading && !rows.length" class="banner">Chargement du suivi échéance…</p>
    <p v-else-if="!loading && rows.length && !rowsInObjectif.length" class="banner warn">
      Aucun prêt du tombé du mois ne figure dans l'objectif de recouvrement. Ces dossiers ne sont pas affichés.
    </p>

    <div v-if="view === 'dashboard' && rowsInObjectif.length" class="kpis">
      <article
        v-for="card in kpiCards"
        :key="card.key"
        class="kpi-card"
        :class="{ on: activeKpi === card.key }"
        :style="{ '--accent': card.accent }"
        role="button"
        tabindex="0"
        :aria-label="`Détail ${card.label}`"
        @click="openKpi(card.key)"
        @keydown.enter.prevent="openKpi(card.key)"
      >
        <span class="kpi-top">
          <i class="kpi-icon" aria-hidden="true" v-html="kpiIcon(card.key)"></i>
          <span>{{ card.label }}</span>
        </span>
        <strong>{{ formatKpi(card) }}</strong>
        <small>{{ card.unit }}</small>
      </article>
      <article
        v-for="card in formulaCards"
        :key="card.key"
        :style="{ '--accent': card.accent }"
      >
        <span class="kpi-top">
          <i class="kpi-icon" aria-hidden="true" v-html="kpiIcon(card.key)"></i>
          <span>{{ card.label }}</span>
        </span>
        <strong>{{ formatKpi(card) }}</strong>
        <small>{{ card.unit }}</small>
      </article>
    </div>

    <div v-if="view === 'dashboard' && activeKpiCard" class="kpi-overlay" @click.self="closeKpi">
      <section class="kpi-panel" role="dialog" aria-modal="true" :aria-label="activeKpiCard.label">
        <header class="kpi-panel-head">
          <div>
            <p>Détail</p>
            <h3>{{ activeKpiCard.label }}</h3>
          </div>
          <button type="button" class="kpi-close" aria-label="Fermer" @click="closeKpi">×</button>
        </header>
        <div class="kpi-panel-stats">
          <p>
            <span>{{ activeKpiCard.money === false ? 'Dossiers' : 'Montant' }}</span>
            <strong>{{ formatKpi(activeKpiCard) }}</strong>
          </p>
          <p><span>Lignes</span><strong>{{ formatCount(kpiDetailRows.length) }}</strong></p>
        </div>
        <label class="kpi-search">
          <span>Recherche</span>
          <input v-model.trim="kpiQuery" type="search" placeholder="N° de prêt, client, agence" @input="kpiPage = 1">
        </label>
        <div class="kpi-panel-table">
          <table>
            <thead>
              <tr>
                <th>N° prêt</th>
                <th>Matricule</th>
                <th>Client</th>
                <th>Compte</th>
                <th class="num">Objectif</th>
                <th class="num">Global dû</th>
                <th class="num">Réalisé du mois</th>
                <th>Déblocage</th>
                <th class="num">Capital accordé</th>
                <th class="num">Encours total</th>
                <th class="num">% remb.</th>
                <th>Statut prêt</th>
                <th>Statut déclassement</th>
                <th>Code gestion</th>
                <th>CAF</th>
                <th class="num">Solde dépôt garantie</th>
                <th>Date échéance</th>
                <th class="num">N° échéance</th>
                <th class="num">Solde compte</th>
                <th class="num">Montant échéance</th>
                <th>Statut échéance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in kpiPageRows" :key="row.no_pret ? rowKey(row) : `${row.account_number}-${index}`">
                <td>{{ row.no_pret || row.account_number || '—' }}</td>
                <td>{{ lineOf(row).matricule_client || '—' }}</td>
                <td>{{ lineOf(row).nom_client || '—' }}</td>
                <td>{{ lineOf(row).compte || '—' }}</td>
                <td class="num">{{ formatMoney(objectifOf(row)) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).mt_global_due_a_date) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).montant_echeance_paye) }}</td>
                <td>{{ formatDate(lineOf(row).date_deblocage) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).montant_capital_accorde) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).encours_total) }}</td>
                <td class="num">{{ formatPercent(lineOf(row).pourcentage_remboursement) }}</td>
                <td>{{ lineOf(row).statut_pret || row.statut_pret || '—' }}</td>
                <td>{{ lineOf(row).statut_declassement || '—' }}</td>
                <td>{{ lineOf(row).code_gestion_pret || '—' }}</td>
                <td>{{ lineOf(row).charge_affaire || '—' }}</td>
                <td class="num">{{ formatMoney(lineOf(row).solde_depot_garantie) }}</td>
                <td>{{ formatDate(lineOf(row).schedule_due_date) }}</td>
                <td class="num">{{ lineOf(row).numero_echeance ?? '—' }}</td>
                <td class="num">{{ formatMoney(lineOf(row).solde_cpte) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).montant_echeance_m) }}</td>
                <td><span class="badge" :class="statusClass(lineOf(row).status_ech)">{{ statusLabel(lineOf(row).status_ech) }}</span></td>
              </tr>
              <tr v-if="!kpiPageRows.length">
                <td colspan="21" class="empty">Aucune ligne pour cet indicateur.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer v-if="kpiPageCount > 1" class="pager">
          <button type="button" :disabled="kpiPage <= 1" @click="kpiPage -= 1">Précédent</button>
          <span>{{ kpiPage }} / {{ kpiPageCount }}</span>
          <button type="button" :disabled="kpiPage >= kpiPageCount" @click="kpiPage += 1">Suivant</button>
        </footer>
      </section>
    </div>

    <div v-if="view === 'dashboard' && rowsInObjectif.length" class="grid-2">
      <article class="panel">
        <header class="panel-head">
          <h2>Échéances par agence</h2>
        </header>
        <div v-if="agencyBars.length" class="chart-scroll">
          <div class="chart-box tall" :style="{ width: agencyChartWidth }">
            <canvas ref="barCanvas"></canvas>
          </div>
        </div>
        <p v-else class="empty">Aucune échéance pour cette sélection.</p>
        <ul v-if="agencyBars.length" class="inline-legend stack-legend">
          <li v-for="item in weekSeries" :key="item.key">
            <span class="swatch square" :style="{ background: item.color }"></span>
            {{ item.label }}
          </li>
        </ul>
      </article>

      <article class="panel">
        <header class="panel-head">
          <h2>Répartition par statut</h2>
        </header>
        <div v-if="statusSlices.length" class="donut-layout">
          <div class="donut">
            <canvas ref="donutCanvas"></canvas>
            <div class="donut-center">
              <strong>{{ formatCount(statusTotal) }}</strong>
              <span>lignes</span>
            </div>
          </div>
          <ul class="legend">
            <li v-for="slice in statusSlices" :key="slice.key">
              <span class="swatch" :style="{ background: slice.color }"></span>
              <span class="legend-name">{{ slice.label }}</span>
              <span class="legend-value">{{ formatCount(slice.value) }}</span>
            </li>
          </ul>
        </div>
        <p v-else class="empty">Aucune échéance pour cette sélection.</p>
      </article>
    </div>

    <section v-if="view === 'detail' && agencyBars.length" class="panel rank-panel">
      <header class="panel-head">
        <h2>Classement des agences</h2>
        <span>Tombé, réalisé et taux</span>
      </header>
      <div class="rank-table">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Agence</th>
              <th class="num">Tombé</th>
              <th class="num">Réalisé</th>
              <th class="num">Reste</th>
              <th>Taux</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, index) in agencyBars"
              :key="row.key"
              class="rank-row"
              :class="{ on: selectedAgency === row.key }"
              @click="openAgency(row)"
            >
              <td class="rank-index" :class="'pos-' + (index + 1)">{{ index + 1 }}</td>
              <td>{{ row.label }}</td>
              <td class="num">{{ formatCompact(row.tombe) }}</td>
              <td class="num">{{ formatCompact(row.realise) }}</td>
              <td class="num" :class="{ 'is-gap': row.reste > 0 }">{{ formatCompact(row.reste) }}</td>
              <td class="rate-cell">
                <span class="rate-track"><span :style="{ width: agencyRate(row) + '%' }"></span></span>
                <strong :class="{ 'is-gap': agencyRate(row) < 100 }">{{ formatPercent(agencyRate(row)) }}</strong>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="view === 'detail' && selectedAgencyRow" class="kpi-overlay" @click.self="closeAgency">
      <section class="kpi-panel" role="dialog" aria-modal="true" :aria-label="selectedAgencyRow.label">
        <header class="kpi-panel-head">
          <div>
            <p>Détail</p>
            <h3>{{ selectedAgencyRow.label }}</h3>
          </div>
          <button type="button" class="kpi-close" aria-label="Fermer" @click="closeAgency">×</button>
        </header>
        <div class="kpi-panel-stats">
          <p><span>Tombé</span><strong>{{ formatCompact(selectedAgencyRow.tombe) }}</strong></p>
          <p><span>Réalisé</span><strong>{{ formatCompact(selectedAgencyRow.realise) }}</strong></p>
          <p><span>Lignes</span><strong>{{ formatCount(agencyDetailRows.length) }}</strong></p>
        </div>
        <label class="kpi-search">
          <span>Recherche</span>
          <input v-model.trim="agencyQuery" type="search" placeholder="N° de prêt, client, compte" @input="agencyPage = 1">
        </label>
        <div class="kpi-panel-table">
          <table>
            <thead>
              <tr>
                <th>N° prêt</th>
                <th>Matricule</th>
                <th>Client</th>
                <th>Compte</th>
                <th class="num">Objectif</th>
                <th class="num">Global dû</th>
                <th class="num">Réalisé du mois</th>
                <th>Déblocage</th>
                <th class="num">Capital accordé</th>
                <th class="num">Encours total</th>
                <th class="num">% remb.</th>
                <th>Statut prêt</th>
                <th>Statut déclassement</th>
                <th>Code gestion</th>
                <th>CAF</th>
                <th class="num">Solde dépôt garantie</th>
                <th>Date échéance</th>
                <th class="num">N° échéance</th>
                <th class="num">Solde compte</th>
                <th class="num">Montant échéance</th>
                <th>Statut échéance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in agencyPageRows" :key="rowKey(row)">
                <td>{{ row.no_pret || '—' }}</td>
                <td>{{ row.matricule_client || '—' }}</td>
                <td>{{ row.nom_client || '—' }}</td>
                <td>{{ row.compte || '—' }}</td>
                <td class="num">{{ formatMoney(objectifOf(row)) }}</td>
                <td class="num">{{ formatMoney(row.mt_global_due_a_date) }}</td>
                <td class="num">{{ formatMoney(row.montant_echeance_paye) }}</td>
                <td>{{ formatDate(row.date_deblocage) }}</td>
                <td class="num">{{ formatMoney(row.montant_capital_accorde) }}</td>
                <td class="num">{{ formatMoney(row.encours_total) }}</td>
                <td class="num">{{ formatPercent(row.pourcentage_remboursement) }}</td>
                <td>{{ row.statut_pret || '—' }}</td>
                <td>{{ row.statut_declassement || '—' }}</td>
                <td>{{ row.code_gestion_pret || '—' }}</td>
                <td>{{ row.charge_affaire || '—' }}</td>
                <td class="num">{{ formatMoney(row.solde_depot_garantie) }}</td>
                <td>{{ formatDate(row.schedule_due_date) }}</td>
                <td class="num">{{ row.numero_echeance ?? '—' }}</td>
                <td class="num">{{ formatMoney(row.solde_cpte) }}</td>
                <td class="num">{{ formatMoney(row.montant_echeance_m) }}</td>
                <td><span class="badge" :class="statusClass(row.status_ech)">{{ statusLabel(row.status_ech) }}</span></td>
              </tr>
              <tr v-if="!agencyPageRows.length">
                <td colspan="21" class="empty">Aucun dossier pour cette agence.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer v-if="agencyPageCount > 1" class="pager">
          <button type="button" :disabled="agencyPage <= 1" @click="agencyPage -= 1">Précédent</button>
          <span>{{ agencyPage }} / {{ agencyPageCount }}</span>
          <button type="button" :disabled="agencyPage >= agencyPageCount" @click="agencyPage += 1">Suivant</button>
        </footer>
      </section>
    </div>

    <div v-if="view === 'objectif'" class="detail-bar">
      <input
        v-model.trim="objectifQuery"
        type="search"
        placeholder="N° de prêt"
        @input="objectifPage = 1"
      />
    </div>
    <p v-if="view === 'objectif' && objectifWarning" class="banner warn">{{ objectifWarning }}</p>
    <div v-if="view === 'objectif' && objectifRows.length" class="kpis kpis-objectif">
      <article v-for="card in objectifCards" :key="card.label" :style="{ '--accent': card.accent }">
        <span>{{ card.label }}</span>
        <strong>{{ card.money ? formatMoney(card.value) : formatCount(card.value) }}</strong>
        <small v-if="card.money">FCFA</small>
      </article>
    </div>
    <div v-if="view === 'objectif' && filteredObjectifRows.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>N° prêt</th>
            <th>Statut prêt</th>
            <th class="num">Exigible M-1</th>
            <th class="num">Montant échéance</th>
            <th class="num">Objectif recouvrement</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in objectifPageRows" :key="`${row.account_number}-${index}`">
            <td>{{ row.account_number || '—' }}</td>
            <td>{{ row.statut_pret || '—' }}</td>
            <td class="num">{{ formatMoney(row.exigible_m_1) }}</td>
            <td class="num">{{ formatMoney(row.montant_echeance) }}</td>
            <td class="num">{{ formatMoney(row.objectif_recouvrement) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <footer v-if="view === 'objectif' && objectifPageCount > 1" class="pager">
      <button type="button" :disabled="objectifPage <= 1" @click="objectifPage -= 1">Précédent</button>
      <span>{{ objectifPage }} / {{ objectifPageCount }} — {{ formatCount(filteredObjectifRows.length) }} lignes</span>
      <button type="button" :disabled="objectifPage >= objectifPageCount" @click="objectifPage += 1">Suivant</button>
    </footer>
  </section>
</template>

<script>
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  DoughnutController,
  ArcElement,
} from 'chart.js';
import { userFacingError } from '../utils/userFacingError.js';

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  DoughnutController,
  ArcElement,
);

const AGENCY_SERIES = [
  { key: 'realise', label: 'Réalisé', color: '#86efac' },
  { key: 'reste', label: 'Reste', color: '#1a4d3a' },
];

function formatAxis(value) {
  const amount = Number(value) || 0;
  if (Math.abs(amount) >= 1e9) {
    return `${(amount / 1e9).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} Md`;
  }
  if (Math.abs(amount) >= 1e6) {
    return `${(amount / 1e6).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} M`;
  }
  return amount.toLocaleString('fr-FR');
}

function agencyLabel(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/(^|[\s-])([a-zàâäéèêëïîôùûüç])/g, (_match, sep, letter) => sep + letter.toUpperCase());
}

const barLabels = {
  id: 'echeanceBarLabels',
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const { datasets } = chart.data;
    const count = chart.data.labels.length;
    ctx.save();
    ctx.font = '700 11px Segoe UI, sans-serif';
    ctx.fillStyle = '#2563eb';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (let index = 0; index < count; index += 1) {
      const total = datasets.reduce((sum, dataset) => sum + (Number(dataset.data[index]) || 0), 0);
      if (!total) continue;
      let top = null;
      let x = null;
      datasets.forEach((dataset, datasetIndex) => {
        if (!(Number(dataset.data[index]) || 0)) return;
        const bar = chart.getDatasetMeta(datasetIndex).data[index];
        if (!bar) return;
        if (top === null || bar.y < top) {
          top = bar.y;
          x = bar.x;
        }
      });
      if (top === null) continue;
      ctx.fillText(formatAxis(total), x, top - 4);
    }
    ctx.restore();
  },
};

const PAGE_SIZE = 40;
const MONTHS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
];

export default {
  name: 'SuiviEcheanceSection',
  data() {
    const now = new Date();
    const year = now.getFullYear();
    return {
      loading: false,
      error: '',
      rows: [],
      periodLabel: '',
      year,
      month: now.getMonth() + 1,
      years: [year, year - 1, year - 2],
      warning: '',
      snapshotLabel: '',
      view: 'dashboard',
      search: '',
      selectedAgency: '',
      agencyQuery: '',
      agencyPage: 1,
      objectifRows: [],
      objectifWarning: '',
      objectifQuery: '',
      objectifPage: 1,
      activeKpi: '',
      kpiQuery: '',
      kpiPage: 1,
      agence: '',
      caf: '',
      status: '',
      week: '',
      page: 1,
    };
  },
  created() {
    this.donutChart = null;
    this.barChart = null;
  },
  watch: {
    chartSignature: {
      handler() {
        this.destroyCharts();
        if (this.view !== 'dashboard') return;
        this.renderCharts();
      },
      flush: 'post',
    },
  },
  computed: {
    monthOptions() {
      return MONTHS.map((label, index) => ({ value: index + 1, label }));
    },
    objectifLoanIds() {
      const ids = new Set();
      this.objectifRows.forEach((row) => {
        const id = this.loanKey(row.account_number);
        if (id) ids.add(id);
      });
      return ids;
    },
    tombeRows() {
      const excluded = new Set();
      this.rows.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id || row.schedule_due_date) return;
        if (String(row.statut_declassement || '').trim().toUpperCase() !== 'NORM') return;
        excluded.add(id);
      });
      if (!excluded.size) return this.rows;
      return this.rows.filter((row) => !excluded.has(this.loanKey(row.no_pret)));
    },
    rowsInObjectif() {
      const ids = this.objectifLoanIds;
      if (!ids.size) return [];
      return this.tombeRows.filter((row) => ids.has(this.loanKey(row.no_pret)) && this.hasObjectif(row));
    },
    suiviByLoan() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id || map.has(id)) return;
        map.set(id, row);
      });
      return map;
    },
    objectifByLoan() {
      const map = new Map();
      this.objectifRows.forEach((row) => {
        const id = this.loanKey(row.account_number);
        if (!id) return;
        const current = map.get(id) || { exigible: null, echeance: 0 };
        if (current.exigible === null) current.exigible = Number(row.exigible_m_1) || 0;
        current.echeance += Number(row.montant_echeance) || 0;
        map.set(id, current);
      });
      const totals = new Map();
      map.forEach((item, id) => totals.set(id, item.exigible + item.echeance));
      return totals;
    },
    agencyOptions() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        if (!row.code_agence || map.has(row.code_agence)) return;
        map.set(row.code_agence, `${row.code_agence} — ${row.nom_agence || row.code_agence}`);
      });
      return [...map.entries()]
        .map(([code, label]) => ({ code, label }))
        .sort((a, b) => a.label.localeCompare(b.label, 'fr'));
    },
    cafOptions() {
      return [...new Set(this.rowsInObjectif.map((row) => row.charge_affaire).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, 'fr'));
    },
    filteredRows() {
      const query = this.search.toLowerCase();
      return this.rowsInObjectif.filter((row) => {
        if (this.agence && row.code_agence !== this.agence) return false;
        if (this.caf && row.charge_affaire !== this.caf) return false;
        if (this.status === 'none' && row.status_ech) return false;
        if (this.status && this.status !== 'none' && row.status_ech !== this.status) return false;
        if (this.week && this.weekOf(row) !== this.week) return false;
        if (!query) return true;
        return [
          row.no_pret,
          row.nom_client,
          row.matricule_client,
          row.compte,
          row.charge_affaire,
          row.code_gestion_pret,
          row.code_agence,
          row.nom_agence,
          row.type_pret,
        ].filter(Boolean).join(' ').toLowerCase().includes(query);
      });
    },
    pageCount() {
      return Math.max(1, Math.ceil(this.filteredRows.length / PAGE_SIZE));
    },
    pageRows() {
      const start = (this.page - 1) * PAGE_SIZE;
      return this.filteredRows.slice(start, start + PAGE_SIZE);
    },
    weekSeries() {
      return AGENCY_SERIES;
    },
    chartSignature() {
      const total = this.filteredRows.reduce(
        (sum, row) => sum + (Number(row.mt_global_due_a_date) || 0),
        0,
      );
      return `${this.view}|${this.filteredRows.length}|${total}|${this.agence}|${this.caf}|${this.status}|${this.week}|${this.search}`;
    },
    statusSlices() {
      const counts = { I: 0, R: 0, A: 0, none: 0 };
      this.filteredRows.forEach((row) => {
        const key = row.status_ech || 'none';
        counts[key] = (counts[key] || 0) + 1;
      });
      return [
        { key: 'I', label: 'Impayé', color: '#dc2626', value: counts.I },
        { key: 'R', label: 'Remboursé', color: '#15803d', value: counts.R },
        { key: 'A', label: 'En attente', color: '#d97706', value: counts.A },
        { key: 'none', label: 'Sans échéance', color: '#94a3b8', value: counts.none },
      ].filter((slice) => slice.value > 0);
    },
    statusTotal() {
      return this.statusSlices.reduce((sum, slice) => sum + slice.value, 0);
    },
    weekCards() {
      const buckets = [
        { key: 'S1', label: 'S1', range: '1 – 7', tombe: 0, realise: 0, count: 0 },
        { key: 'S2', label: 'S2', range: '8 – 14', tombe: 0, realise: 0, count: 0 },
        { key: 'S3', label: 'S3', range: '15 – 21', tombe: 0, realise: 0, count: 0 },
        { key: 'S4', label: 'S4', range: '22 – 31', tombe: 0, realise: 0, count: 0 },
      ];
      const byKey = Object.fromEntries(buckets.map((item) => [item.key, item]));
      this.rowsInObjectif.forEach((row) => {
        if (this.agence && row.code_agence !== this.agence) return;
        if (this.caf && row.charge_affaire !== this.caf) return;
        const key = this.weekOf(row);
        if (!key || !byKey[key]) return;
        const paye = Number(row.montant_echeance_paye) || 0;
        const reste = Number(row.montant_echeance_m) || 0;
        byKey[key].tombe += paye + reste;
        if (this.realiseMatchesObjectif(row)) byKey[key].realise += paye;
        byKey[key].count += 1;
      });
      return buckets.map((item) => ({
        ...item,
        rate: item.tombe > 0 ? Math.min(100, (item.realise / item.tombe) * 100) : 0,
      }));
    },
    agencyBars() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        if (this.agence && row.code_agence !== this.agence) return;
        if (this.caf && row.charge_affaire !== this.caf) return;
        if (this.week && this.weekOf(row) !== this.week) return;
        if (!row.schedule_due_date) return;
        const code = row.code_agence || '—';
        const name = agencyLabel(String(row.nom_agence || code).replace(/^AGENCE\s+/i, ''));
        if (!map.has(code)) map.set(code, { key: code, label: name, tombe: 0, realise: 0, reste: 0 });
        const item = map.get(code);
        const paye = Number(row.montant_echeance_paye) || 0;
        const reste = Number(row.montant_echeance_m) || 0;
        item.tombe += paye + reste;
        if (this.realiseMatchesObjectif(row)) item.realise += paye;
      });
      return [...map.values()]
        .map((item) => ({ ...item, reste: Math.max(0, item.tombe - item.realise) }))
        .sort((left, right) => right.tombe - left.tombe || left.label.localeCompare(right.label, 'fr'));
    },
    agencyChartWidth() {
      return `${Math.max(this.agencyBars.length * 88, 640)}px`;
    },
    selectedAgencyRow() {
      return this.agencyBars.find((row) => row.key === this.selectedAgency) || null;
    },
    agencyDetailRows() {
      if (!this.selectedAgency) return [];
      const query = this.agencyQuery.toLowerCase();
      return this.rowsInObjectif.filter((row) => {
        if ((row.code_agence || '—') !== this.selectedAgency) return false;
        if (this.caf && row.charge_affaire !== this.caf) return false;
        if (this.week && this.weekOf(row) !== this.week) return false;
        if (!query) return true;
        return [
          row.no_pret,
          row.nom_client,
          row.matricule_client,
          row.compte,
          row.charge_affaire,
          row.code_gestion_pret,
        ].filter(Boolean).join(' ').toLowerCase().includes(query);
      });
    },
    agencyPageCount() {
      return Math.max(1, Math.ceil(this.agencyDetailRows.length / PAGE_SIZE));
    },
    agencyPageRows() {
      const start = (this.agencyPage - 1) * PAGE_SIZE;
      return this.agencyDetailRows.slice(start, start + PAGE_SIZE);
    },
    filteredObjectifRows() {
      const query = this.objectifQuery.toLowerCase();
      if (!query) return this.objectifRows;
      return this.objectifRows.filter((row) => (row.account_number || '').toLowerCase().includes(query));
    },
    objectifPageCount() {
      return Math.max(1, Math.ceil(this.filteredObjectifRows.length / PAGE_SIZE));
    },
    objectifPageRows() {
      const start = (this.objectifPage - 1) * PAGE_SIZE;
      return this.filteredObjectifRows.slice(start, start + PAGE_SIZE);
    },
    objectifCards() {
      const seen = new Set();
      let exigible = 0;
      let echeance = 0;
      this.filteredObjectifRows.forEach((row) => {
        echeance += Number(row.montant_echeance) || 0;
        const id = row.account_number;
        if (!id || seen.has(id)) return;
        seen.add(id);
        exigible += Number(row.exigible_m_1) || 0;
      });
      return [
        { label: 'Prêts financés', value: seen.size, money: false, accent: '#1a4d3a' },
        { label: 'Exigible M-1', value: exigible, money: true, accent: '#7c3aed' },
        { label: 'Montant échéance', value: echeance, money: true, accent: '#2563eb' },
        { label: 'Objectif recouvrement', value: exigible + echeance, money: true, accent: '#143d2e' },
      ];
    },
    activeKpiCard() {
      return this.kpiCards.find((card) => card.key === this.activeKpi) || null;
    },
    dossiersByLoan() {
      const map = new Map();
      this.filteredRows.forEach((row) => {
        const id = row.no_pret;
        if (!id) return;
        if (!map.has(id)) map.set(id, []);
        map.get(id).push(row);
      });
      return map;
    },
    suiviMetrics() {
      const rows = this.filteredRows;
      const withDue = rows.filter((row) => row.schedule_due_date);
      const sum = (list, key) => list.reduce((total, row) => total + (Number(row[key]) || 0), 0);
      const seen = new Set();
      let objectif = 0;
      this.objectifRows.forEach((row) => {
        const id = this.loanKey(row.account_number);
        if (!id || seen.has(id) || !this.hasObjectif(row)) return;
        seen.add(id);
        objectif += Number(this.objectifOf(row)) || 0;
      });
      const realise = sum(withDue.filter((row) => this.realiseMatchesObjectif(row)), 'montant_echeance_paye');
      const taux = objectif ? (realise / objectif) * 100 : 0;
      let attente = 0;
      const lateLoans = new Set();
      this.dossiersByLoan.forEach((items) => {
        if (items.some((row) => row.status_ech === 'A')) attente += 1;
      });
      withDue.forEach((row) => {
        if (!this.hasEcartObjectif(row)) return;
        const id = this.loanKey(row.no_pret);
        if (id) lateLoans.add(id);
      });
      const retard = lateLoans.size;
      return {
        objectif,
        realise,
        attente,
        retard,
        global: this.sumOncePerLoan(rows, 'etat_exigible_m_1')
          + this.sumOncePerLoan(rows, 'total_charge')
          + sum(withDue, 'montant_echeance_m'),
        taux,
      };
    },
    kpiAmountLabel() {
      if (this.activeKpi === 'global') return 'Global dû';
      return 'MT recouvré';
    },
    kpiDetailRows() {
      const query = this.kpiQuery.toLowerCase();
      let rows = [];
      if (this.activeKpi === 'objectif') {
        rows = this.objectifRows.filter((row) => this.hasObjectif(row));
      } else if (this.activeKpi === 'global') {
        rows = this.filteredRows.filter((row) => this.hasObjectif(row) && (Number(row.mt_global_due_a_date) || 0) !== 0);
      } else if (this.activeKpi === 'realise') {
        rows = this.filteredRows.filter((row) => row.schedule_due_date && this.realiseMatchesObjectif(row));
      } else if (this.activeKpi === 'retard') {
        rows = this.filteredRows.filter((row) => this.hasEcartObjectif(row));
      } else if (this.activeKpi === 'attente') {
        const loans = [];
        this.dossiersByLoan.forEach((items) => {
          const head = items.find((row) => row.status_ech === 'A');
          if (head) loans.push(head);
        });
        rows = loans;
      }
      if (!query) return rows;
      return rows.filter((row) => [
        row.account_number,
        row.no_pret,
        row.nom_client,
        row.matricule_client,
        row.code_agence,
        row.nom_agence,
        row.compte,
        row.statut_pret,
        row.statut_declassement,
      ].filter(Boolean).join(' ').toLowerCase().includes(query));
    },
    kpiPageCount() {
      return Math.max(1, Math.ceil(this.kpiDetailRows.length / PAGE_SIZE));
    },
    kpiPageRows() {
      const start = (this.kpiPage - 1) * PAGE_SIZE;
      return this.kpiDetailRows.slice(start, start + PAGE_SIZE);
    },
    kpiCards() {
      const metrics = this.suiviMetrics;
      return [
        {
          key: 'objectif',
          label: 'Objectif de recouvrement',
          value: metrics.objectif,
          money: true,
          unit: 'FCFA',
          accent: '#059669',
        },
        {
          key: 'global',
          label: 'Global dû à date',
          value: metrics.global,
          money: true,
          unit: 'FCFA',
          accent: '#0284c7',
        },
        {
          key: 'realise',
          label: 'Réalisé du mois',
          value: metrics.realise,
          money: true,
          unit: 'MT recouvré',
          accent: '#16a34a',
        },
        {
          key: 'attente',
          label: 'En attente',
          value: metrics.attente,
          money: false,
          unit: 'dossiers',
          accent: '#f59e0b',
        },
        {
          key: 'retard',
          label: 'En retard',
          value: metrics.retard,
          money: false,
          unit: 'dossiers',
          accent: '#ef4444',
        },
      ];
    },
    formulaCards() {
      const metrics = this.suiviMetrics;
      return [
        {
          key: 'taux',
          label: 'Taux de réalisation',
          value: metrics.taux,
          percent: true,
          unit: 'réalisé',
          accent: '#7c3aed',
        },
      ];
    },
  },
  mounted() {
    this.load();
  },
  updated() {
    const canvas = this.$refs.barCanvas;
    if (!canvas || this.view !== 'dashboard' || !this.agencyBars.length) return;
    if (Chart.getChart(canvas)) return;
    this.renderBars();
  },
  beforeUnmount() {
    this.destroyCharts();
  },
  methods: {
    weekOf(row) {
      const text = String(row?.schedule_due_date || '');
      const match = text.match(/(\d{4})-(\d{2})-(\d{2})/);
      const day = match ? Number(match[3]) : 0;
      if (!day) return '';
      if (day <= 7) return 'S1';
      if (day <= 14) return 'S2';
      if (day <= 21) return 'S3';
      return 'S4';
    },
    realiseMatchesObjectif(row) {
      const objectif = Math.round(Number(this.objectifOf(row)) || 0);
      const realise = Math.round(Number(row?.montant_echeance_paye) || 0);
      const status = String(row?.status_ech || '').trim().toUpperCase();
      return objectif > 0 && objectif === realise && status !== 'I';
    },
    hasEcartObjectif(row) {
      const objectif = Math.round(Number(this.objectifOf(row)) || 0);
      if (objectif <= 0 || !row?.schedule_due_date) return false;
      if (String(row?.status_ech || '').trim().toUpperCase() === 'I') return true;
      return Math.round(Number(row.montant_echeance_paye) || 0) !== objectif;
    },
    kpiIcon(key) {
      const paths = {
        objectif: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
        global: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
        realise: '<path d="M20 7L9 18l-5-5"/>',
        attente: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>',
        retard: '<path d="M12 4l8 14H4L12 4z"/><path d="M12 10v4M12 16h.01"/>',
        taux: '<path d="M19 5L5 19"/><circle cx="7.5" cy="7.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/>',
      };
      const body = paths[key] || paths.objectif;
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
    },
    formatKpi(card) {
      if (!card) return '—';
      if (card.percent) return this.formatPercent(card.value);
      if (card.money === false) return this.formatCount(card.value);
      return this.formatMoney(card.value);
    },
    openKpi(key) {
      if (key === 'objectif') {
        this.activeKpi = '';
        this.view = 'objectif';
        this.objectifQuery = '';
        this.objectifPage = 1;
        return;
      }
      this.activeKpi = key;
      this.kpiQuery = '';
      this.kpiPage = 1;
    },
    closeKpi() {
      this.activeKpi = '';
      this.kpiQuery = '';
      this.kpiPage = 1;
    },
    kpiAmount(row) {
      if (this.activeKpi === 'global') return row.mt_global_due_a_date;
      if (this.activeKpi === 'realise') return row.montant_echeance_paye;
      if (this.activeKpi === 'attente') return row.montant_echeance_m;
      return row.exigible_ech;
    },
    destroyCharts() {
      if (this.donutChart) {
        this.donutChart.destroy();
        this.donutChart = null;
      }
      if (this.barChart) {
        this.barChart.destroy();
        this.barChart = null;
      }
    },
    renderCharts() {
      this.renderBars();
      this.renderDonut();
    },
    renderDonut() {
      const canvas = this.$refs.donutCanvas;
      if (!canvas || !this.statusSlices.length) return;
      this.donutChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          labels: this.statusSlices.map((slice) => slice.label),
          datasets: [{
            data: this.statusSlices.map((slice) => slice.value),
            backgroundColor: this.statusSlices.map((slice) => slice.color),
            borderColor: '#fff',
            borderWidth: 3,
            hoverOffset: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '66%',
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const value = context.parsed || 0;
                  const share = this.statusTotal ? Math.round((value / this.statusTotal) * 100) : 0;
                  return ` ${context.label} : ${this.formatCount(value)} (${share} %)`;
                },
              },
            },
          },
        },
      });
    },
    renderBars() {
      const canvas = this.$refs.barCanvas;
      const rows = this.agencyBars;
      if (!canvas || !rows.length) return;
      const existing = Chart.getChart(canvas);
      if (existing) existing.destroy();
      const width = Math.max(rows.length * 88, 640);
      const height = 360;
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      this.barChart = new Chart(canvas, {
        type: 'bar',
        plugins: [barLabels],
        data: {
          labels: rows.map((row) => row.label),
          datasets: AGENCY_SERIES.map((serie) => ({
            label: serie.label,
            data: rows.map((row) => row[serie.key] || 0),
            backgroundColor: serie.color,
            stack: 'echeance',
            maxBarThickness: 46,
            borderWidth: 0,
          })),
        },
        options: {
          responsive: false,
          animation: false,
          layout: { padding: { top: 22 } },
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const value = Number(context.parsed.y) || 0;
                  if (!value) return null;
                  return ` ${context.dataset.label} : ${formatAxis(value)}`;
                },
                footer: (items) => {
                  const total = items.reduce((sum, item) => sum + (Number(item.parsed.y) || 0), 0);
                  return `Tombé : ${formatAxis(total)}`;
                },
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              grid: { display: false },
              ticks: {
                color: '#64748b',
                maxRotation: 0,
                autoSkip: false,
                font: { size: 11 },
                callback(value) {
                  const label = String(this.getLabelForValue(value) || '');
                  const words = label.split(/\s+/).filter(Boolean);
                  if (words.length < 2) return label;
                  const mid = Math.ceil(words.length / 2);
                  return [words.slice(0, mid).join(' '), words.slice(mid).join(' ')];
                },
              },
            },
            y: {
              stacked: true,
              beginAtZero: true,
              ticks: { color: '#64748b', callback: (value) => formatAxis(value) },
              grid: { color: '#e8eef5' },
              border: { display: false },
            },
          },
        },
      });
    },
    sumOncePerLoan(rows, key) {
      const seen = new Set();
      return rows.reduce((total, row) => {
        const id = row.no_pret || row.compte;
        if (!id || seen.has(id)) return total;
        seen.add(id);
        return total + (Number(row[key]) || 0);
      }, 0);
    },
    async load() {
      this.loading = true;
      this.error = '';
      this.warning = '';
      this.objectifWarning = '';
      this.page = 1;
      this.objectifPage = 1;
      const params = { year: this.year, month: this.month };
      try {
        const [suiviResult, objectifResult] = await Promise.allSettled([
          window.axios.get('/api/oracle/data/suivi-echeance', { params }),
          window.axios.get('/api/oracle/data/objectif-recouvrement', { params }),
        ]);
        if (suiviResult.status === 'fulfilled') {
          const payload = suiviResult.value.data || {};
          this.rows = Array.isArray(payload.rows) ? payload.rows : [];
          this.periodLabel = payload.period?.label || '';
          this.warning = payload.warning || '';
          this.snapshotLabel = payload.snapshot?.jour
            ? this.formatDate(payload.snapshot.jour)
            : '';
        } else {
          this.rows = [];
          this.periodLabel = '';
          this.warning = '';
          this.snapshotLabel = '';
          this.error = userFacingError(suiviResult.reason, 'Le suivi échéance n\'a pas pu être chargé.');
        }
        if (objectifResult.status === 'fulfilled') {
          const payload = objectifResult.value.data || {};
          this.objectifRows = Array.isArray(payload.rows) ? payload.rows : [];
          this.objectifWarning = payload.warning || '';
        } else {
          this.objectifRows = [];
          this.objectifWarning = userFacingError(
            objectifResult.reason,
            'L\'objectif de recouvrement n\'a pas pu être chargé.',
          );
        }
      } finally {
        this.loading = false;
      }
    },
    loanKey(value) {
      return String(value || '').trim().toUpperCase();
    },
    objectifOf(row) {
      const id = this.loanKey(row?.no_pret || row?.account_number);
      if (!id || !this.objectifByLoan.has(id)) return null;
      return this.objectifByLoan.get(id);
    },
    hasObjectif(row) {
      return (Number(this.objectifOf(row)) || 0) > 0;
    },
    lineOf(row) {
      if (row?.no_pret) return row;
      return this.suiviByLoan.get(this.loanKey(row?.account_number)) || row || {};
    },
    rowKey(row) {
      return `${row.no_pret}-${row.numero_echeance || 'x'}-${row.schedule_due_date || 'nodue'}-${row.date_deblocage || ''}`;
    },
    statusLabel(status) {
      if (status === 'I') return 'Impayé';
      if (status === 'R') return 'Remboursé';
      if (status === 'A') return 'Échéance A';
      return 'Sans échéance';
    },
    statusClass(status) {
      if (status === 'I') return 'is-late';
      if (status === 'R') return 'is-paid';
      if (status === 'A') return 'is-wait';
      return 'is-empty';
    },
    openAgency(row) {
      if (this.selectedAgency === row.key) {
        this.closeAgency();
        return;
      }
      this.selectedAgency = row.key;
      this.agencyQuery = '';
      this.agencyPage = 1;
    },
    closeAgency() {
      this.selectedAgency = '';
      this.agencyQuery = '';
      this.agencyPage = 1;
    },
    formatCompact(value) {
      return formatAxis(value);
    },
    agencyRate(row) {
      const tombe = Number(row?.tombe) || 0;
      if (!tombe) return 0;
      return ((Number(row.realise) || 0) / tombe) * 100;
    },
    formatCount(value) {
      return new Intl.NumberFormat('fr-FR').format(value || 0);
    },
    formatMoney(value) {
      if (value === null || value === undefined || value === '') return '—';
      const amount = Number(value);
      if (!Number.isFinite(amount)) return '—';
      return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(amount);
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '') return '—';
      const amount = Number(value);
      if (!Number.isFinite(amount)) return '—';
      return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(amount)} %`;
    },
    formatDate(value) {
      if (!value) return '—';
      const text = String(value);
      if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
        const [year, month, day] = text.slice(0, 10).split('-');
        return `${day}/${month}/${year}`;
      }
      return text;
    },
    exportCsv() {
      const headers = [
        'N° prêt', 'Matricule', 'Client', 'Compte', 'Objectif', 'Global dû', 'Réalisé du mois',
        'Déblocage', 'Capital accordé', 'Encours total', '% remboursé', 'Statut prêt',
        'Statut déclassement', 'Code gestion', 'CAF', 'Solde dépôt garantie', 'Date échéance',
        'N° échéance', 'Solde compte', 'Montant échéance', 'Statut échéance',
      ];
      const lines = this.filteredRows.map((row) => [
        row.no_pret, row.matricule_client, row.nom_client, row.compte,
        this.objectifOf(row), row.mt_global_due_a_date, row.montant_echeance_paye,
        row.date_deblocage, row.montant_capital_accorde, row.encours_total,
        row.pourcentage_remboursement, row.statut_pret, row.statut_declassement,
        row.code_gestion_pret, row.charge_affaire, row.solde_depot_garantie,
        row.schedule_due_date, row.numero_echeance, row.solde_cpte,
        row.montant_echeance_m, this.statusLabel(row.status_ech),
      ]);
      const csv = [headers, ...lines]
        .map((line) => line.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join(';'))
        .join('\n');
      const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `suivi-echeance-${this.year}-${String(this.month).padStart(2, '0')}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    },
  },
};
</script>

<style scoped>
.echeance {
  padding: 0.75rem 1.25rem 2rem;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #e3eee8;
  border-radius: 16px;
}

.head-top,
.filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.head h2 {
  margin: 0;
  flex: 0 0 auto;
  font-size: 1.2rem;
  color: #111827;
  white-space: nowrap;
}

.segment {
  display: flex;
  flex: 0 0 auto;
  height: 40px;
  margin-left: 8px;
  padding: 3px;
  background: #f3f6f4;
  border-radius: 10px;
}

.segment button {
  border: 0;
  background: transparent;
  color: #4d6158;
  font-weight: 700;
  font-size: 13px;
  padding: 0 18px;
  border-radius: 8px;
  cursor: pointer;
}

.segment button.on {
  background: #1a4d3a;
  color: #fff;
}

.chip {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 30px 0 12px;
  background: #f3f6f4 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%236b7c74' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") right 10px center no-repeat;
  border-radius: 10px;
}

.chip-year,
.chip-month { flex: 0 0 auto; margin-left: 0; }
.chip-year { margin-left: auto; }

.filters .chip { flex: 1 1 0; min-width: 0; }

.chip span {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  color: #6b7c74;
}

.chip select {
  flex: 1 1 auto;
  width: auto;
  min-width: 4.5rem;
  height: 100%;
  border: 0;
  background: transparent;
  color: #1c2b24;
  font-size: 13px;
  font-weight: 600;
  padding: 0;
  appearance: none;
  cursor: pointer;
}

.refresh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 10px;
  background: #1a4d3a;
  color: #fff;
  cursor: pointer;
}

.refresh svg { width: 16px; height: 16px; }
.refresh:disabled { opacity: 0.65; cursor: wait; }

.detail-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

input[type="search"],
.btn {
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  font-size: 0.875rem;
  color: #111827;
}

input[type="search"] {
  flex: 1;
  min-width: 220px;
  padding: 0 0.75rem;
}

.btn {
  padding: 0 0.9rem;
  cursor: pointer;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpis-objectif {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 14px;
}


.kpis article {
  background: #fff;
  border: 1px solid #e4eee8;
  border-top: 3px solid var(--accent, #1a4d3a);
  border-radius: 14px;
  padding: 14px 16px 12px;
  box-shadow: 0 8px 22px rgba(20, 61, 46, 0.04);
}

.kpi-card {
  cursor: pointer;
  text-align: left;
}

.kpi-card:hover,
.kpi-card.on,
.kpi-card:focus-visible {
  border-color: var(--accent, #1a4d3a);
  outline: none;
}

.kpi-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.35);
}

.kpi-panel {
  width: min(1280px, 100%);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: -12px 0 40px rgba(15, 23, 42, 0.16);
}

.kpi-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 18px 20px 8px;
}

.kpi-panel-head p {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1a4d3a;
}

.kpi-panel-head h3 {
  margin: 0;
  font-size: 22px;
  color: #0f2744;
}

.kpi-close {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: #f3f6f4;
  color: #334155;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.kpi-panel-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 8px 20px 12px;
}

.kpi-panel-stats p {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f4f7f5;
}

.kpi-panel-stats span {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  color: #64748b;
}

.kpi-search {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0 20px 12px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.kpi-panel-table {
  flex: 1;
  overflow: auto;
  margin: 0 20px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.kpi-panel .pager {
  padding: 12px 20px 16px;
}

.kpis .kpi-top {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  margin-bottom: 8px;
}

.kpis .kpi-top > span {
  font-size: 14px;
  line-height: 1.2;
  color: var(--accent, #1a4d3a);
}

.kpi-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #fff;
  background: var(--accent, #1a4d3a);
}

.kpi-icon :deep(svg) {
  width: 24px;
  height: 24px;
}

.kpis span {
  display: block;
  color: #6b7c74;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25;
}

.kpis strong {
  display: block;
  font-size: 1.05rem;
  letter-spacing: -0.03em;
  color: #0b1f33;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.kpis small {
  display: block;
  margin-top: 2px;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.banner {
  padding: 0.85rem 1rem;
  border-radius: 8px;
  background: #f9fafb;
  color: #4b5563;
  margin-bottom: 1rem;
}

.banner.error {
  background: #fef2f2;
  color: #b91c1c;
}

.banner.warn {
  background: #fffbeb;
  color: #92400e;
}

.table-wrap {
  overflow: auto;
  max-height: calc(100vh - 280px);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

th,
td {
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
  vertical-align: top;
}

th {
  position: sticky;
  top: 0;
  background: #f3f4f6;
  color: #374151;
  font-weight: 600;
  z-index: 1;
}

.num {
  text-align: right;
}

tbody tr:hover {
  background: #f9fafb;
}

.code {
  display: inline-block;
  margin-right: 0.35rem;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
  background: #ecfdf5;
  color: #065f46;
  font-size: 0.75rem;
  font-weight: 600;
}

.client,
.sub {
  display: block;
}

.sub {
  color: #6b7280;
  font-size: 0.75rem;
}

.badge {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.is-late {
  background: #fee2e2;
  color: #991b1b;
}

.is-paid {
  background: #dcfce7;
  color: #166534;
}

.is-wait {
  background: #fef3c7;
  color: #92400e;
}

.is-empty {
  background: #f3f4f6;
  color: #4b5563;
}

.pager,
.count {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
  color: #4b5563;
  font-size: 0.875rem;
}

.pager button {
  height: 32px;
  padding: 0 0.7rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.pager button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 12px;
  margin-top: 14px;
}

.panel {
  background: #fff;
  border: 1px solid #e4eee8;
  border-radius: 16px;
  padding: 16px;
  min-width: 0;
  box-shadow: 0 8px 24px rgba(20, 61, 46, 0.04);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 12px;
}

.panel-head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #143d2e;
}

.panel-head span {
  font-size: 12px;
  color: #6b7c74;
}

.chart-box { position: relative; min-height: 240px; }
.chart-scroll { overflow-x: auto; }
.chart-box.tall { height: 360px; min-width: 100%; }
.stack-legend { justify-content: center; }

.rank-panel { margin-top: 12px; }
.rank-table { overflow: auto; }
.rank-table table { width: 100%; border-collapse: collapse; }
.rank-table th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7c74;
  padding: 8px 10px;
  border-bottom: 1px solid #e4eee8;
}
.rank-table td {
  padding: 9px 10px;
  border-bottom: 1px solid #f1f5f3;
  color: #143d2e;
  font-size: 13px;
  font-weight: 600;
}
.rank-table th.num,
.rank-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.rank-index {
  width: 36px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.rank-row { cursor: pointer; }
.rank-row:hover td { background: #f4faf6; }
.rank-row.on td { background: #e7f6ee; }
.rank-index.pos-1,
.rank-index.pos-2,
.rank-index.pos-3 { color: #15803d; }
.rank-table td.is-gap,
.rate-cell strong.is-gap { color: #dc2626; }
.agency-detail { margin-top: 12px; }
.agency-detail .detail-bar { margin: 0 0 12px; }
.agency-detail .kpi-close {
  border: 0;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
}
.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
}
.rate-track {
  flex: 1;
  height: 8px;
  border-radius: 99px;
  background: #e8f5ee;
  overflow: hidden;
}
.rate-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #16a34a;
}
.rate-cell strong {
  width: 64px;
  text-align: right;
  font-size: 12px;
  color: #143d2e;
}

.donut-layout {
  display: flex;
  gap: 18px;
  align-items: center;
  min-height: 280px;
}

.donut {
  position: relative;
  width: 230px;
  height: 230px;
  flex-shrink: 0;
}

.donut-center {
  position: absolute;
  inset: 26%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  pointer-events: none;
}

.donut-center strong {
  font-size: 22px;
  font-weight: 800;
  color: #143d2e;
  letter-spacing: -0.03em;
}

.donut-center span {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.legend,
.inline-legend {
  list-style: none;
  margin: 0;
  padding: 0;
}

.legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend li,
.inline-legend li {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.legend-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: #143d2e;
}

.inline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 10px;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.swatch.square {
  width: 14px;
  height: 10px;
  border-radius: 2px;
}

.empty {
  margin: 24px 0;
  color: #6b7c74;
}

@media (max-width: 1100px) {
  .kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .strip p,
  .strip button { flex: 1 1 140px; }
  .grid-2 { grid-template-columns: 1fr; }
  .head-top,
  .filters { flex-wrap: wrap; }
  .chip-year { margin-left: 0; }
  .filters .chip { flex: 1 1 180px; }
}
</style>
