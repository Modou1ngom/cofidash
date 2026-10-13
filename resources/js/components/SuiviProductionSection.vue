<template>
  <section class="suivi">
    <div class="suivi-body">
      <div class="toolbar">
        <div class="segment" role="tablist" aria-label="Période">
          <button type="button" :class="{ on: scope === 'month' }" @click="setScope('month')">Mois</button>
          <button type="button" :class="{ on: scope === 'ytd' }" @click="setScope('ytd')">YTD</button>
        </div>
        <label class="chip chip-year">
          <span>Année</span>
          <select v-model.number="year" @change="load">
            <option v-for="item in years" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label v-if="scope === 'month'" class="chip chip-month">
          <span>Mois</span>
          <select v-model.number="month" @change="load">
            <option v-for="item in monthOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>
        <span class="toolbar-split" aria-hidden="true"></span>
        <label class="chip">
          <span>Agence</span>
          <select v-model="agence" @change="load">
            <option value="">Toutes</option>
            <option v-for="item in agencyOptions" :key="item.code" :value="item.code">{{ item.label }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Secteur</span>
          <select v-model="secteur" @change="load">
            <option value="">Tous</option>
            <option v-for="item in sectorOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Type</span>
          <select v-model="typeCredit" @change="load">
            <option value="">Tous</option>
            <option v-for="item in creditTypes" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
        </label>
        <button type="button" class="table-link" :class="{ on: page === 'table' }" @click="openTable">Tableau</button>
        <button type="button" class="table-link perf-link" :class="{ on: page === 'performance' }" @click="openPerformance">Performance</button>
        <button type="button" class="refresh" :disabled="loading" title="Actualiser" @click="load">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M20 12a8 8 0 1 1-2.2-5.5" stroke-linecap="round" />
            <path d="M20 4v5h-5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <p v-if="error" class="banner error">{{ error }}</p>
      <p v-else-if="loading && !payload" class="banner">Chargement de la production…</p>

      <div v-if="page === 'board'" class="kpi-row">
        <article
          v-for="card in kpiCards"
          :key="card.key"
          class="kpi"
          :class="{ 'kpi-static': !card.clickable }"
          :style="{ '--accent': card.tint }"
          :role="card.clickable ? 'button' : undefined"
          :tabindex="card.clickable ? 0 : undefined"
          :aria-label="card.clickable ? `Détail ${card.title}` : card.title"
          @click="card.clickable && openDetail(card.key)"
          @keydown.enter.prevent="card.clickable && openDetail(card.key)"
        >
          <div class="kpi-head">
            <span class="kpi-icon" v-html="card.icon"></span>
            <span class="kpi-title">{{ card.title }}</span>
          </div>
          <div class="kpi-main">
            <div>
              <p class="kpi-value">{{ formatAmount(card.amount) }}</p>
              <p class="kpi-unit">FCFA</p>
            </div>
            <p
              v-if="card.variation !== undefined"
              class="kpi-evo"
              :class="deltaClass(card.variation)"
              :title="evolutionHint(card.variation)"
            >{{ formatCardEvolution(card.variation) }}</p>
          </div>
        </article>
      </div>

      <div v-if="page === 'board' && activeDetailCard" class="detail-overlay" @click.self="closeDetail">
        <section class="detail" role="dialog" aria-modal="true" :aria-label="activeDetailCard.title">
          <header class="detail-head">
            <div>
              <p class="detail-kicker">Détail de la production</p>
              <h2>{{ activeDetailCard.title }}</h2>
            </div>
            <button type="button" class="detail-close" aria-label="Fermer" @click="closeDetail">×</button>
          </header>
          <div class="detail-stats">
            <p><span>Montant</span><strong>{{ formatMoney(activeDetailCard.amount) }}</strong></p>
            <p><span>Prêts</span><strong>{{ linesLoading ? '…' : detailRows.length.toLocaleString('fr-FR') }}</strong></p>
            <p><span>Part</span><strong>{{ activeDetailCard.shareValue }}</strong></p>
          </div>
          <div class="detail-tabs" role="tablist">
            <button type="button" :class="{ on: detailTab === 'prets' }" @click="setDetailTab('prets')">Prêts</button>
            <button type="button" :class="{ on: detailTab === 'agences' }" @click="setDetailTab('agences')">Agences</button>
            <button type="button" :class="{ on: detailTab === 'secteurs' }" @click="setDetailTab('secteurs')">Secteurs</button>
          </div>
          <label v-if="detailTab === 'prets'" class="detail-search">
            <span>Recherche</span>
            <input v-model="detailQuery" type="search" placeholder="N° de prêt, agence ou secteur" @input="detailPage = 1">
          </label>
          <div class="detail-table-wrap">
            <table v-if="detailTab === 'prets'">
              <thead>
                <tr>
                  <th>N° de prêt</th>
                  <th>Date</th>
                  <th>Agence</th>
                  <th>Secteur</th>
                  <th class="num">Montant</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="linesLoading">
                  <td colspan="5">Chargement des prêts…</td>
                </tr>
                <tr v-for="row in detailPageRows" :key="`${row.pret}-${row.date}`">
                  <td>{{ row.pret || '—' }}</td>
                  <td>{{ formatDate(row.date) }}</td>
                  <td>{{ row.agence }}</td>
                  <td>{{ row.secteur }}</td>
                  <td class="num">{{ formatMoney(row.montant) }}</td>
                </tr>
                <tr v-if="!detailPageRows.length">
                  <td colspan="5" class="detail-empty">Aucun prêt sur cette sélection.</td>
                </tr>
              </tbody>
            </table>
            <table v-else>
              <thead>
                <tr>
                  <th>{{ detailTab === 'agences' ? 'Agence' : 'Secteur' }}</th>
                  <th class="num">Prêts</th>
                  <th class="num">Montant</th>
                  <th class="num">Part</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in detailGroups" :key="row.label">
                  <td>{{ row.label }}</td>
                  <td class="num">{{ row.count.toLocaleString('fr-FR') }}</td>
                  <td class="num">{{ formatMoney(row.total) }}</td>
                  <td class="num">{{ formatShare(row.share) }}</td>
                </tr>
                <tr v-if="!detailGroups.length">
                  <td colspan="4" class="detail-empty">Aucune ligne à afficher.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <footer v-if="detailTab === 'prets' && detailPageCount > 1" class="detail-pager">
            <button type="button" :disabled="detailPage <= 1" @click="detailPage -= 1">Précédent</button>
            <span>{{ detailPage }} / {{ detailPageCount }}</span>
            <button type="button" :disabled="detailPage >= detailPageCount" @click="detailPage += 1">Suivant</button>
          </footer>
        </section>
      </div>

      <section v-if="page === 'table'" class="zone-agencies-section">
        <div class="table-page-head">
          <button type="button" class="back-link" @click="page = 'board'">← Retour</button>
          <h2 class="section-title">Détail de la production par agence et par type de crédit</h2>
        </div>
        <div class="table-container">
          <table v-if="agencyMatrix.length" class="agencies-table">
            <colgroup>
              <col class="w-agence" />
              <col class="w-gest" />
              <col span="8" />
            </colgroup>
            <thead>
              <tr>
                <th class="col-label col-agence">Agence</th>
                <th class="col-label col-gest">CAF</th>
                <th>
                  <span class="th-title">Objectif</span>
                  <span class="th-unit">(FCFA)</span>
                </th>
                <th v-for="type in creditTypes" :key="type.key">
                  <span class="th-title">{{ type.label }}</span>
                  <span class="th-unit">(FCFA)</span>
                </th>
                <th>
                  <span class="th-title">Globale</span>
                  <span class="th-unit">(FCFA)</span>
                </th>
                <th>
                  <span class="th-title">TRO</span>
                  <span class="th-unit">(%)</span>
                </th>
                <th>
                  <span class="th-title">Variation</span>
                  <span class="th-unit">(FCFA)</span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
                <td class="level-1 col-label col-agence">
                  <span class="cell-line">
                    <button type="button" class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">{{ expanded.TERRITOIRE ? '−' : '+' }}</button>
                    <strong>TERRITOIRE</strong>
                  </span>
                </td>
                <td class="col-label col-gest">—</td>
                <td><strong>{{ formatAmount(matrixObjectif) }}</strong></td>
                <td v-for="type in creditTypes" :key="`root-${type.key}`"><strong>{{ formatAmount(matrixTotals[type.key]) }}</strong></td>
                <td><strong>{{ formatAmount(matrixTotals.total) }}</strong></td>
                <td :class="troClass(matrixScore.tro)"><strong>{{ formatTro(matrixScore.tro) }}</strong></td>
                <td :class="deltaClass(matrixScore.variation)"><strong>{{ formatGap(matrixScore.variation) }}</strong></td>
              </tr>
              <template v-if="expanded.TERRITOIRE">
                <template v-for="territory in territoryGroups" :key="territory.key">
                  <tr class="level-2-row" @click="toggleExpand(territory.key)">
                    <td class="level-2 col-label col-agence">
                      <span class="cell-line">
                        <button type="button" class="expand-btn" @click.stop="toggleExpand(territory.key)">{{ expanded[territory.key] ? '−' : '+' }}</button>
                        <span>{{ territory.name }}</span>
                      </span>
                    </td>
                    <td class="col-label col-gest">—</td>
                    <td><strong>{{ formatAmount(territory.objectif) }}</strong></td>
                    <td v-for="type in creditTypes" :key="`${territory.key}-${type.key}`"><strong>{{ formatAmount(territory.totals[type.key]) }}</strong></td>
                    <td><strong>{{ formatAmount(territory.totals.total) }}</strong></td>
                    <td :class="troClass(territory.score.tro)"><strong>{{ formatTro(territory.score.tro) }}</strong></td>
                    <td :class="deltaClass(territory.score.variation)"><strong>{{ formatGap(territory.score.variation) }}</strong></td>
                  </tr>
                  <template v-if="expanded[territory.key]">
                    <template v-for="row in territory.agencies" :key="row.key">
                      <tr class="level-3-row" @click="toggleExpand(row.key)">
                        <td class="level-3 col-label col-agence">
                          <span class="cell-line">
                            <button type="button" class="expand-btn" @click.stop="toggleExpand(row.key)">{{ expanded[row.key] ? '−' : '+' }}</button>
                            <span>{{ row.label }}</span>
                          </span>
                        </td>
                        <td class="col-label col-gest">—</td>
                        <td>{{ formatAmount(row.objectif) }}</td>
                        <td v-for="type in creditTypes" :key="`${row.key}-${type.key}`">{{ formatAmount(row[type.key]) }}</td>
                        <td><strong>{{ formatAmount(row.total) }}</strong></td>
                        <td :class="troClass(row.score.tro)">{{ formatTro(row.score.tro) }}</td>
                        <td :class="deltaClass(row.score.variation)">{{ formatGap(row.score.variation) }}</td>
                      </tr>
                      <template v-if="expanded[row.key]">
                        <tr v-for="caf in row.cafs" :key="caf.key" class="level-4-row">
                          <td class="level-4 col-label col-agence"><span class="agency-code">{{ row.key }}</span></td>
                          <td class="col-label col-gest">{{ caf.label }}</td>
                          <td>{{ formatAmount(caf.objectif) }}</td>
                          <td v-for="type in creditTypes" :key="`${caf.key}-${type.key}`">{{ formatAmount(caf[type.key]) }}</td>
                          <td><strong>{{ formatAmount(caf.total) }}</strong></td>
                          <td :class="troClass(caf.score.tro)">{{ formatTro(caf.score.tro) }}</td>
                          <td :class="deltaClass(caf.score.variation)">{{ formatGap(caf.score.variation) }}</td>
                        </tr>
                      </template>
                    </template>
                  </template>
                </template>
              </template>
              <tr class="total-row">
                <td class="col-label col-agence">Total</td>
                <td class="col-label col-gest">—</td>
                <td>{{ formatAmount(matrixObjectif) }}</td>
                <td v-for="type in creditTypes" :key="`total-${type.key}`">{{ formatAmount(matrixTotals[type.key]) }}</td>
                <td>{{ formatAmount(matrixTotals.total) }}</td>
                <td :class="troClass(matrixScore.tro)">{{ formatTro(matrixScore.tro) }}</td>
                <td :class="deltaClass(matrixScore.variation)">{{ formatGap(matrixScore.variation) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty">Aucune production sur cette période.</p>
        </div>
      </section>

      <section v-if="page === 'performance'" class="zone-agencies-section">
        <div class="table-page-head">
          <button type="button" class="back-link" @click="page = 'board'">← Retour</button>
          <h2 class="section-title">Performance de la production</h2>
        </div>
        <div v-if="bestMarks.length" class="podium">
          <article v-for="mark in bestMarks" :key="mark.key" :class="'is-' + mark.key">
            <span class="podium-ico" v-html="mark.icon"></span>
            <div class="podium-id">
              <p>{{ mark.kicker }}</p>
              <strong>{{ mark.label }}</strong>
            </div>
            <div class="podium-foot">
              <span v-if="mark.amountText">{{ mark.amountText }}</span>
              <em :class="mark.tone">{{ mark.rateText }}</em>
              <small v-if="mark.targetText">Obj. {{ mark.targetText }}</small>
            </div>
            <p v-if="mark.key === 'zone' && otherZones.length" class="zone-follow">
              <span v-for="zone in otherZones" :key="zone.key">{{ zone.short }} {{ formatShare(zone.share) }}</span>
            </p>
          </article>
        </div>
        <div class="perf-grid">
          <article class="panel perf-card is-caf">
            <header class="perf-head">
              <span class="perf-ico is-top" v-html="iconUser"></span>
              <h2>Top 5 des CAF</h2>
            </header>
            <ol v-if="topCafs.length" class="rank-list is-top">
              <li v-for="(row, index) in topCafs" :key="row.key">
                <span class="rank-index" :class="'pos-' + (index + 1)">{{ index + 1 }}</span>
                <div class="rank-id">
                  <span class="rank-name">{{ row.label }}</span>
                  <span v-if="row.hint" class="rank-hint">{{ row.hint }}</span>
                </div>
                <span class="rank-figure">{{ formatCompact(row.total) }}<small :class="row.tro != null ? troClass(row.tro) : ''">{{ row.tro != null ? formatTro(row.tro) : formatShare(row.share) }}</small><small v-if="row.objectif" class="rank-target">Obj. {{ formatCompact(row.objectif) }}</small></span>
              </li>
            </ol>
            <p v-else class="empty">Aucun CAF sur cette période.</p>
          </article>

          <article class="panel perf-card is-caf is-low">
            <header class="perf-head">
              <span class="perf-ico is-flop" v-html="iconUser"></span>
              <h2>Flop 5 des CAF</h2>
            </header>
            <ol v-if="flopCafs.length" class="rank-list is-flop">
              <li v-for="(row, index) in flopCafs" :key="row.key">
                <span class="rank-index">{{ index + 1 }}</span>
                <div class="rank-id">
                  <span class="rank-name">{{ row.label }}</span>
                  <span v-if="row.hint" class="rank-hint">{{ row.hint }}</span>
                </div>
                <span class="rank-figure">{{ formatCompact(row.total) }}</span>
              </li>
            </ol>
            <p v-else class="empty">Pas assez de CAF pour un flop.</p>
          </article>

          <article class="panel perf-card is-agency">
            <header class="perf-head">
              <span class="perf-ico is-top" v-html="iconAgency"></span>
              <h2>Top 5 des agences</h2>
            </header>
            <ol v-if="topAgencies.length" class="rank-list is-top">
              <li v-for="(row, index) in topAgencies" :key="row.key">
                <span class="rank-index" :class="'pos-' + (index + 1)">{{ index + 1 }}</span>
                <div class="rank-id">
                  <span class="rank-name">{{ row.label }}</span>
                  <span v-if="row.hint" class="rank-hint">{{ row.hint }}</span>
                </div>
                <span class="rank-figure">{{ formatCompact(row.total) }}<small :class="row.tro != null ? troClass(row.tro) : ''">{{ row.tro != null ? formatTro(row.tro) : formatShare(row.share) }}</small><small v-if="row.objectif" class="rank-target">Obj. {{ formatCompact(row.objectif) }}</small></span>
              </li>
            </ol>
            <p v-else class="empty">Aucune agence sur cette période.</p>
          </article>

          <article class="panel perf-card is-agency is-low">
            <header class="perf-head">
              <span class="perf-ico is-flop" v-html="iconAgency"></span>
              <h2>Flop 5 des agences</h2>
            </header>
            <ol v-if="flopAgencies.length" class="rank-list is-flop">
              <li v-for="(row, index) in flopAgencies" :key="row.key">
                <span class="rank-index">{{ index + 1 }}</span>
                <div class="rank-id">
                  <span class="rank-name">{{ row.label }}</span>
                  <span v-if="row.hint" class="rank-hint">{{ row.hint }}</span>
                </div>
                <span class="rank-figure">{{ formatCompact(row.total) }}</span>
              </li>
            </ol>
            <p v-else class="empty">Pas assez d’agences pour un flop.</p>
          </article>

        </div>
      </section>

      <div v-if="page === 'board'" class="grid-2">
        <article class="panel">
          <header class="panel-head">
            <h2>Production par agence</h2>
          </header>
          <div v-if="agencyStacks.length" class="chart-scroll">
            <div class="chart-box tall" :style="{ width: agencyChartWidth }">
              <canvas ref="barCanvas"></canvas>
            </div>
          </div>
          <ul v-if="agencyStacks.length" class="inline-legend stack-legend">
            <li v-for="type in creditTypes" :key="type.key">
              <span class="swatch square" :style="{ background: type.color }"></span>
              {{ type.stackLabel }}
            </li>
          </ul>
          <p v-else class="empty">Aucune production sur cette période.</p>
        </article>

        <article class="panel">
          <header class="panel-head">
            <h2>Répartition de la production par secteur d'activité</h2>
          </header>
          <div v-if="sectorSlices.length" class="donut-layout">
            <div class="donut">
              <canvas ref="donutCanvas"></canvas>
              <div class="donut-center">
                <strong>{{ formatAmount(sectorTotal) }}</strong>
                <span>FCFA</span>
              </div>
            </div>
            <ul class="legend">
              <li v-for="slice in sectorSlices" :key="slice.label">
                <span class="swatch" :style="{ background: slice.color }"></span>
                <span class="legend-name">{{ slice.label }}</span>
              </li>
            </ul>
          </div>
          <p v-else class="empty">Aucune répartition à afficher.</p>
        </article>
      </div>

      <div v-if="page === 'board'" class="grid-2">
        <article class="panel">
          <header class="panel-head">
            <h2 class="chart-title">Évolution de la production par type de crédit (6 derniers mois)</h2>
          </header>
          <div v-if="months.length" class="chart-box">
            <canvas ref="lineCanvas"></canvas>
          </div>
          <ul v-if="months.length" class="inline-legend">
            <li v-for="type in creditTypes" :key="type.key">
              <span class="swatch" :style="{ background: type.color }"></span>
              {{ type.label }}
            </li>
          </ul>
          <p v-else class="empty">Pas encore d'historique.</p>
        </article>

        <article class="panel">
          <header class="panel-head">
            <h2 class="chart-title">Évolution de la production par famille de crédit (6 derniers mois)</h2>
          </header>
          <div v-if="familleSeries.length" class="chart-box">
            <canvas ref="familleCanvas"></canvas>
          </div>
          <ul v-if="familleSeries.length" class="inline-legend">
            <li v-for="(serie, index) in familleSeries" :key="serie.key">
              <span class="swatch" :style="{ background: familleColor(index) }"></span>
              {{ serie.label }}
            </li>
          </ul>
          <p v-else class="empty">Pas encore d'historique.</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script>
import {
  Chart,
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
  DoughnutController,
  ArcElement,
} from 'chart.js';

Chart.register(
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
  DoughnutController,
  ArcElement,
);

const ICON_DOC = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3.2h6.2L18.8 9v10.6a1.6 1.6 0 0 1-1.6 1.6H7a1.6 1.6 0 0 1-1.6-1.6V4.8A1.6 1.6 0 0 1 7 3.2z"/><path d="M13 3.4V8.6h5.2M8.4 12.4h7.2M8.4 15.6h7.2M8.4 18.4h4.2"/></svg>';
const ICON_REFRESH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 0 1-13.7 5.6L4 16"/><path d="M4 20v-4h4"/><path d="M4 12a8 8 0 0 1 13.7-5.6L20 8"/><path d="M20 4v4h-4"/></svg>';
const ICON_USER = '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="3.4"/><path d="M5.2 19.6c.7-3.5 3.3-5.3 6.8-5.3s6.1 1.8 6.8 5.3a.8.8 0 0 1-.8.9H6a.8.8 0 0 1-.8-.9Z"/></svg>';
const ICON_TARGET = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1" fill="currentColor"/></svg>';

const VILLE = ['territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'];
const BANLIEUE = ['territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'];
const CENTRE = ['territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'];
const NORD = ['territoire_province_nord', 'TERRITOIRE PROVINCE NORD'];
const TERRITORY_TOKENS = [
  ['TAMBACOUNDA', ...CENTRE],
  ['PRINCIPALE POINT E', ...VILLE],
  ['LAMINE GUEYE', ...VILLE],
  ['SAINT LOUIS', ...NORD],
  ['GRAND COMPTE', ...VILLE],
  ['ZINGUINCHOR', ...CENTRE],
  ['ZIGUINCHOR', ...CENTRE],
  ['NIARRY TALLI', ...VILLE],
  ['NIARRY TALLY', ...VILLE],
  ['NIARY TALLY', ...VILLE],
  ['KEUR MASSAR', ...BANLIEUE],
  ['OUROSSOGUI', ...NORD],
  ['GUEDIAWAYE', ...BANLIEUE],
  ['PARCELLES', ...BANLIEUE],
  ['DIOURBEL', ...NORD],
  ['RUFISQUE', ...BANLIEUE],
  ['NGUELAW', ...VILLE],
  ['LINGUERE', ...BANLIEUE],
  ['KAOLACK', ...CENTRE],
  ['MARISTES', ...VILLE],
  ['CASTORS', ...VILLE],
  ['PIKINE', ...BANLIEUE],
  ['MBOUR', ...CENTRE],
  ['THIES', ...CENTRE],
  ['TOUBA', ...NORD],
  ['LOUGA', ...NORD],
  ['POINT E', ...VILLE],
  ['GUEYE', ...VILLE],
  ['SIEGE', ...VILLE],
];

function resolveTerritory(label) {
  const text = String(label || '').toUpperCase().replace(/[-']/g, ' ').replace(/\s+/g, ' ').trim();
  const hit = TERRITORY_TOKENS.find(([token]) => text.includes(token));
  if (!hit) return null;
  return { key: hit[1], name: hit[2] };
}

const TYPES = [
  { key: 'restructure', label: 'Restructure', stackLabel: 'Crédit Restructuré', color: '#22c55e', icon: ICON_DOC },
  { key: 'protocole', label: 'Protocole', stackLabel: 'Crédit Protocole', color: '#7c3aed', icon: ICON_DOC },
  { key: 'rebooker', label: 'Reboocker', stackLabel: 'Reboocker', color: '#f97316', icon: ICON_REFRESH },
  { key: 'simple', label: 'Net', stackLabel: 'Crédit Simple', color: '#14b8a6', icon: ICON_USER },
];

const SLICE_COLORS = ['#2563eb', '#22c55e', '#f97316', '#7c3aed', '#14b8a6', '#94a3b8', '#1A4D3A', '#c6a15b'];
const FAMILLE_COLORS = ['#22c55e', '#f97316', '#7c3aed', '#3b82f6', '#06b6d4', '#94a3b8'];

const donutPercents = {
  id: 'donutPercents',
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const dataset = chart.data.datasets[0];
    const total = dataset.data.reduce((sum, value) => sum + (Number(value) || 0), 0);
    if (!total) return;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.fillStyle = '#fff';
    ctx.font = '700 12px Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    meta.data.forEach((arc, index) => {
      const value = Number(dataset.data[index]) || 0;
      const percent = Math.round((value / total) * 100);
      if (percent < 5) return;
      const point = arc.getCenterPoint();
      ctx.fillText(`${percent}%`, point.x, point.y);
    });
    ctx.restore();
  },
};
const MONTH_NAMES = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];

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

const endLabels = {
  id: 'endLabels',
  afterDatasetsDraw(chart) {
    const { ctx, chartArea } = chart;
    const gap = 14;
    const items = [];
    chart.data.datasets.forEach((dataset, index) => {
      const points = chart.getDatasetMeta(index).data;
      const last = points[points.length - 1];
      const value = Number(dataset.data[dataset.data.length - 1]) || 0;
      if (!last || !value) return;
      items.push({
        text: formatAxis(value),
        x: last.x + 8,
        y: last.y,
        anchor: last.y,
        color: dataset.borderColor,
      });
    });
    if (!items.length) return;
    const top = chartArea.top + 7;
    const bottom = chartArea.bottom - 7;
    items.sort((left, right) => left.y - right.y);
    items[0].y = Math.max(items[0].y, top);
    for (let index = 1; index < items.length; index += 1) {
      items[index].y = Math.max(items[index].y, items[index - 1].y + gap);
    }
    items[items.length - 1].y = Math.min(items[items.length - 1].y, bottom);
    for (let index = items.length - 2; index >= 0; index -= 1) {
      items[index].y = Math.min(items[index].y, items[index + 1].y - gap);
    }
    ctx.save();
    ctx.font = '600 11px Segoe UI, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    items.forEach((item) => {
      if (Math.abs(item.y - item.anchor) > 7) {
        ctx.strokeStyle = item.color;
        ctx.globalAlpha = 0.4;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(item.x - 8, item.anchor);
        ctx.lineTo(item.x - 2, item.y);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
      ctx.fillStyle = item.color;
      ctx.fillText(item.text, item.x, item.y);
    });
    ctx.restore();
  },
};

const barLabels = {
  id: 'barLabels',
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

export default {
  name: 'SuiviProductionSection',
  data() {
    const now = new Date();
    return {
      scope: 'ytd',
      year: now.getFullYear(),
      month: now.getMonth() + 1,
      agence: '',
      secteur: '',
      typeCredit: '',
      loading: false,
      error: '',
      payload: null,
      objectives: [],
      page: 'board',
      iconUser: '<svg viewBox="0 0 32 32"><path d="M10.5 4h4.2l.8 6h-5.8l.8-6z" fill="#5b8def"/><path d="M17.2 4H21.5l.9 6h-6.1l.9-6z" fill="#ef5b4c"/><circle cx="16" cy="18.2" r="8" fill="#f6c445"/><circle cx="16" cy="18.2" r="5.4" fill="none" stroke="#fff4c2" stroke-width="1.4"/><path d="M13.2 15.6l1.7 1.6 3.2-3.3" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
      iconAgency: '<svg viewBox="0 0 32 32"><path d="M8 7h16v7.2a8 8 0 01-16 0V7z" fill="#f6c445"/><path d="M8 9.2H5.2A4.2 4.2 0 009.2 14" fill="none" stroke="#e0a816" stroke-width="1.6" stroke-linecap="round"/><path d="M24 9.2h2.8A4.2 4.2 0 0122.8 14" fill="none" stroke="#e0a816" stroke-width="1.6" stroke-linecap="round"/><path d="M16 22.2v3.2M11.5 27.2h9" fill="none" stroke="#d39b09" stroke-width="1.8" stroke-linecap="round"/></svg>',
      iconZone: '<svg viewBox="0 0 32 32"><path d="M12.2 4.5h7.6L18.6 10h-5.2l-1.2-5.5z" fill="#3b82f6"/><path d="M16 11.2l2.1 4.2 4.6.7-3.3 3.2.8 4.6L16 21.7l-4.2 2.2.8-4.6-3.3-3.2 4.6-.7 2.1-4.2z" fill="#f6c445"/></svg>',
      expanded: { TERRITOIRE: true },
      activeCard: null,
      detailTab: 'prets',
      detailQuery: '',
      detailPage: 1,
      linesLoading: false,
      linesLoaded: false,
      barChart: null,
      lineChart: null,
      familleChart: null,
      donutChart: null,
      creditTypes: TYPES,
      years: [now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2],
      monthOptions: MONTH_NAMES.slice(1).map((label, index) => ({ value: index + 1, label })),
    };
  },
  computed: {
    agencyOptions() {
      return this.payload?.options?.agencies || [];
    },
    sectorOptions() {
      return this.payload?.options?.sectors || [];
    },
    agencies() {
      return this.payload?.agencies || [];
    },
    agencyStacks() {
      return (this.payload?.agency_matrix || [])
        .map((row) => ({
          key: row.key,
          label: String(row.label || '').replace(/^agence\s+/i, '').trim() || row.label,
          total: Number(row.total) || 0,
          restructure: Number(row.restructure) || 0,
          protocole: Number(row.protocole) || 0,
          rebooker: Number(row.rebooker) || 0,
          simple: Number(row.simple) || 0,
        }))
        .sort((left, right) => right.total - left.total);
    },
    agencyChartWidth() {
      return `${Math.max(this.agencyStacks.length * 88, 640)}px`;
    },
    months() {
      return this.payload?.months || [];
    },
    familleSeries() {
      return this.payload?.famille_months?.series || [];
    },
    familleLabels() {
      return this.payload?.famille_months?.labels || [];
    },
    activeDetailCard() {
      if (!this.activeCard) return null;
      return this.kpiCards.find((card) => card.key === this.activeCard) || null;
    },
    detailRows() {
      const rows = this.payload?.lines || [];
      if (!this.activeCard || this.activeCard === 'total') return rows;
      return rows.filter((row) => row.type === this.activeCard);
    },
    detailMatched() {
      const query = this.detailQuery.trim().toLowerCase();
      if (!query) return this.detailRows;
      return this.detailRows.filter((row) => (
        String(row.pret || '').toLowerCase().includes(query)
        || String(row.agence || '').toLowerCase().includes(query)
        || String(row.secteur || '').toLowerCase().includes(query)
      ));
    },
    detailPageCount() {
      return Math.max(1, Math.ceil(this.detailMatched.length / 12));
    },
    detailPageRows() {
      const start = (this.detailPage - 1) * 12;
      return this.detailMatched.slice(start, start + 12);
    },
    detailGroups() {
      const key = this.detailTab === 'agences' ? 'agence' : 'secteur';
      return this.groupLines(this.detailRows, key);
    },
    agencyMatrix() {
      return this.payload?.agency_matrix || [];
    },
    matrixTotals() {
      return this.sumMatrix(this.agencyMatrix);
    },
    matrixObjectif() {
      return this.territoryGroups.reduce((sum, group) => sum + group.objectif, 0);
    },
    matrixScore() {
      return this.score(this.matrixTotals.total, this.matrixObjectif);
    },
    zoneRanks() {
      const total = this.matrixTotals.total || 0;
      return this.territoryGroups
        .map((group) => ({
          key: group.key,
          label: String(group.name || '').replace(/^territoire\s+/i, '').trim() || group.name,
          total: group.totals.total,
          share: total ? (group.totals.total / total) * 100 : 0,
          objectif: this.visibleTarget(group.totals.total, group.objectif),
          tro: this.score(group.totals.total, this.visibleTarget(group.totals.total, group.objectif)).tro,
        }))
        .filter((zone) => zone.total > 0)
        .sort((left, right) => right.total - left.total);
    },
    agencyRanks() {
      const rows = this.territoryGroups.flatMap((group) => group.agencies.map((row) => ({
        key: row.key,
        label: this.agencyShort(row.label),
        hint: String(group.name || '').replace(/^territoire\s+/i, '').trim(),
        total: row.total,
        objectif: this.visibleTarget(row.total, row.objectif),
        tro: this.score(row.total, this.visibleTarget(row.total, row.objectif)).tro,
      })));
      return this.rankEnds(rows);
    },
    cafRanks() {
      const rows = this.territoryGroups.flatMap((group) => group.agencies.flatMap((row) => (row.cafs || []).map((caf) => ({
        key: caf.key,
        label: this.cafDisplayName(caf),
        hint: this.agencyShort(row.label),
        total: caf.total,
        objectif: this.visibleTarget(caf.total, caf.objectif),
        tro: this.score(caf.total, this.visibleTarget(caf.total, caf.objectif)).tro,
      }))));
      return this.rankEnds(rows);
    },
    topAgencies() {
      return this.agencyRanks.top;
    },
    flopAgencies() {
      return this.agencyRanks.flop;
    },
    topCafs() {
      return this.cafRanks.top;
    },
    flopCafs() {
      return this.cafRanks.flop;
    },
    otherZones() {
      return this.zoneRanks.slice(1).map((zone) => ({
        ...zone,
        short: String(zone.label || '').replace(/^province\s+/i, '').trim(),
      }));
    },
    bestMarks() {
      const shown = (row) => {
        if (!row) return null;
        const hasRate = row.tro !== null && row.tro !== undefined && !Number.isNaN(Number(row.tro));
        return {
          label: row.label,
          amountText: this.formatCompact(row.total),
          targetText: row.objectif ? this.formatCompact(row.objectif) : '',
          rateText: hasRate ? this.formatTro(row.tro) : this.formatShare(row.share),
          tone: hasRate ? this.troClass(row.tro) : 'positive',
        };
      };
      return [
        ['caf', 'Meilleur CAF', this.topCafs[0], this.iconUser],
        ['agency', 'Meilleure agence', this.topAgencies[0], this.iconAgency],
        ['zone', 'Meilleur territoire', this.zoneRanks[0], this.iconZone],
      ].flatMap(([key, kicker, row, icon]) => {
        const view = shown(row);
        return view ? [{ key, kicker, icon, ...view }] : [];
      });
    },
    territoryGroups() {
      const order = [
        { key: 'territoire_dakar_ville', name: 'TERRITOIRE DAKAR VILLE' },
        { key: 'territoire_dakar_banlieue', name: 'TERRITOIRE DAKAR BANLIEUE' },
        { key: 'territoire_province_centre_sud', name: 'TERRITOIRE PROVINCE CENTRE-SUD' },
        { key: 'territoire_province_nord', name: 'TERRITOIRE PROVINCE NORD' },
      ];
      const grouped = new Map();
      this.agencyMatrix.forEach((row) => {
        const fromApi = row.territory_key && row.territory_key !== 'non_rattache'
          ? { key: row.territory_key, name: row.territory }
          : null;
        const resolved = fromApi || resolveTerritory(row.label) || { key: 'non_rattache', name: 'NON RATTACHÉ' };
        if (!grouped.has(resolved.key)) {
          grouped.set(resolved.key, { key: resolved.key, name: resolved.name, agencies: [] });
        }
        grouped.get(resolved.key).agencies.push(row);
      });
      const decorate = (group, name) => {
        const agencies = group.agencies.map((row) => {
          const objectif = this.agencyObjectif(row.key, row.label);
          const cafs = (row.cafs || []).map((caf) => {
            const cafObjectif = this.cafObjectif(caf.label);
            return { ...caf, objectif: cafObjectif, score: this.score(caf.total, cafObjectif) };
          });
          return { ...row, objectif, score: this.score(row.total, objectif), cafs };
        });
        const totals = this.sumMatrix(agencies);
        const objectif = this.territoryObjectif(group);
        return { ...group, name, agencies, totals, objectif, score: this.score(totals.total, objectif) };
      };
      const known = order
        .filter((item) => grouped.has(item.key))
        .map((item) => decorate(grouped.get(item.key), item.name));
      const extra = [...grouped.values()]
        .filter((group) => !order.some((item) => item.key === group.key))
        .map((group) => decorate(group, group.name));
      return [...known, ...extra];
    },
    kpiCards() {
      const kpis = this.payload?.kpis || {};
      const cards = [
        {
          key: 'objectif',
          title: 'Objectif',
          tint: '#1a4d3a',
          icon: ICON_TARGET,
          amount: this.objectifAmount(),
          clickable: false,
        },
        {
          key: 'total',
          title: 'Production globale',
          tint: '#2563eb',
          icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.4c-4.6 0-8.2 1.4-8.2 3.2v1.7c0 1.8 3.6 3.2 8.2 3.2s8.2-1.4 8.2-3.2V5.6c0-1.8-3.6-3.2-8.2-3.2Zm0 9.6c-4.6 0-8.2-1.2-8.2-2.6v2.2c0 1.8 3.6 3.2 8.2 3.2s8.2-1.4 8.2-3.2V9.4c0 1.4-3.6 2.6-8.2 2.6Zm0 5.4c-4.6 0-8.2-1.2-8.2-2.6v2.2c0 1.8 3.6 3.2 8.2 3.2s8.2-1.4 8.2-3.2v-2.2c0 1.4-3.6 2.6-8.2 2.6Z"/></svg>',
          amount: kpis.total?.amount || 0,
          variation: kpis.total?.variation_pct,
          shareValue: '100%',
          clickable: true,
        },
      ];
      TYPES.forEach((type) => {
        const item = kpis[type.key] || {};
        cards.push({
          key: type.key,
          title: type.label,
          tint: type.color,
          icon: type.icon,
          amount: item.amount || 0,
          variation: item.variation_pct,
          shareValue: this.formatShare(item.share_pct),
          clickable: true,
        });
      });
      return cards;
    },
    sectorSlices() {
      const rows = (this.payload?.sectors || [])
        .filter((row) => Number(row.total) > 0)
        .map((row, index) => ({
          label: row.label,
          value: Number(row.total) || 0,
          share: Number(row.share_pct) || 0,
          color: SLICE_COLORS[index % SLICE_COLORS.length],
        }));
      if (rows.length <= 6) return rows;
      const head = rows.slice(0, 5);
      const rest = rows.slice(5);
      const restValue = rest.reduce((sum, row) => sum + row.value, 0);
      const total = rows.reduce((sum, row) => sum + row.value, 0);
      head.push({
        label: 'Autres',
        value: restValue,
        share: total ? Math.round((restValue / total) * 1000) / 10 : 0,
        color: '#94a3b8',
      });
      return head;
    },
    sectorTotal() {
      return this.sectorSlices.reduce((sum, slice) => sum + slice.value, 0);
    },
  },
  watch: {
    payload: {
      flush: 'post',
      handler() {
        this.renderCharts();
      },
    },
    page(value) {
      if (value === 'board') this.$nextTick(() => this.renderCharts());
    },
  },
  mounted() {
    this.load();
  },
  beforeUnmount() {
    this.destroyCharts();
  },
  methods: {
    formatAmount(value) {
      return Math.round(Number(value) || 0).toLocaleString('fr-FR');
    },
    formatMoney(value) {
      return `${this.formatAmount(value)} FCFA`;
    },
    formatCompact(value) {
      const amount = Number(value) || 0;
      const abs = Math.abs(amount);
      if (abs >= 1e9) return `${(amount / 1e9).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} Md`;
      if (abs >= 1e6) return `${(amount / 1e6).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} M`;
      if (abs >= 1e3) return `${(amount / 1e3).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} k`;
      return amount.toLocaleString('fr-FR');
    },
    agencyShort(label) {
      return String(label || '').replace(/^agence\s+/i, '').trim() || label;
    },
    cafDisplayName(caf) {
      const name = String(caf?.label || '').trim();
      if (!name || /^non renseign/i.test(name)) {
        return caf?.code && caf.code !== '-' ? caf.code : 'Non renseigné';
      }
      return name.toLocaleLowerCase('fr-FR').replace(/(^|[\s'-])(\p{L})/gu, (_, sep, letter) => sep + letter.toLocaleUpperCase('fr-FR'));
    },
    rankEnds(rows) {
      const total = this.matrixTotals.total || 0;
      const ordered = [...rows].filter((row) => row.total > 0).sort((left, right) => right.total - left.total);
      const peak = ordered[0]?.total || 1;
      const decorate = (list) => list.map((row) => ({
        ...row,
        share: total ? (row.total / total) * 100 : 0,
        bar: (row.total / peak) * 100,
      }));
      return {
        top: decorate(ordered.slice(0, 5)),
        flop: decorate(ordered.slice(5).sort((left, right) => left.total - right.total).slice(0, 5)),
      };
    },
    formatShare(value) {
      const number = Number(value) || 0;
      if (number > 0 && number < 0.1) return '< 0,1 %';
      return `${number.toLocaleString('fr-FR', { maximumFractionDigits: 1, minimumFractionDigits: 1 })} %`;
    },
    formatDate(value) {
      const text = String(value || '').slice(0, 10);
      const [year, month, day] = text.split('-');
      if (!year || !month || !day) return '—';
      return `${day}/${month}/${year}`;
    },
    groupLines(rows, key) {
      const buckets = new Map();
      rows.forEach((row) => {
        const label = row[key] || '—';
        const bucket = buckets.get(label) || { label, total: 0, count: 0 };
        bucket.total += Number(row.montant) || 0;
        bucket.count += 1;
        buckets.set(label, bucket);
      });
      const items = [...buckets.values()].sort((left, right) => right.total - left.total);
      const sum = items.reduce((total, item) => total + item.total, 0);
      return items.map((item) => ({
        ...item,
        share: sum ? (item.total / sum) * 100 : 0,
      }));
    },
    sumMatrix(rows) {
      const totals = { restructure: 0, protocole: 0, rebooker: 0, simple: 0, total: 0, previous: 0 };
      rows.forEach((row) => {
        totals.restructure += Number(row.restructure) || 0;
        totals.protocole += Number(row.protocole) || 0;
        totals.rebooker += Number(row.rebooker) || 0;
        totals.simple += Number(row.simple) || 0;
        totals.total += Number(row.total) || 0;
        totals.previous += Number(row.previous_total) || 0;
      });
      totals.variation_pct = totals.previous
        ? ((totals.total - totals.previous) / totals.previous) * 100
        : null;
      return totals;
    },
    openTable() {
      this.page = 'table';
      this.closeDetail();
    },
    openPerformance() {
      this.page = 'performance';
      this.closeDetail();
    },
    toggleExpand(key) {
      this.expanded = { ...this.expanded, [key]: !this.expanded[key] };
    },
    openDetail(key) {
      this.activeCard = key;
      this.detailTab = 'prets';
      this.detailQuery = '';
      this.detailPage = 1;
      if (!this.linesLoaded) this.loadLines();
    },
    closeDetail() {
      this.activeCard = null;
    },
    setDetailTab(tab) {
      this.detailTab = tab;
    },
    deltaClass(value) {
      const number = Number(value);
      if (!number) return '';
      return number > 0 ? 'positive' : 'negative';
    },
    formatCardEvolution(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      const number = Number(value);
      const sign = number > 0 ? '+' : '';
      const digits = Math.abs(number) >= 100 ? 0 : 1;
      return `${sign}${number.toLocaleString('fr-FR', { maximumFractionDigits: digits, minimumFractionDigits: digits })} %`;
    },
    formatEvolution(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      const number = Number(value);
      const abs = Math.abs(number);
      if (abs >= 1000) {
        const ratio = Math.abs(1 + number / 100);
        const digits = ratio >= 100 ? 0 : 1;
        return `× ${ratio.toLocaleString('fr-FR', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
      }
      const sign = number > 0 ? '+' : '';
      return `${sign}${number.toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
    },
    evolutionHint(value) {
      if (value === null || value === undefined || Math.abs(Number(value)) < 1000) return '';
      const number = Number(value);
      const sign = number > 0 ? '+' : '';
      return `${sign}${number.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} % par rapport à la période précédente`;
    },
    objectifEndMonth() {
      if (this.scope === 'month') return this.month;
      return Number(String(this.payload?.period?.end || '').slice(5, 7))
        || (this.year === new Date().getFullYear() ? new Date().getMonth() + 1 : 12);
    },
    objectivePool(includeCaf = false) {
      const latest = new Map();
      this.objectives.forEach((row) => {
        if (!['validated', 'pending_validation'].includes(row.status)) return;
        const isCaf = /CAF\s*:/i.test(String(row.agency_name || ''));
        if (isCaf !== includeCaf) return;
        if (!includeCaf && this.agence && String(row.agency_code) !== String(this.agence)) return;
        const key = `${row.agency_code}|${row.category}|${row.period}|${row.month || 0}|${row.agency_name || ''}`;
        const previous = latest.get(key);
        if (!previous || Number(row.id) > Number(previous.id)) latest.set(key, row);
      });
      const unique = [...latest.values()];
      const validated = unique.filter((row) => row.status === 'validated');
      return validated.length ? validated : unique;
    },
    periodAmount(rows) {
      const endMonth = this.objectifEndMonth();
      const amountOf = (list) => list.reduce((sum, row) => {
        const volume = Number(row.value_volume) || 0;
        const value = Number(row.value) || 0;
        return sum + (volume > 0 ? volume : value);
      }, 0);
      if (this.scope === 'month') {
        const monthly = rows.filter((row) => row.period === 'month' && Number(row.month) === this.month);
        if (monthly.length) return amountOf(monthly);
        const annual = rows.filter((row) => row.period === 'year');
        return annual.length ? amountOf(annual) / 12 : 0;
      }
      const monthly = rows.filter((row) => row.period === 'month' && Number(row.month) >= 1 && Number(row.month) <= endMonth);
      if (monthly.length) return amountOf(monthly);
      const annual = rows.filter((row) => row.period === 'year');
      return annual.length ? amountOf(annual) * (endMonth / 12) : 0;
    },
    objectifAmount() {
      const pool = this.objectivePool(false);
      const pick = (list) => {
        if (this.agence) {
          return list.filter((row) => row.category === 'POINT SERVICES' || row.category === 'GRAND COMPTE');
        }
        const filiale = list.filter((row) => row.category === 'FILIALE');
        if (filiale.length) return filiale;
        const agencies = list.filter((row) => row.category === 'POINT SERVICES' || row.category === 'GRAND COMPTE');
        if (agencies.length) return agencies;
        return list.filter((row) => row.category === 'TERRITOIRE');
      };
      return this.periodAmount(pick(pool));
    },
    agencyObjectif(code, label) {
      const codeKey = String(code || '');
      const nameKey = this.normName(label);
      const rows = this.objectivePool(false).filter((row) => {
        if (row.category === 'FILIALE') return false;
        const rowCode = String(row.agency_code || '');
        const rowName = this.normName(row.agency_name);
        if (codeKey && rowCode === codeKey) return true;
        if (nameKey && (rowName === nameKey || this.normName(rowCode) === nameKey)) return true;
        return false;
      });
      return this.periodAmount(rows);
    },
    territoryObjectif(group) {
      const full = this.normName(group?.name);
      const short = this.normName(String(group?.name || '').replace(/^territoire\s+/i, ''));
      const key = this.normName(group?.key);
      const rows = this.objectivePool(false).filter((row) => {
        const rowCode = this.normName(row.agency_code);
        const rowName = this.normName(row.agency_name);
        if (key && rowCode === key) return true;
        return Boolean(rowName) && (rowName === full || rowName === short);
      });
      return this.periodAmount(rows);
    },
    cafObjectif(label) {
      const name = this.normName(label);
      if (!name || name === 'NON RENSEIGNE') return 0;
      const rows = this.objectivePool(true).filter((row) => {
        const match = String(row.agency_name || '').match(/CAF\s*:\s*(.+)$/i);
        return match && this.normName(match[1]) === name;
      });
      return this.periodAmount(rows);
    },
    normName(value) {
      return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-zA-Z0-9]+/g, ' ')
        .trim()
        .toUpperCase();
    },
    visibleTarget(total, objectif) {
      const target = Number(objectif) || 0;
      const realised = Number(total) || 0;
      if (target <= 0 || realised <= 0) return 0;
      if (realised / target > 10) return 0;
      return target;
    },
    score(amount, objectif) {
      const target = Number(objectif) || 0;
      if (!target) return { tro: null, variation: null };
      const realised = Number(amount) || 0;
      return {
        tro: (realised / target) * 100,
        variation: realised - target,
      };
    },
    formatTro(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      return `${Number(value).toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
    },
    formatGap(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
      const number = Math.round(Number(value));
      const sign = number > 0 ? '+' : '';
      return `${sign}${number.toLocaleString('fr-FR')}`;
    },
    troClass(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '';
      if (value >= 100) return 'positive';
      if (value >= 80) return 'mid';
      return 'negative';
    },
    familleColor(index) {
      return FAMILLE_COLORS[index % FAMILLE_COLORS.length];
    },
    setScope(scope) {
      if (this.scope === scope) return;
      this.scope = scope;
      this.load();
    },
    async load() {
      this.loading = true;
      this.error = '';
      this.linesLoaded = false;
      this.linesLoading = false;
      try {
        const params = { scope: this.scope, year: this.year };
        if (this.scope === 'month') params.month = this.month;
        if (this.agence) params.agences = this.agence;
        if (this.secteur) params.secteurs = this.secteur;
        if (this.typeCredit) params.types = this.typeCredit;
        const [response, objectives] = await Promise.all([
          window.axios.get('/api/oracle/data/suivi-production', { params }),
          window.axios.get('/api/objectives', { params: { type: 'PRODUCTION', year: this.year } }).catch(() => ({ data: { data: [] } })),
        ]);
        this.payload = response.data;
        this.objectives = objectives.data?.data || [];
        if (this.activeCard) this.loadLines();
      } catch (error) {
        this.error = error?.response?.data?.detail
          || error?.response?.data?.message
          || 'Impossible de charger le suivi de production.';
      } finally {
        this.loading = false;
      }
    },
    async loadLines() {
      this.linesLoading = true;
      try {
        const params = { scope: this.scope, year: this.year, lignes: 1 };
        if (this.scope === 'month') params.month = this.month;
        if (this.agence) params.agences = this.agence;
        if (this.secteur) params.secteurs = this.secteur;
        if (this.typeCredit) params.types = this.typeCredit;
        const response = await window.axios.get('/api/oracle/data/suivi-production', { params });
        if (this.payload) {
          this.payload = { ...this.payload, lines: response.data?.lines || [] };
        }
        this.linesLoaded = true;
      } catch (error) {
        this.error = error?.response?.data?.detail
          || error?.response?.data?.message
          || 'Impossible de charger le détail des prêts.';
      } finally {
        this.linesLoading = false;
      }
    },
    destroyCharts() {
      [this.barChart, this.lineChart, this.familleChart, this.donutChart].forEach((chart) => {
        if (!chart) return;
        try {
          chart.destroy();
        } catch (error) {
          /* le canvas a déjà été retiré du DOM */
        }
      });
      this.barChart = null;
      this.lineChart = null;
      this.familleChart = null;
      this.donutChart = null;
    },
    renderCharts() {
      this.destroyCharts();
      this.renderBars();
      this.renderLines();
      this.renderFamilleLines();
      this.renderDonut();
    },
    evolutionChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { right: 72, top: 12, bottom: 8 } },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => `${context.dataset.label} : ${formatAxis(context.parsed.y)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: '#64748b',
              maxRotation: 0,
              autoSkip: false,
              font: { size: 11 },
              callback(value) {
                const labels = this.chart.data.labels || [];
                const label = String(labels[value] || '');
                const [month, year] = label.split(' ');
                if (!month) return label;
                const previous = value > 0 ? String(labels[value - 1] || '') : '';
                if (!previous || previous.split(' ')[1] !== year) return [month, year];
                return month;
              },
            },
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#64748b', callback: (value) => formatAxis(value) },
            grid: { color: '#e8eef5' },
            border: { display: false },
          },
        },
      };
    },
    renderDonut() {
      const canvas = this.$refs.donutCanvas;
      if (!canvas || !this.sectorSlices.length) return;
      this.donutChart = new Chart(canvas, {
        type: 'doughnut',
        plugins: [donutPercents],
        data: {
          labels: this.sectorSlices.map((slice) => slice.label),
          datasets: [{
            data: this.sectorSlices.map((slice) => slice.value),
            backgroundColor: this.sectorSlices.map((slice) => slice.color),
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
                  const share = this.sectorTotal
                    ? Math.round((value / this.sectorTotal) * 100)
                    : 0;
                  return ` ${context.label} : ${this.formatMoney(value)} (${share} %)`;
                },
              },
            },
          },
        },
      });
    },
    renderBars() {
      const canvas = this.$refs.barCanvas;
      if (!canvas || !this.agencyStacks.length) return;
      const rows = this.agencyStacks;
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
          datasets: TYPES.map((type) => ({
            label: type.stackLabel,
            data: rows.map((row) => Number(row[type.key]) || 0),
            backgroundColor: type.color,
            stack: 'credit',
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
                  return `Total : ${formatAxis(total)}`;
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
    renderLines() {
      const canvas = this.$refs.lineCanvas;
      const rows = this.months.slice(-6);
      if (!canvas || !rows.length) return;
      this.lineChart = new Chart(canvas, {
        type: 'line',
        plugins: [endLabels],
        data: {
          labels: rows.map((row) => row.label),
          datasets: TYPES.map((type) => ({
            label: type.label,
            data: rows.map((row) => Number(row[type.key]) || 0),
            borderColor: type.color,
            backgroundColor: type.color,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBorderWidth: 0,
            borderWidth: 2.5,
            tension: 0.35,
          })),
        },
        options: this.evolutionChartOptions(),
      });
    },
    renderFamilleLines() {
      const canvas = this.$refs.familleCanvas;
      const start = Math.max(0, this.familleLabels.length - 6);
      const labels = this.familleLabels.slice(start);
      if (!canvas || !this.familleSeries.length || !labels.length) return;
      this.familleChart = new Chart(canvas, {
        type: 'line',
        plugins: [endLabels],
        data: {
          labels,
          datasets: this.familleSeries.map((serie, index) => {
            const color = this.familleColor(index);
            return {
              label: serie.label,
              data: (serie.values || []).slice(start).map((value) => Number(value) || 0),
              borderColor: color,
              backgroundColor: color,
              pointRadius: 4,
              pointHoverRadius: 6,
              pointBorderWidth: 0,
              borderWidth: 2.5,
              tension: 0.35,
            };
          }),
        },
        options: this.evolutionChartOptions(),
      });
    },
  },
};
</script>

<style scoped>
.suivi {
  margin: -20px -20px 0;
  min-height: 100%;
  background: #f4f7f5;
  color: #1c2b24;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.suivi-body {
  padding: 16px 20px 36px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px;
  background: #fff;
  border: 1px solid #e3eee8;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(20, 61, 46, 0.04);
}

.segment {
  display: flex;
  flex: 0 0 auto;
  height: 36px;
  padding: 3px;
  background: #f3f6f4;
  border-radius: 10px;
  box-sizing: border-box;
}

.segment button {
  border: 0;
  background: transparent;
  color: #4d6158;
  font-weight: 700;
  font-size: 12px;
  padding: 0 12px;
  border-radius: 8px;
  cursor: pointer;
}

.segment button.on {
  background: #1a4d3a;
  color: #fff;
}

.toolbar-split {
  width: 1px;
  height: 22px;
  background: #e1ebe6;
  flex: 0 0 1px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 0;
  min-width: 0;
  height: 36px;
  padding: 0 28px 0 12px;
  background: #f3f6f4 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%236b7c74' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") right 10px center no-repeat;
  border-radius: 10px;
}

.chip-year { flex: 0 0 132px; }
.chip-month { flex: 0 0 158px; }

.chip span {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  color: #6b7c74;
}

.chip select {
  flex: 1 1 auto;
  width: 0;
  min-width: 0;
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
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 10px;
  background: #1a4d3a;
  color: #fff;
  cursor: pointer;
}

.refresh svg { width: 16px; height: 16px; }

.refresh:disabled { opacity: 0.65; cursor: wait; }

.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.kpi,
.panel {
  background: #fff;
  border: 1px solid #d5e4f2;
  border-radius: 16px;
  box-shadow: 0 8px 22px rgba(30, 64, 110, 0.06);
}

.panel { border-color: #e4eee8; box-shadow: 0 8px 24px rgba(20, 61, 46, 0.04); }

.kpi {
  display: flex;
  flex-direction: column;
  padding: 8px 10px 7px;
  min-width: 0;
  border-radius: 10px;
  border-top: 2px solid var(--accent, #2563eb);
  cursor: pointer;
}

.kpi-static { cursor: default; }
.kpi:hover { border-color: var(--accent, #2563eb); }
.kpi:focus-visible { outline: 2px solid var(--accent, #2563eb); outline-offset: 2px; }

.kpi-head {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 22px;
  margin-bottom: 4px;
}

.kpi-title {
  color: #1e293b;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.2;
}

.kpi-icon {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  background: var(--accent, #2563eb);
}

.kpi-icon :deep(svg) { width: 12px; height: 12px; }

.kpi-value {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: #0b1f33;
  font-variant-numeric: tabular-nums;
}

.kpi-unit {
  margin: 1px 0 0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #94a3b8;
}

.kpi-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  min-width: 0;
}

.kpi-evo {
  flex: 0 0 auto;
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  color: #64748b;
}

.table-link.on,
.perf-link.on {
  background: #143d2e;
}

.table-link,
.back-link {
  height: 36px;
  padding: 0 14px;
  border: 0;
  border-radius: 10px;
  background: #1a4d3a;
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.back-link { background: #e7f2ec; color: #1a4d3a; }

.table-page-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.perf-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}

.perf-card.is-caf:not(.is-low) { order: 1; }
.perf-card.is-agency:not(.is-low) { order: 2; }
.perf-card.is-low.is-caf { order: 3; }
.perf-card.is-low.is-agency { order: 4; }

.perf-card {
  border-radius: 16px;
  overflow: hidden;
}

.rank-id {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.rank-hint {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.is-caf .rank-hint::before { content: 'Agence '; color: #94a3b8; font-weight: 600; }
.is-agency .rank-hint::before { content: 'Zone '; color: #94a3b8; font-weight: 600; }

.perf-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -16px -16px 12px;
  padding: 10px 14px;
}

.perf-card.is-caf .perf-head,
.perf-card.is-agency .perf-head { background: #d7f0e3; }
.perf-card.is-caf .perf-head h2,
.perf-card.is-agency .perf-head h2 { color: #143d2e; }
.perf-card.is-low .perf-head { background: #fdecec; }
.perf-card.is-low .perf-head h2 { color: #991b1b; }

.perf-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #143d2e;
}

.perf-ico,
.rank-ico,
.zone-ico {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 10px;
}

.perf-ico {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #fff;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.06);
}

.perf-ico :deep(svg),
.zone-ico :deep(svg) {
  width: 24px;
  height: 24px;
}

.perf-ico.is-top,
.rank-list.is-top { --tone: #1a4d3a; }
.perf-ico.is-flop,
.rank-list.is-flop { --tone: #b91c1c; }

.perf-ico.is-top { background: #f3faf6; }
.perf-ico.is-flop { background: #fef2f2; }

.zone-ico {
  color: inherit;
  background: #fff;
}

.podium {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.podium article {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 10px;
  min-width: 0;
  background: #fff;
  border: 1px solid #e6edf3;
  border-radius: 12px;
  padding: 10px 12px;
}

.zone-follow {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 8px 0 0;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.35);
  overflow: hidden;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

.zone-follow span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.zone-follow span + span::before {
  content: '·';
  margin-right: 8px;
  color: rgba(255, 255, 255, 0.6);
}

.podium article.is-caf {
  background: #ffd24a;
  border-color: #e6b000;
}
.podium article.is-agency {
  background: #3ecf8e;
  border-color: #14915c;
}
.podium article.is-zone {
  background: #5b8def;
  border-color: #2f62d6;
}
.podium article.is-caf em { color: #92600a; background: #fff; }
.podium article.is-agency em { color: #0f7a45; background: #fff; }
.podium article.is-zone em { color: #1d4ed8; background: #fff; }
.podium article.is-agency .podium-id p,
.podium article.is-zone .podium-id p { color: rgba(255, 255, 255, 0.86); }
.podium article.is-agency .podium-id strong,
.podium article.is-zone .podium-id strong,
.podium article.is-agency .podium-foot > span,
.podium article.is-zone .podium-foot > span { color: #fff; }

.podium-ico {
  width: 32px;
  height: 32px;
  margin: 0;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.podium-ico :deep(svg) { width: 20px; height: 20px; }

.podium-id { min-width: 0; flex: 1; }

.podium-id p {
  margin: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.podium-id strong {
  display: block;
  margin-top: 1px;
  font-size: 13px;
  line-height: 1.25;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.podium-foot {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0;
  margin: 0;
  padding: 0;
  border: 0;
  flex-shrink: 0;
}

.podium-foot > span,
.podium-foot small {
  white-space: nowrap;
}

.podium-foot > span {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}

.podium em {
  display: inline-block;
  margin: 2px 0 0;
  padding: 2px 7px;
  border-radius: 999px;
  background: #eef6f1;
  font-style: normal;
  font-size: 12px;
  font-weight: 700;
  color: #1a4d3a;
  white-space: nowrap;
}

.podium em.positive { color: #15803d; background: #e7f6ec; }
.podium em.mid { color: #b45309; background: #fff4e5; }
.podium em.negative { color: #b91c1c; background: #fdecec; }

.perf-zones { grid-column: 1 / -1; }

.zone-strip {
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e4eee8;
  border-radius: 12px;
}

.zone-track {
  display: flex;
  height: 6px;
  gap: 3px;
  overflow: hidden;
  border-radius: 99px;
  background: #f4f7f5;
}

.zone-track span {
  min-width: 10px;
  border-radius: 99px;
  background: #1a4d3a;
}

.zone-track span:nth-child(2) { background: #3d8f68; }
.zone-track span:nth-child(3) { background: #8fbfa6; }
.zone-track span:nth-child(4) { background: #d5e6dc; }

.zone-legend {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 8px;
}

.zone-legend p {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  margin: 0;
}

.zone-legend strong {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #143d2e;
  white-space: nowrap;
}

.zone-legend strong::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
  background: #1a4d3a;
}

.zone-legend p:nth-child(2) strong::before { background: #3d8f68; }
.zone-legend p:nth-child(3) strong::before { background: #8fbfa6; }
.zone-legend p:nth-child(4) strong::before { background: #d5e6dc; }

.zone-legend span,
.zone-legend em {
  font-style: normal;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}

.zone-legend span { color: #0f172a; font-weight: 800; }

.rank-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.rank-list li,
.rank-list.is-flop li {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 9px 2px;
  border-bottom: 1px solid #f1f5f3;
}

.rank-list li:last-child { border-bottom: 0; padding-bottom: 2px; }
.rank-list li:first-child { padding-top: 2px; }

.rank-index {
  flex: 0 0 26px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 800;
  background: #eef2f6;
  color: #64748b;
}

.rank-list.is-top .pos-1 { background: #1a4d3a; color: #fff; }
.rank-list.is-top .pos-2 { background: #3d8f68; color: #fff; }
.rank-list.is-top .pos-3 { background: #8fbfa6; color: #143d2e; }
.rank-list.is-top .rank-index { background: #e5f6ec; color: #1a4d3a; }
.rank-list.is-flop .rank-index { background: #fee2e2; color: #b91c1c; }

.rank-name {
  min-width: 0;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-track {
  display: block;
  height: 5px;
  margin-top: 5px;
  border-radius: 99px;
  background: #eef3f8;
  overflow: hidden;
}

.rank-fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  min-width: 6px;
  background: var(--tone);
}

.rank-figure {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
  white-space: nowrap;
}

.rank-figure small {
  display: inline-block;
  margin: 2px 0 0;
  padding: 1px 6px;
  border-radius: 999px;
  background: #f3f6f4;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

.rank-list.is-top .rank-figure small { color: #1a4d3a; }
.rank-list.is-flop .rank-figure small { color: #b91c1c; }
.rank-list .rank-figure small.positive { color: #15803d; background: #e7f6ec; }
.rank-list .rank-figure small.mid { color: #b45309; background: #fff4e5; }
.rank-list .rank-figure small.negative { color: #b91c1c; background: #fdecec; }
.rank-list .rank-figure small.rank-target {
  margin: 0;
  padding: 0;
  background: none;
  color: #94a3b8;
  font-weight: 600;
}
.podium-foot small {
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
}

@media (max-width: 900px) {
  .perf-grid,
  .podium,
  .zone-legend { grid-template-columns: 1fr; }
}

.zone-agencies-section { margin-top: 4px; }

.level-1-row { background: #2a2a2a; color: #fff; font-weight: 700; cursor: pointer; }
.level-2-row { background: #4a4a4a; color: #fff; font-weight: 600; cursor: pointer; }
.level-3-row { background: #fff; cursor: pointer; }
.level-3-row:hover td { background: #f5f5f5; }
.level-4-row { background: #f7f8f7; }
.level-4-row:hover td { background: #eef3f0; }
.level-2 { padding-left: 16px; }
.level-3 { padding-left: 28px; color: #333; }
.level-4 { padding-left: 28px; color: #333; font-weight: 500; }

.cell-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 700;
}

.level-3 .expand-btn {
  color: #1c2b24;
  border-color: #d5e4f2;
  background: #f3f6f4;
}
.level-1-row .positive, .level-2-row .positive, .total-row .positive { color: #86efac; }
.level-1-row .negative, .level-2-row .negative, .total-row .negative { color: #fca5a5; }
.level-1-row .mid, .level-2-row .mid, .total-row .mid { color: #fde68a; }
.mid { color: #d97706; font-weight: 600; }

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
  color: #143d2e;
}

.table-container {
  overflow-x: auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agencies-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  min-width: 1080px;
  table-layout: fixed;
}

.w-agence { width: 148px; }
.w-gest { width: 210px; }

.agencies-table thead { background: #dc2626; color: #fff; }

.agencies-table th {
  padding: 10px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  white-space: nowrap;
}

.agencies-table th.col-label,
.agencies-table td.col-label {
  text-align: left;
  padding-left: 10px;
}

.agency-code {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.agencies-table th.col-agence,
.agencies-table td.col-agence,
.agencies-table td.col-gest {
  white-space: normal;
  overflow-wrap: break-word;
  line-height: 1.25;
  padding-right: 8px;
}

.th-title,
.th-unit { display: block; }
.th-unit {
  margin-top: 2px;
  font-size: 10px;
  font-weight: 500;
  opacity: 0.85;
}

.agencies-table td {
  padding: 10px 8px;
  font-size: 13px;
  text-align: center;
  vertical-align: middle;
  border-bottom: 1px solid #eee;
  border-right: 1px solid #f0f0f0;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.agencies-table td.col-label {
  font-weight: 600;
}

.agencies-table tbody tr:hover td { background: #f5f5f5; }

.total-row { background: #dc2626; font-weight: 600; color: #fff; }
.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
  color: #fff;
}
.total-row:hover td { background: #dc2626; }

.positive { color: #10b981; font-weight: 600; }
.negative { color: #ef4444; font-weight: 600; }
.total-row .positive { color: #bbf7d0; }
.total-row .negative { color: #fecaca; }

.grid-2 {
  display: grid;
  grid-template-columns: 1.35fr 0.9fr;
  gap: 12px;
  margin-top: 12px;
}

.panel { padding: 16px 16px 14px; min-width: 0; }

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

.chart-title {
  color: #2563eb;
  font-size: 15px;
  font-weight: 700;
}

.panel-head span { font-size: 12px; color: #6b7c74; }

.chart-scroll { overflow-x: auto; }
.chart-box { position: relative; height: 280px; }
.chart-box.tall { height: 360px; min-width: 100%; }

.stack-legend { justify-content: center; }
.swatch.square { width: 14px; height: 10px; border-radius: 2px; }

.donut-layout {
  display: flex;
  gap: 18px;
  align-items: center;
  min-height: 280px;
}

.donut {
  position: relative;
  width: 260px;
  height: 260px;
  flex-shrink: 0;
}

.donut-center {
  position: absolute;
  inset: 27%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  pointer-events: none;
}

.donut-center strong {
  font-size: 15px;
  font-weight: 800;
  color: #1e3a8a;
  line-height: 1.2;
  letter-spacing: -0.03em;
}
.donut-center span {
  margin-top: 2px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.legend, .inline-legend, .top-list { list-style: none; margin: 0; padding: 0; }
.legend {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.legend li {
  display: flex;
  align-items: center;
  gap: 10px;
}
.swatch { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.legend-name { font-size: 14px; font-weight: 600; color: #1e293b; }

.inline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 8px;
}
.inline-legend li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #3d4a44;
}
.inline-legend .swatch { margin-top: 0; }

.top-list {
  max-height: 320px;
  overflow: auto;
}
.top-list li {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}
.rank {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: #e7f2ec;
  color: #1a4d3a;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.top-body { flex: 1; min-width: 0; }
.top-line {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 6px;
}
.top-name { font-weight: 700; color: #1c2b24; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.top-line strong { font-weight: 700; color: #143d2e; white-space: nowrap; }
.top-line em { font-style: normal; font-weight: 600; color: #6b7c74; }
.bar-track { height: 8px; border-radius: 99px; background: #e7f0eb; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #1a4d3a, #3d9a72); }

.banner, .empty {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e4eee8;
  color: #3d4a44;
}
.banner.error { background: #fff5f5; border-color: #fecaca; color: #9f1239; }

.detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.35);
}

.detail {
  width: min(880px, 100%);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: -12px 0 40px rgba(15, 23, 42, 0.16);
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 18px 20px 12px;
}

.detail-kicker {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1a4d3a;
}

.detail-head h2 {
  margin: 0;
  font-size: 22px;
  color: #0f2744;
}

.detail-close {
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

.detail-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 0 20px 14px;
}

.detail-stats p {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f4f7f5;
}

.detail-stats span {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  color: #64748b;
}

.detail-stats strong {
  font-size: 14px;
  color: #0f2744;
}

.detail-tabs {
  display: flex;
  gap: 6px;
  padding: 0 20px 12px;
}

.detail-tabs button {
  border: 0;
  background: #f3f6f4;
  color: #3d4f46;
  font-weight: 700;
  font-size: 13px;
  border-radius: 8px;
  padding: 7px 12px;
  cursor: pointer;
}

.detail-tabs button.on {
  background: #1a4d3a;
  color: #fff;
}

.detail-search {
  display: grid;
  gap: 4px;
  padding: 0 20px 12px;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

.detail-search input {
  height: 36px;
  border: 1px solid #d7e3dc;
  border-radius: 8px;
  padding: 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #1c2b24;
}

.detail-table-wrap {
  flex: 1;
  overflow: auto;
  padding: 0 20px 16px;
}

.detail table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.detail th {
  position: sticky;
  top: 0;
  text-align: left;
  padding: 8px 10px;
  background: #f8faf9;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.detail td {
  padding: 9px 10px;
  border-top: 1px solid #eef2f6;
  color: #1e293b;
}

.detail .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.detail-empty { text-align: center; color: #64748b; }

.detail-pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 12px 20px 16px;
  border-top: 1px solid #eef2f6;
  font-size: 13px;
  color: #475569;
}

.detail-pager button {
  border: 1px solid #d7e3dc;
  background: #fff;
  border-radius: 8px;
  padding: 6px 10px;
  font-weight: 700;
  cursor: pointer;
}

.detail-pager button:disabled { opacity: 0.45; cursor: default; }

@media (max-width: 1200px) {
  .toolbar { flex-wrap: wrap; }
  .chip { flex: 1 1 160px; }
  .toolbar-split { display: none; }
  .kpi-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .grid-2 { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .kpi-row { grid-template-columns: 1fr; }
  .donut-layout { flex-direction: column; }
}
</style>
