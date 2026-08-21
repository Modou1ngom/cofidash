<template>
  <div class="comptes-ouverts">
    <div class="toolbar-row">
      <div class="toolbar-nav">
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
        <button
          v-if="canOpenSettings"
          type="button"
          class="btn-settings"
          @click="openSettings"
        >
          Paramétrage
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
            <div class="kpi-body">
              <span class="kpi-label">Obj. annuel</span>
              <strong class="kpi-value">{{ formatObj(kpis.objAnnuel) }}</strong>
            </div>
          </article>
          <article class="kpi kpi-ytd">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M4 19V5M4 19h16M8 15l3-3 3 2 4-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <div class="kpi-body">
              <span class="kpi-label">Obj. YTD</span>
              <strong class="kpi-value">{{ formatObj(kpis.objYtd) }}</strong>
            </div>
          </article>
          <article class="kpi kpi-realise">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" stroke-linecap="round"/></svg>
            </span>
            <div class="kpi-body">
              <span class="kpi-label">Réalisé YTD</span>
              <strong class="kpi-value">{{ formatNumber(kpis.realiseYtd) }}</strong>
            </div>
            <span class="kpi-meta">{{ formatNumber(kpis.courantsYtd) }} cour. · {{ formatNumber(kpis.epargneYtd) }} ép.</span>
          </article>
          <article class="kpi" :class="ecartClass(kpis.ecartYtd)">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M7 17l5-5 5 5M7 7l5 5 5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </span>
            <div class="kpi-body">
              <span class="kpi-label">Écart YTD</span>
              <strong class="kpi-value">{{ kpis.tro === null ? '—' : formatSigned(kpis.ecartYtd) }}</strong>
            </div>
          </article>
          <article class="kpi" :class="troTone(kpis.tro)">
            <span class="kpi-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2" stroke-linecap="round"/></svg>
            </span>
            <div class="kpi-body">
              <span class="kpi-label">TRO YTD</span>
              <strong class="kpi-value">{{ formatTro(kpis.tro) }}</strong>
            </div>
          </article>
        </section>

        <div class="dash-row dash-row--chart">
          <section class="dash-card dash-card--chart">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent" />
                <h3>Évolution mensuelle</h3>
              </div>
              <span class="dash-card-meta">{{ monthlyChartMeta }}</span>
            </div>
            <div class="dash-card-chart-body">
              <PythonChart
                :key="`co-${monthlyChartType}-${selectedMonth}-${selectedYear}-${hasObjectives}`"
                :chart-type="monthlyChartType"
                :chart-data="monthlyChartData"
                :height="180"
              />
            </div>
          </section>

          <div class="dash-col-stack">
            <div class="dash-mode-bar">
              <span class="dash-mode-bar-label">Vue dashboard</span>
              <div class="perf-mode-toggle">
                <button
                  type="button"
                  :class="{ active: dashboardMode === 'ytd' }"
                  @click="dashboardMode = 'ytd'"
                >
                  YTD
                </button>
                <button
                  type="button"
                  :class="{ active: dashboardMode === 'month' }"
                  @click="dashboardMode = 'month'"
                >
                  Mois
                </button>
              </div>
            </div>
            <section class="dash-card">
              <div class="dash-card-head">
                <div class="dash-card-title">
                  <span class="dash-card-accent" />
                  <h3>Performance territoire</h3>
                </div>
                <span class="dash-card-meta">{{ dashboardTerritoryMeta }}</span>
              </div>
              <div class="territory-table-wrap">
                <table class="territory-table">
                  <thead>
                    <tr>
                      <th>Territoire</th>
                      <th class="num col-objectif">{{ dashboardMode === 'ytd' ? 'Obj. YTD' : 'Obj. mensuel' }}</th>
                      <th class="num">{{ dashboardMode === 'ytd' ? 'Réalisé YTD' : 'Réalisé mois' }}</th>
                      <th class="num">TRO</th>
                      <th class="col-status">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(row, idx) in dashboardTerritoryRows"
                      :key="row.key"
                      :class="{ 'is-lead': idx === 0 }"
                    >
                      <td>
                        <strong v-if="idx === 0">{{ row.name }}</strong>
                        <template v-else>{{ row.name }}</template>
                      </td>
                      <td class="num col-objectif">{{ formatObj(dashboardTerritoryObj(row)) }}</td>
                      <td class="num">{{ formatNumber(dashboardTerritoryRealise(row)) }}</td>
                      <td class="num col-tro">
                        <template v-if="dashboardTerritoryTro(row) !== null">{{ formatTro(dashboardTerritoryTro(row)) }}</template>
                        <template v-else>—</template>
                      </td>
                      <td class="col-status">
                        <span
                          class="status-orb"
                          :class="territoryStatusClass(dashboardTerritoryTro(row))"
                          :title="formatTro(dashboardTerritoryTro(row))"
                        />
                      </td>
                    </tr>
                    <tr v-if="!dashboardTerritoryRows.length">
                      <td colspan="5" class="empty">Aucune donnée</td>
                    </tr>
                  </tbody>
                </table>
                <div class="status-legend"></div>
              </div>
            </section>

            <section class="dash-card dash-card--resume">
              <div class="resume-card-head">
                <h3>Résumé période</h3>
                <span class="dash-card-meta">{{ dashboardTerritoryMeta }}</span>
              </div>
              <ul class="dash-resume-list">
                <li class="resume-agency">
                  <span class="dash-resume-icon" aria-hidden="true">🏆</span>
                  <div class="dash-resume-text">
                    <span class="dash-resume-label">Meilleure agence</span>
                    <strong class="dash-resume-value">{{ dashboardBestAgency?.name || '—' }}</strong>
                  </div>
                  <span
                    v-if="dashboardBestAgency"
                    :class="hasObjectives && dashboardAgencyTro(dashboardBestAgency) !== null ? troBadge(dashboardAgencyTro(dashboardBestAgency)) : 'badge good'"
                  >
                    {{ hasObjectives && dashboardAgencyTro(dashboardBestAgency) !== null ? formatTro(dashboardAgencyTro(dashboardBestAgency)) : formatNumber(dashboardAgencyRealise(dashboardBestAgency)) }}
                  </span>
                </li>
                <li class="resume-zone">
                  <span class="dash-resume-icon" aria-hidden="true">🎖️</span>
                  <div class="dash-resume-text">
                    <span class="dash-resume-label">Meilleur territoire</span>
                    <strong class="dash-resume-value">{{ dashboardBestTerritory?.name || '—' }}</strong>
                  </div>
                  <span
                    v-if="dashboardBestTerritory"
                    :class="hasObjectives && dashboardTerritoryTro(dashboardBestTerritory) !== null ? troBadge(dashboardTerritoryTro(dashboardBestTerritory)) : 'badge good'"
                  >
                    {{ hasObjectives && dashboardTerritoryTro(dashboardBestTerritory) !== null ? formatTro(dashboardTerritoryTro(dashboardBestTerritory)) : formatNumber(dashboardTerritoryRealise(dashboardBestTerritory)) }}
                  </span>
                </li>
              </ul>
              <div class="status-legend"></div>
            </section>
          </div>
        </div>

        <div class="dash-rank-section">
          <div class="dash-rank-toolbar">
            <span class="dash-rank-toolbar-label">Classement agences</span>
            <span class="dash-rank-toolbar-meta">{{ dashboardAgencyRankMeta }}</span>
          </div>
          <div class="dash-row dash-row--2">
          <section class="dash-card dash-card--top">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent dash-card-accent--top" />
                <h3>Top 5 agences</h3>
              </div>
              <span class="dash-card-meta">{{ dashboardAgencyRankMeta }}</span>
            </div>
            <ol class="agency-rank">
              <li v-for="(row, idx) in dashboardTopAgencies" :key="row.id">
                <span class="rank" :class="idx === 0 ? 'rank-gold' : idx === 1 ? 'rank-silver' : idx === 2 ? 'rank-bronze' : 'rank-top'">{{ idx + 1 }}</span>
                <div class="meta">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.territory }}</span>
                </div>
                <span
                  v-if="hasObjectives && dashboardAgencyTro(row) !== null"
                  :class="troBadge(dashboardAgencyTro(row))"
                >
                  {{ formatTro(dashboardAgencyTro(row)) }}
                </span>
                <span v-else class="badge good">{{ formatNumber(dashboardAgencyRealise(row)) }}</span>
              </li>
              <li v-if="!dashboardTopAgencies.length" class="empty">Aucune donnée</li>
            </ol>
          </section>

          <section class="dash-card dash-card--flop">
            <div class="dash-card-head">
              <div class="dash-card-title">
                <span class="dash-card-accent dash-card-accent--flop" />
                <h3>Flop 5 agences</h3>
              </div>
              <span class="dash-card-meta">{{ dashboardAgencyRankMeta }}</span>
            </div>
            <ol class="agency-rank">
              <li v-for="(row, idx) in dashboardFlopAgencies" :key="row.id">
                <span class="rank rank-flop">{{ idx + 1 }}</span>
                <div class="meta">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.territory }}</span>
                </div>
                <span
                  v-if="hasObjectives && dashboardAgencyTro(row) !== null"
                  :class="troBadge(dashboardAgencyTro(row))"
                >
                  {{ formatTro(dashboardAgencyTro(row)) }}
                </span>
                <span v-else class="badge warn">{{ formatNumber(dashboardAgencyRealise(row)) }}</span>
              </li>
              <li v-if="!dashboardFlopAgencies.length" class="empty">Aucune donnée</li>
            </ol>
          </section>
          </div>
        </div>
      </div>

      <!-- ── PERFORMANCE DÉTAILLÉE ── -->
      <div v-if="viewMode === 'performance'" class="perf-view">
        <section class="perf-kpi-grid">
          <article class="perf-kpi perf-kpi--month">
            <div class="perf-kpi-main">
              <span class="perf-kpi-label">Réalisé du mois</span>
              <strong class="perf-kpi-value">{{ formatNumber(kpis.realiseM) }}</strong>
            </div>
            <div class="perf-kpi-side">
              <span class="perf-kpi-obj">
                Obj. {{ formatObj(kpis.objMensuel) }}
                <span v-if="kpis.troM !== null" :class="troBadge(kpis.troM)">{{ formatTro(kpis.troM) }}</span>
              </span>
              <span class="perf-kpi-meta">{{ monthLabel }} {{ selectedYear }}</span>
            </div>
          </article>
          <article class="perf-kpi perf-kpi--ytd">
            <div class="perf-kpi-main">
              <span class="perf-kpi-label">Réalisé YTD</span>
              <strong class="perf-kpi-value">{{ formatNumber(kpis.realiseYtd) }}</strong>
            </div>
            <div class="perf-kpi-side">
              <span class="perf-kpi-obj">
                Obj. {{ formatObj(kpis.objYtd) }}
                <span v-if="kpis.tro !== null" :class="troBadge(kpis.tro)">{{ formatTro(kpis.tro) }}</span>
              </span>
              <span class="perf-kpi-meta">Jan. → {{ monthLabel }}</span>
            </div>
          </article>
          <article class="perf-kpi perf-kpi--courants">
            <div class="perf-kpi-main">
              <span class="perf-kpi-label">Courants</span>
              <strong class="perf-kpi-value">{{ formatNumber(kpis.courantsYtd) }}</strong>
            </div>
            <span class="perf-kpi-meta">Mois : {{ formatNumber(kpis.courantsM) }}</span>
          </article>
          <article class="perf-kpi perf-kpi--epargne">
            <div class="perf-kpi-main">
              <span class="perf-kpi-label">Épargne</span>
              <strong class="perf-kpi-value">{{ formatNumber(kpis.epargneYtd) }}</strong>
            </div>
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
                    <th class="num col-objectif">Obj. YTD</th>
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
                    <td class="num col-objectif">{{ formatObj(row.objYtd) }}</td>
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
                    <td class="num col-objectif"><strong>{{ formatObj(kpis.objYtd) }}</strong></td>
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
                    <th class="num col-objectif">{{ perfTableMode === 'ytd' ? 'Obj. YTD' : 'Obj. mensuel' }}</th>
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
                      <td class="num col-objectif">{{ formatObj(perfObjSecondary(territory)) }}</td>
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
                        <td class="num col-objectif">{{ formatObj(perfObjSecondary(agency)) }}</td>
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
                    <td class="num col-objectif"><strong>{{ formatObj(perfTotals.objSecondary) }}</strong></td>
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

    <Teleport to="body">
      <div v-if="showSettings" class="co-modal-overlay" @click.self="closeSettings">
        <div class="co-modal" role="dialog" aria-labelledby="co-settings-title">
          <div class="co-modal-head">
            <h2 id="co-settings-title">Paramétrage — Comptes ouverts</h2>
            <button type="button" class="co-modal-close" aria-label="Fermer" @click="closeSettings">×</button>
          </div>
          <div class="co-modal-tabs" v-if="canEditSeuils">
            <button
              type="button"
              :class="{ active: settingsTab === 'seuils' }"
              @click="settingsTab = 'seuils'"
            >
              Seuils TRO
            </button>
            <button
              type="button"
              :class="{ active: settingsTab === 'objectifs' }"
              @click="settingsTab = 'objectifs'"
            >
              Objectifs
            </button>
          </div>

          <div v-if="settingsTab === 'seuils' && canEditSeuils" class="co-modal-body">
            <p class="co-modal-intro">Seuils TRO — réservés au DGA. Ils colorent le statut du tableau Performance territoire.</p>
            <ul class="seuil-editor">
              <li>
                <span class="status-orb good" />
                <label>
                  <span>≥</span>
                  <input v-model.number="seuilDraft.reached" type="number" min="1" max="200" step="0.1" />
                  <span>%</span>
                </label>
                <span class="seuil-label">objectif atteint/dépassé</span>
              </li>
              <li>
                <span class="status-orb close" />
                <label>
                  <input v-model.number="seuilDraft.close" type="number" min="1" max="200" step="0.1" />
                  <span>%</span>
                </label>
                <span class="seuil-label">proche de l'objectif</span>
              </li>
              <li>
                <span class="status-orb mid" />
                <label>
                  <input v-model.number="seuilDraft.vigilance" type="number" min="1" max="200" step="0.1" />
                  <span>%</span>
                </label>
                <span class="seuil-label">vigilance</span>
              </li>
              <li>
                <span class="status-orb bad" />
                <span class="seuil-fixed">&lt; {{ formatSeuil(seuilDraft.vigilance) }}</span>
                <span class="seuil-label">alerte</span>
              </li>
            </ul>
            <p v-if="seuilError" class="co-modal-error">{{ seuilError }}</p>
          </div>

          <div v-else class="co-modal-body">
            <p class="co-modal-intro">{{ objectivesIntro }}</p>
            <div v-if="dgaEnvelopeStats" class="co-modal-envelope" :class="{ 'is-over': dgaEnvelopeStats.isOver }">
              <span class="envelope-item">
                <span class="envelope-label">Objectif DGA</span>
                <strong class="envelope-value envelope-value--obj">{{ formatNumber(dgaEnvelopeStats.envelope) }}</strong>
              </span>
              <span class="envelope-sep">·</span>
              <span class="envelope-item">
                <span class="envelope-label">Réparti</span>
                <strong class="envelope-value" :class="{ 'envelope-value--over': dgaEnvelopeStats.isOver }">
                  {{ formatNumber(dgaEnvelopeStats.distributed) }}
                </strong>
              </span>
              <span class="envelope-sep">·</span>
              <span class="envelope-item">
                <span class="envelope-label">Reste</span>
                <strong class="envelope-value" :class="dgaEnvelopeStats.remaining < 0 ? 'envelope-value--over' : 'envelope-value--ok'">
                  {{ formatSigned(dgaEnvelopeStats.remaining) }}
                </strong>
              </span>
            </div>
            <p v-else-if="dgaEnvelopeMissingLabel" class="co-modal-envelope co-modal-envelope--muted">
              {{ dgaEnvelopeMissingLabel }}
            </p>
            <div v-if="canToggleObjectiveLevel" class="perf-mode-toggle" style="margin-bottom: 0.75rem;">
              <button
                type="button"
                :class="{ active: objectiveLevel === 'territoire' }"
                @click="switchObjectiveLevel('territoire')"
              >
                Territoires
              </button>
              <button
                type="button"
                :class="{ active: objectiveLevel === 'agence' }"
                @click="switchObjectiveLevel('agence')"
              >
                Agences
              </button>
            </div>
            <div class="obj-editor-wrap">
              <table class="obj-editor">
                <thead>
                  <tr>
                    <th>{{ objectiveLevel === 'territoire' ? 'Territoire' : 'Agence' }}</th>
                    <th v-if="objectiveLevel === 'agence'">Territoire</th>
                    <th class="num col-objectif">Objectif mensuel</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in objectiveDrafts" :key="row.key">
                    <td>{{ objectiveLevel === 'territoire' ? row.territory : row.agency_name }}</td>
                    <td v-if="objectiveLevel === 'agence'">{{ row.territory }}</td>
                    <td class="num">
                      <input
                        v-model.number="row.value"
                        type="number"
                        min="0"
                        step="1"
                        class="obj-input"
                      />
                    </td>
                  </tr>
                  <tr v-if="!objectiveDrafts.length">
                    <td :colspan="objectiveLevel === 'agence' ? 3 : 2" class="empty">{{ emptyObjectivesLabel }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-if="objectiveError" class="co-modal-error">{{ objectiveError }}</p>
            <p v-if="objectiveSuccess" class="co-modal-ok">{{ objectiveSuccess }}</p>
          </div>

          <div class="co-modal-foot">
            <button type="button" class="btn-ghost" @click="closeSettings">Fermer</button>
            <button
              v-if="settingsTab === 'seuils'"
              type="button"
              class="btn-refresh"
              :disabled="savingSeuils || !canEditSeuils"
              @click="saveThresholds"
            >
              {{ savingSeuils ? 'Enregistrement…' : 'Enregistrer les seuils' }}
            </button>
            <button
              v-if="settingsTab === 'objectifs'"
              type="button"
              class="btn-refresh"
              :disabled="savingObjectives || !canEditCurrentObjectives"
              @click="saveObjectives"
            >
              {{ savingObjectives ? 'Enregistrement…' : 'Enregistrer les objectifs' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import PythonChart from './charts/PythonChart.vue';
import { ProfileManager, PROFILES } from '../utils/profiles';

const DEFAULT_THRESHOLDS = { reached: 100, close: 90, vigilance: 70 };
const THRESHOLDS_STORAGE_KEY = 'comptes-ouverts-seuils';
const THRESHOLDS_API_KEY = 'comptes-ouverts-seuils';
const OBJECTIVE_TYPE = 'COMPTES_OUVERTS';
const TERRITORY_CODES = new Set([
  'DAKAR_VILLE',
  'DAKAR_BANLIEUE',
  'PROVINCE_CENTRE_SUD',
  'PROVINCE_NORD',
  'GRAND_COMPTE',
]);

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
      dashboardMode: 'ytd',
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
      ],
      payload: null,
      objectivesCatalog: [],
      expanded: {},
      showSettings: false,
      settingsTab: 'seuils',
      objectiveLevel: 'agence',
      thresholds: { ...DEFAULT_THRESHOLDS },
      seuilDraft: { ...DEFAULT_THRESHOLDS },
      seuilError: '',
      savingSeuils: false,
      objectiveDrafts: [],
      savingObjectives: false,
      objectiveError: '',
      objectiveSuccess: '',
    };
  },
  created() {
    this.loadStoredThresholds();
    this.loadRemoteThresholds();
  },
  computed: {
    profileCode() {
      return String(ProfileManager.getProfileCode() || '').toUpperCase();
    },
    canEditSeuils() {
      return this.profileCode === PROFILES.DGA || this.profileCode === PROFILES.ADMIN;
    },
    canEditTerritoryObjectives() {
      return this.profileCode === PROFILES.DGA || this.profileCode === PROFILES.ADMIN;
    },
    canEditAgencyObjectives() {
      return this.profileCode === PROFILES.RESPONSABLE_ZONE || this.profileCode === PROFILES.ADMIN;
    },
    canOpenSettings() {
      return this.canEditSeuils || this.canEditTerritoryObjectives || this.canEditAgencyObjectives;
    },
    canToggleObjectiveLevel() {
      return this.canEditTerritoryObjectives && this.canEditAgencyObjectives;
    },
    canEditCurrentObjectives() {
      return this.objectiveLevel === 'territoire'
        ? this.canEditTerritoryObjectives
        : this.canEditAgencyObjectives;
    },
    userTerritory() {
      return ProfileManager.getCurrentUser()?.territory || null;
    },
    userTerritoryCode() {
      const territory = this.userTerritory;
      const code = String(territory?.code || '').toUpperCase().trim();
      if (code && TERRITORY_CODES.has(code)) return code;
      if (territory?.name) return this.territoryFormCode(territory.name);
      return '';
    },
   
    emptyObjectivesLabel() {
      if (this.objectiveLevel === 'agence' && this.profileCode === PROFILES.RESPONSABLE_ZONE && !this.userTerritoryCode) {
        return 'Aucun territoire n’est associé à votre profil.';
      }
      return this.objectiveLevel === 'territoire'
        ? 'Chargez d’abord les données pour lister les territoires.'
        : 'Aucune agence à paramétrer pour votre territoire.';
    },
    dgaEnvelopeStats() {
      if (this.objectiveLevel !== 'agence' || !this.userTerritoryCode) return null;
      const envelope = Number(this.territoryObjectiveForCode(this.userTerritoryCode, this.selectedMonth) || 0);
      if (!envelope) return null;
      const distributed = this.objectiveDrafts.reduce((sum, row) => sum + (Number(row.value) || 0), 0);
      return {
        envelope,
        distributed,
        remaining: envelope - distributed,
        isOver: distributed > envelope,
      };
    },
    dgaEnvelopeMissingLabel() {
      if (this.objectiveLevel !== 'agence' || !this.userTerritoryCode) return '';
      const envelope = Number(this.territoryObjectiveForCode(this.userTerritoryCode, this.selectedMonth) || 0);
      if (envelope) return '';
      return 'Aucun objectif territoire n’a encore été fixé par le DGA.';
    },
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
    objectiveMapsByMonth() {
      const maps = {};
      for (let month = 1; month <= 12; month += 1) {
        maps[month] = this.buildObjectiveMaps(month);
      }
      return maps;
    },
    monthlyObjectiveTotals() {
      const totals = Array(13).fill(0);
      for (let month = 1; month <= 12; month += 1) {
        totals[month] = this.totalObjMensuelForMonth(month);
      }
      return totals;
    },
    cumulativeObjectiveYtdByMonth() {
      const cumulative = Array(13).fill(0);
      let running = 0;
      for (let month = 1; month <= 12; month += 1) {
        running += this.monthlyObjectiveTotals[month];
        cumulative[month] = running;
      }
      return cumulative;
    },
    kpis() {
      const realiseYtd = Number(this.rawKpis.realise_ytd || 0);
      const realiseM = Number(this.rawKpis.realise_m || 0);
      const courantsYtd = Number(this.rawKpis.realise_ytd_251 || 0);
      const epargneYtd = Number(this.rawKpis.realise_ytd_253 || 0);
      const objMensuel = this.monthlyObjectiveTotals[this.selectedMonth] || 0;
      const objYtd = this.cumulativeObjectiveYtdByMonth[this.selectedMonth] || 0;
      const hasObj = objYtd > 0;
      const objAnnuel = this.cumulativeObjectiveYtdByMonth[12] || 0;
      const tro = hasObj ? (realiseYtd / objYtd) * 100 : null;
      const courantsM = Number(this.rawKpis.realise_m_251 || 0);
      const epargneM = Number(this.rawKpis.realise_m_253 || 0);
      const troM = objMensuel > 0 ? (realiseM / objMensuel) * 100 : null;
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
      return this.monthlyObjectiveTotals[this.selectedMonth] || 0;
    },
    hasObjectives() {
      return (this.cumulativeObjectiveYtdByMonth[this.selectedMonth] || 0) > 0;
    },
    monthlyRows() {
      const rows = this.payload?.monthly || [];
      return rows.map((row) => {
        const objMensuel = row.month <= this.selectedMonth
          ? (this.monthlyObjectiveTotals[row.month] || 0)
          : 0;
        const objYtd = row.month <= this.selectedMonth
          ? (this.cumulativeObjectiveYtdByMonth[row.month] || 0)
          : 0;
        const tro = objYtd > 0 ? (Number(row.ytd || 0) / objYtd) * 100 : null;
        return {
          ...row,
          objMensuel,
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
          const objMensuel = this.agencyObjMensuel(agency, this.selectedMonth);
          const objYtd = this.agencyObjYtd(agency, this.selectedMonth);
          return {
            ...agency,
            objMensuel,
            objYtd,
            objAnnuel: this.agencyObjYtd(agency, 12),
            tro: this.tro(agency.realise_ytd, objYtd),
          };
        });
        const objMensuel = this.territoryObjMensuel(territory, this.selectedMonth);
        const objYtd = this.territoryObjYtd(territory, this.selectedMonth);
        return {
          ...territory,
          agencies,
          objMensuel,
          objYtd,
          objAnnuel: this.territoryObjYtd(territory, 12),
          tro: this.tro(territory.realise_ytd, objYtd),
          troM: this.tro(territory.realise_m, objMensuel),
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
            realise_m: a.realise_m,
            objMensuel: a.objMensuel,
            objYtd: a.objYtd,
            tro: a.tro,
            troM: this.tro(a.realise_m, a.objMensuel),
          });
        }
      }
      return list;
    },
    rankedAgenciesForDashboard() {
      const isMonth = this.dashboardMode === 'month';
      const ranked = [...this.allAgencies]
        .map((agency) => ({
          agency,
          metric: this.agencyRankMetric(agency, isMonth),
        }))
        .filter((item) => item.metric !== null)
        .sort((a, b) => {
          if (a.metric.kind !== b.metric.kind) {
            return a.metric.kind === 'tro' ? -1 : 1;
          }
          return b.metric.value - a.metric.value;
        });
      return ranked.map((item) => item.agency);
    },
    dashboardTerritoryMeta() {
      if (!this.hasObjectives) {
        return this.dashboardMode === 'month' ? 'Réalisé mois' : 'Réalisé YTD';
      }
      return this.dashboardMode === 'month' ? 'TRO mois' : 'TRO YTD';
    },
    dashboardAgencyRankMeta() {
      if (!this.hasObjectives) {
        return this.dashboardMode === 'month' ? 'Ouvertures mois' : 'Ouvertures YTD';
      }
      return this.dashboardMode === 'month' ? 'TRO mois' : 'TRO YTD';
    },
    dashboardTopAgencies() {
      return this.rankedAgenciesForDashboard.slice(0, 5);
    },
    dashboardFlopAgencies() {
      return [...this.rankedAgenciesForDashboard].reverse().slice(0, 5);
    },
    dashboardTerritoryRows() {
      const isMonth = this.dashboardMode === 'month';
      const ranked = [...this.territories]
        .map((territory) => ({
          territory,
          metric: this.territoryRankMetric(territory, isMonth),
        }))
        .filter((item) => item.metric !== null)
        .sort((a, b) => {
          if (a.metric.kind !== b.metric.kind) {
            return a.metric.kind === 'tro' ? -1 : 1;
          }
          return b.metric.value - a.metric.value;
        });
      return ranked.map((item) => item.territory);
    },
    dashboardBestAgency() {
      return this.dashboardTopAgencies[0] || null;
    },
    dashboardBestTerritory() {
      return this.dashboardTerritoryRows[0] || null;
    },
    monthlyChartType() {
      return 'multiseries';
    },
    monthlyChartMeta() {
      return this.hasObjectives
        ? 'Cumul objectif vs réalisé'
        : 'Ouvertures cumulées';
    },
    monthlyChartData() {
      const rows = this.monthlyRowsVisible;
      const labels = rows.map((r) => r.label);
      const realiseYtd = rows.map((r) => Number(r.ytd != null ? r.ytd : r.total) || 0);
      if (this.hasObjectives) {
        return {
          labels,
          series: {
            Objectif: rows.map((r) => Number(r.objYtd) || 0),
            Réalisé: realiseYtd,
          },
          title: '',
          xlabel: 'Mois',
          ylabel: 'Ouvertures',
          colors: ['#2563EB', '#16a34a'],
        };
      }
      return {
        labels,
        series: {
          Réalisé: realiseYtd,
        },
        title: '',
        xlabel: 'Mois',
        ylabel: 'Ouvertures',
        colors: ['#16a34a'],
      };
    },
  },
  mounted() {
    this.loadData();
  },
  methods: {
    agencyRankMetric(agency, isMonth = this.dashboardMode === 'month') {
      const realise = Number(isMonth ? agency.realise_m : agency.realise_ytd) || 0;
      if (this.hasObjectives) {
        const tro = isMonth ? agency.troM : agency.tro;
        const obj = Number(isMonth ? agency.objMensuel : agency.objYtd) || 0;
        if (tro !== null && obj > 0) {
          return { kind: 'tro', value: Number(tro) };
        }
      }
      if (realise > 0) {
        return { kind: 'realise', value: realise };
      }
      return null;
    },
    territoryRankMetric(territory, isMonth = this.dashboardMode === 'month') {
      const realise = Number(isMonth ? territory.realise_m : territory.realise_ytd) || 0;
      if (this.hasObjectives) {
        const tro = isMonth ? territory.troM : territory.tro;
        const obj = Number(isMonth ? territory.objMensuel : territory.objYtd) || 0;
        if (tro !== null && obj > 0) {
          return { kind: 'tro', value: Number(tro) };
        }
      }
      if (realise > 0) {
        return { kind: 'realise', value: realise };
      }
      return null;
    },
    dashboardAgencyTro(row) {
      return this.dashboardMode === 'month' ? row.troM : row.tro;
    },
    dashboardAgencyRealise(row) {
      return this.dashboardMode === 'month' ? row.realise_m : row.realise_ytd;
    },
    dashboardTerritoryObj(row) {
      return this.dashboardMode === 'month' ? row.objMensuel : row.objYtd;
    },
    dashboardTerritoryRealise(row) {
      return this.dashboardMode === 'month' ? row.realise_m : row.realise_ytd;
    },
    dashboardTerritoryTro(row) {
      return this.dashboardMode === 'month' ? row.troM : row.tro;
    },
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
      return `${Number(value).toLocaleString('fr-FR', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })} %`;
    },
    formatSeuil(value) {
      const n = Number(value);
      if (Number.isNaN(n)) return '—';
      return `${n.toLocaleString('fr-FR', {
        minimumFractionDigits: Number.isInteger(n) ? 0 : 1,
        maximumFractionDigits: 1,
      })} %`;
    },
    tro(realise, objectif) {
      const obj = Number(objectif || 0);
      if (obj <= 0) return null;
      return (Number(realise || 0) / obj) * 100;
    },
    troTone(value) {
      const level = this.troLevel(value);
      if (level === 'good') return 'kpi-good';
      if (level === 'close') return 'kpi-close';
      if (level === 'mid') return 'kpi-warn';
      if (level === 'bad') return 'kpi-bad';
      return 'kpi-neutral';
    },
    troBadge(value) {
      const level = this.troLevel(value);
      if (level === 'good') return 'badge good';
      if (level === 'close') return 'badge close';
      if (level === 'mid') return 'badge mid';
      if (level === 'bad') return 'badge bad';
      return 'badge muted';
    },
    territoryStatusClass(value) {
      return this.troLevel(value);
    },
    troLevel(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return 'muted';
      const n = Number(value);
      if (n >= this.thresholds.reached) return 'good';
      if (n >= this.thresholds.close) return 'close';
      if (n >= this.thresholds.vigilance) return 'mid';
      return 'bad';
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
    toggleTerritory(key) {
      this.expanded = { ...this.expanded, [key]: !this.expanded[key] };
    },
    objectiveForAgency(agency, month = this.selectedMonth) {
      return this.agencyObjMensuel(agency, month);
    },
    agencyObjMensuel(agency, month) {
      const maps = this.objectiveMapsByMonth[month] || this.buildObjectiveMaps(month);
      const code = String(agency.branch_code || '').trim();
      if (code && maps.byCode[code] != null) {
        return Number(maps.byCode[code]) || 0;
      }
      const name = String(agency.branch_name || '').toUpperCase().trim();
      if (name && maps.byName[name] != null) {
        return Number(maps.byName[name]) || 0;
      }
      return 0;
    },
    agencyObjYtd(agency, month) {
      let sum = 0;
      for (let m = 1; m <= month; m += 1) {
        sum += this.agencyObjMensuel(agency, m);
      }
      return sum;
    },
    territoryObjectiveForCode(territoryCode, month) {
      const maps = this.objectiveMapsByMonth[month] || this.buildObjectiveMaps(month);
      return Number(maps.byTerritory[String(territoryCode || '').toUpperCase()] || 0);
    },
    territoryObjMensuel(territory, month) {
      const agencies = territory.agencies || [];
      const agencySum = agencies.reduce(
        (sum, agency) => sum + this.agencyObjMensuel(agency, month),
        0,
      );
      if (agencySum > 0) return agencySum;
      return this.territoryObjectiveForCode(this.territoryFormCode(territory.name), month);
    },
    territoryObjYtd(territory, month) {
      let sum = 0;
      for (let m = 1; m <= month; m += 1) {
        sum += this.territoryObjMensuel(territory, m);
      }
      return sum;
    },
    totalObjMensuelForMonth(month) {
      const list = this.payload?.territories || [];
      return list.reduce((sum, territory) => sum + this.territoryObjMensuel(territory, month), 0);
    },
    loadStoredThresholds() {
      try {
        const raw = localStorage.getItem(THRESHOLDS_STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        const next = this.normalizeThresholds(parsed);
        if (next) {
          this.thresholds = next;
          this.seuilDraft = { ...next };
        }
      } catch {
        /* ignore */
      }
    },
    normalizeThresholds(input) {
      const reached = Number(input?.reached);
      const close = Number(input?.close);
      const vigilance = Number(input?.vigilance);
      if (![reached, close, vigilance].every((n) => Number.isFinite(n) && n > 0 && n <= 200)) {
        return null;
      }
      if (!(reached > close && close > vigilance)) return null;
      return { reached, close, vigilance };
    },
    openSettings() {
      this.seuilDraft = { ...this.thresholds };
      this.seuilError = '';
      this.objectiveError = '';
      this.objectiveSuccess = '';
      this.objectiveLevel = this.canEditAgencyObjectives && !this.canEditTerritoryObjectives
        ? 'agence'
        : 'territoire';
      this.settingsTab = this.canEditSeuils ? 'seuils' : 'objectifs';
      this.objectiveDrafts = this.buildObjectiveDrafts();
      this.showSettings = true;
    },
    closeSettings() {
      this.showSettings = false;
    },
    switchObjectiveLevel(level) {
      this.objectiveLevel = level;
      this.objectiveError = '';
      this.objectiveSuccess = '';
      this.objectiveDrafts = this.buildObjectiveDrafts();
    },
    async saveThresholds() {
      const next = this.normalizeThresholds(this.seuilDraft);
      if (!next) {
        this.seuilError = 'Les seuils doivent être décroissants : atteint > proche > vigilance, entre 1 et 200.';
        return;
      }
      this.savingSeuils = true;
      this.seuilError = '';
      try {
        const response = await window.axios.put(`/api/settings/${THRESHOLDS_API_KEY}`, next, {
          headers: this.authHeaders(),
        });
        const saved = this.normalizeThresholds(response.data?.data) || next;
        this.applyThresholds(saved);
        this.showSettings = false;
      } catch (err) {
        this.seuilError =
          err?.response?.data?.message ||
          err?.message ||
          'Impossible d’enregistrer les seuils.';
      } finally {
        this.savingSeuils = false;
      }
    },
    applyThresholds(next) {
      this.thresholds = next;
      this.seuilDraft = { ...next };
      localStorage.setItem(THRESHOLDS_STORAGE_KEY, JSON.stringify(next));
    },
    async loadRemoteThresholds() {
      try {
        const response = await window.axios.get(`/api/settings/${THRESHOLDS_API_KEY}`, {
          headers: this.authHeaders(),
        });
        const next = this.normalizeThresholds(response.data?.data);
        if (next) this.applyThresholds(next);
      } catch {
        /* keep local / defaults */
      }
    },
    buildObjectiveDrafts() {
      if (this.objectiveLevel === 'territoire') {
        return this.territories.map((territory) => {
          const code = this.territoryFormCode(territory.name);
          return {
            key: `territory-${territory.key || code}`,
            level: 'territoire',
            territory: territory.name,
            territoryCode: code,
            category: this.agencyCategory(territory.name),
            agency_code: code,
            agency_name: territory.name,
            value: Number(this.territoryObjectiveForCode(code, this.selectedMonth) || 0) || null,
          };
        });
      }
      const rows = [];
      for (const territory of this.territories) {
        const territoryCode = this.territoryFormCode(territory.name);
        if (this.profileCode === PROFILES.RESPONSABLE_ZONE && this.userTerritoryCode
          && territoryCode !== this.userTerritoryCode) {
          continue;
        }
        for (const agency of territory.agencies || []) {
          const code = String(agency.branch_code || '').trim();
          const name = String(agency.branch_name || '').trim();
          if (!code && !name) continue;
          rows.push({
            key: `${territory.key}-${code || name}`,
            level: 'agence',
            territory: territory.name,
            territoryCode,
            category: this.agencyCategory(territory.name),
            agency_code: code || name,
            agency_name: name || code,
            value: this.objectiveForAgency(agency) || null,
          });
        }
      }
      return rows;
    },
    territoryFormCode(name) {
      const n = String(name || '').toUpperCase();
      if (n.includes('BANLIEUE')) return 'DAKAR_BANLIEUE';
      if (n.includes('GRAND')) return 'GRAND_COMPTE';
      if (n.includes('NORD')) return 'PROVINCE_NORD';
      if (n.includes('CENTRE SUD') || n.includes('CENTRE-SUD')) return 'PROVINCE_CENTRE_SUD';
      if (n.includes('DAKAR') || n.includes('VILLE')) return 'DAKAR_VILLE';
      return n.replace(/\s+/g, '_');
    },
    agencyCategory(name) {
      return String(name || '').toUpperCase().includes('GRAND') ? 'GRAND COMPTE' : 'TERRITOIRE';
    },
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    objectivePriorityScoreForMonth(obj, month) {
      const period = String(obj?.period || 'month');
      if (period === 'month') {
        return Number(obj.month) === month ? 300 : 0;
      }
      if (period === 'quarter') {
        const quarter = Math.ceil(month / 3);
        return Number(obj.quarter) === quarter ? 200 : 0;
      }
      if (period === 'year') return 100;
      return 0;
    },
    monthlyObjectiveValue(obj) {
      const value = Number(obj?.value || 0);
      if (!value) return 0;
      const period = String(obj?.period || 'month');
      if (period === 'year') return value / 12;
      if (period === 'quarter') return value / 3;
      return value;
    },
    buildObjectiveMaps(month) {
      const byCode = {};
      const byName = {};
      const byTerritory = {};
      const ranked = (Array.isArray(this.objectivesCatalog) ? this.objectivesCatalog : [])
        .filter((obj) => ['validated', 'pending_validation'].includes(String(obj?.status || 'validated')))
        .map((obj) => ({
          obj,
          score: this.objectivePriorityScoreForMonth(obj, month),
          monthly: this.monthlyObjectiveValue(obj),
        }))
        .filter((item) => item.score > 0 && item.monthly > 0)
        .sort((a, b) => b.score - a.score);

      ranked.forEach(({ obj, monthly }) => {
        const code = String(obj.agency_code || '').trim().toUpperCase();
        const name = String(obj.agency_name || '').toUpperCase().trim();
        if (TERRITORY_CODES.has(code)) {
          if (byTerritory[code] == null) byTerritory[code] = monthly;
          return;
        }
        if (code && byCode[code] == null) byCode[code] = monthly;
        if (name && byName[name] == null) byName[name] = monthly;
      });

      return { byCode, byName, byTerritory };
    },
    async fetchObjectives(type) {
      const response = await window.axios.get('/api/objectives', {
        params: {
          type,
          year: this.selectedYear,
        },
        headers: this.authHeaders(),
      });
      return response.data?.success ? response.data.data : [];
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
        this.objectivesCatalog = await this.fetchObjectives(OBJECTIVE_TYPE);
      } catch {
        this.objectivesCatalog = [];
      }
    },
    async saveObjectives() {
      this.objectiveError = '';
      this.objectiveSuccess = '';
      const rows = this.objectiveDrafts.filter((row) => row.value !== null && row.value !== '' && Number(row.value) >= 0);
      if (!rows.length) {
        this.objectiveError = 'Saisissez au moins un objectif mensuel.';
        return;
      }
      if (this.dgaEnvelopeStats?.isOver) {
        this.objectiveError = `La répartition (${this.formatNumber(this.dgaEnvelopeStats.distributed)}) dépasse l’objectif DGA (${this.formatNumber(this.dgaEnvelopeStats.envelope)}).`;
        return;
      }
      this.savingObjectives = true;
      try {
        const results = await Promise.all(rows.map((row) => window.axios.post('/api/objectives', {
          type: OBJECTIVE_TYPE,
          category: row.level === 'territoire' ? 'TERRITOIRE' : row.category,
          territory: row.territoryCode,
          agency_code: row.agency_code,
          agency_name: row.agency_name,
          value: Number(row.value) || 0,
          period: 'month',
          month: this.selectedMonth,
          year: this.selectedYear,
        }, { headers: this.authHeaders() })));
        const pending = results.some((res) => res.data?.data?.status === 'pending_validation');
        await this.loadObjectives();
        this.objectiveDrafts = this.buildObjectiveDrafts();
        this.objectiveSuccess = pending
          ? 'Objectifs enregistrés et en attente de validation.'
          : 'Objectifs enregistrés.';
      } catch (err) {
        this.objectiveError =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          'Impossible d’enregistrer les objectifs.';
      } finally {
        this.savingObjectives = false;
      }
    },
  },
};
</script>

<style scoped>
.comptes-ouverts,
.co-modal-overlay {
  --ink: #1e293b;
  --muted: #64748b;
  --line: #e2e8f0;
  --brand: #dc2626;
  --brand-dark: #b91c1c;
  --row-dark: #2a2a2a;
  --row-mid: #4a4a4a;
  --green: #16a34a;
  --green-soft: #dcfce7;
  --green-dark: #166534;
  --green-mid: #22c55e;
  --green-light: #f0fdf4;
  --green-bar: #4ade80;
  --slate: #475569;
  --slate-soft: #94a3b8;
  --gold: #ca8a04;
  --gold-soft: #fef9c3;
  --gold-dark: #854d0e;
  --warn: #d97706;
  --warn-soft: #fef3c7;
  --bad: #dc2626;
  --bad-soft: #fef2f2;
  --surface: #f8fafb;
  --head-bg: #dc2626;
  --card-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 2px 8px rgba(15, 23, 42, 0.03);
}

.comptes-ouverts {
  padding: 0 0 2rem;
  color: var(--ink);
}

/* ── Barre outils (onglets + filtres) ── */
.toolbar-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.85rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--line);
}

.toolbar-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
}

.toolbar-nav .btn-settings {
  min-height: auto;
  padding: 0.55rem 0.9rem;
  font-size: 0.84rem;
}

.period-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
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
.btn-refresh,
.btn-settings {
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
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
  font-weight: 600;
  background: var(--brand);
  color: #fff;
  border-color: var(--brand);
  padding: 0 1.1rem;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--brand-dark);
  border-color: var(--brand-dark);
}

.btn-refresh:disabled {
  opacity: 0.65;
  cursor: default;
}

.btn-settings {
  cursor: pointer;
  font-weight: 600;
  background: #fff;
  color: var(--ink);
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
  border-color: rgba(220, 38, 38, 0.2);
  border-top-color: var(--brand);
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
  color: var(--brand);
  background: rgba(220, 38, 38, 0.06);
}

.view-tab.active {
  color: #fff;
  font-weight: 600;
  background: var(--brand);
  box-shadow: 0 2px 6px rgba(220, 38, 38, 0.25);
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
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 0.65rem;
}

.kpi-grid--5 .kpi {
  flex: 1 1 180px;
}

.kpi {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.55rem 0.65rem;
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.kpi-body {
  flex: 1;
  min-width: 0;
}

.kpi-icon {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.85rem;
  height: 1.85rem;
  border-radius: 8px;
}

.kpi-icon svg {
  width: 0.95rem;
  height: 0.95rem;
}

.kpi-label {
  display: block;
  font-size: 0.62rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--slate);
  margin-bottom: 0.08rem;
  font-weight: 700;
  white-space: nowrap;
}

.kpi-value {
  display: block;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
  color: var(--ink);
}

.kpi-meta {
  flex-shrink: 0;
  font-size: 0.62rem;
  color: var(--muted);
  text-align: right;
  white-space: nowrap;
  line-height: 1.25;
}

.kpi-obj {
  box-shadow: inset 3px 0 0 #2563eb, var(--card-shadow);
}

.kpi-obj .kpi-icon {
  background: #eff6ff;
  color: #2563eb;
}

.kpi-obj .kpi-value {
  color: #1d4ed8;
}

.kpi-ytd {
  box-shadow: inset 3px 0 0 #2563eb, var(--card-shadow);
}

.kpi-ytd .kpi-icon {
  background: #eff6ff;
  color: #2563eb;
}

.kpi-ytd .kpi-value {
  color: #1d4ed8;
}

.kpi-realise {
  box-shadow: inset 3px 0 0 var(--brand), var(--card-shadow);
}

.kpi-realise .kpi-icon {
  background: #fef2f2;
  color: var(--brand);
}

.kpi-realise .kpi-value {
  color: var(--ink);
}

.kpi-good {
  box-shadow: inset 3px 0 0 var(--green), var(--card-shadow);
}

.kpi-good .kpi-icon {
  background: #ecfdf5;
  color: var(--green);
}

.kpi-good .kpi-value {
  color: var(--green-dark);
}

.kpi-close {
  box-shadow: inset 3px 0 0 var(--gold), var(--card-shadow);
}

.kpi-close .kpi-icon {
  background: var(--gold-soft);
  color: var(--gold);
}

.kpi-close .kpi-value {
  color: var(--gold-dark);
}

.kpi-warn {
  box-shadow: inset 3px 0 0 var(--warn), var(--card-shadow);
}

.kpi-warn .kpi-icon {
  background: var(--warn-soft);
  color: var(--warn);
}

.kpi-warn .kpi-value {
  color: #b45309;
}

.kpi-bad {
  box-shadow: inset 3px 0 0 var(--brand), var(--card-shadow);
}

.kpi-bad .kpi-icon {
  background: #fef2f2;
  color: var(--brand);
}

.kpi-bad .kpi-value {
  color: var(--brand);
}

.kpi-neutral {
  box-shadow: inset 3px 0 0 var(--slate-soft), var(--card-shadow);
}

.kpi-neutral .kpi-icon {
  background: #f1f5f9;
  color: var(--slate);
}

.kpi-neutral .kpi-value {
  color: var(--ink);
}

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

.dash-rank-section {
  margin-bottom: 0.85rem;
}

.dash-rank-section .dash-row--2 {
  margin-bottom: 0;
}

.dash-rank-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  margin-bottom: 0.45rem;
}

.dash-rank-toolbar-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
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

.dash-card-head,
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding: 0.8rem 1rem;
  background: #fff;
  color: var(--ink);
  border-bottom: 2px solid var(--brand);
}

.dash-card--top .dash-card-head,
.dash-card--flop .dash-card-head,
.panel--territory .panel-head {
  background: #fff;
  border-bottom-color: var(--brand);
}

.dash-card-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.dash-card-accent {
  display: none;
}

.dash-card-head h3,
.panel-head h3 {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--ink);
}

.dash-card-meta,
.panel-head-meta {
  font-size: 0.72rem;
  color: var(--muted);
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

.dash-mode-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  padding: 0.35rem 0.15rem 0;
}

.dash-mode-bar-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--muted);
}

.dash-rank-toolbar-meta {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
}

/* ── Territoire ── */
.territory-table-wrap {
  overflow-x: auto;
}

.territory-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.territory-table th,
.territory-table td {
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid #eef2f6;
  text-align: left;
  white-space: nowrap;
}

.territory-table thead th {
  background: #f1f5f9;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.territory-table tbody tr:last-child td {
  border-bottom: none;
}

.territory-table tbody tr.is-lead td:first-child {
  color: var(--ink);
}

.territory-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.territory-table .col-tro {
  font-weight: 700;
  color: var(--ink);
}

.territory-table .col-objectif,
.perf-table .col-objectif {
  color: #2563eb;
  font-weight: 600;
}

.perf-table thead .col-objectif {
  color: #fff;
}

.territory-table .col-status {
  text-align: center;
  width: 3.2rem;
}

.territory-table .empty {
  text-align: center;
  color: var(--muted);
  padding: 0.85rem 0.5rem;
}

.status-orb {
  display: inline-block;
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 50%;
  vertical-align: middle;
  box-shadow:
    inset -1px -1px 3px rgba(0, 0, 0, 0.18),
    inset 1px 1px 2px rgba(255, 255, 255, 0.5);
}

.status-orb.good {
  background: radial-gradient(circle at 32% 28%, #86efac, #16a34a 70%);
}

.status-orb.close {
  background: radial-gradient(circle at 32% 28%, #fde047, #ca8a04 70%);
}

.status-orb.mid {
  background: radial-gradient(circle at 32% 28%, #fdba74, #ea580c 70%);
}

.status-orb.bad {
  background: radial-gradient(circle at 32% 28%, #fca5a5, #dc2626 70%);
}

.status-orb.muted {
  background: radial-gradient(circle at 32% 28%, #e2e8f0, #94a3b8 70%);
}

.status-legend {
  list-style: none;
  margin: 0;
  padding: 0.55rem 0.7rem 0.75rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem 0.85rem;
  border-top: 1px solid #f1f5f9;
}

.status-legend li {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  color: var(--muted);
}

/* ── Résumé période ── */
.dash-card--resume {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #f8fafc;
}

.resume-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem 0.55rem;
  background: #fff;
  border-bottom: 1px solid #f1f5f9;
}

.resume-card-head h3 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
  position: relative;
  padding-left: 0.65rem;
  letter-spacing: -0.01em;
}

.resume-card-head h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0.95rem;
  border-radius: 2px;
  background: linear-gradient(180deg, #1a4d3a 0%, #0f766e 100%);
}

.dash-resume-list {
  list-style: none;
  margin: 0;
  padding: 0.65rem 1rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.dash-resume-list li {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.6rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #eef2f7;
}

.dash-resume-list li.resume-agency {
  background: linear-gradient(90deg, #fff7ed 0%, #f8fafc 55%);
  border-color: #ffedd5;
}

.dash-resume-list li.resume-zone {
  background: linear-gradient(90deg, #ecfdf5 0%, #f8fafc 55%);
  border-color: #d1fae5;
}

.dash-resume-icon {
  flex: 0 0 auto;
  width: 1.85rem;
  height: 1.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #fff;
  font-size: 1rem;
  line-height: 1;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.dash-resume-text {
  flex: 1 1 auto;
  min-width: 0;
}

.dash-resume-label {
  display: block;
  font-size: 0.68rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
  margin-bottom: 0.15rem;
}

.dash-resume-value {
  display: block;
  font-size: 0.86rem;
  color: #0f172a;
  font-weight: 700;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-resume-list .badge {
  flex: 0 0 auto;
}

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
  background: #fee2e2;
  color: var(--brand);
}

.rank-gold {
  background: #fef3c7;
  color: #92400e;
  box-shadow: 0 0 0 1px #fcd34d;
}

.rank-silver {
  background: #f1f4f6;
  color: var(--slate);
  box-shadow: 0 0 0 1px #dde3e8;
}

.rank-bronze {
  background: #f3eeea;
  color: #7a6555;
  box-shadow: 0 0 0 1px #e0d5cc;
}

.rank-flop {
  background: #f5f5f5;
  color: var(--row-mid);
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

.badge.good { background: var(--green-soft); color: var(--green-dark); }
.badge.close { background: var(--gold-soft); color: var(--gold-dark); }
.badge.mid { background: var(--warn-soft); color: var(--warn); }
.badge.warn { background: #f3ece0; color: #7a6538; }
.badge.bad { background: var(--bad-soft); color: var(--brand-dark); }
.badge.muted, .muted { color: var(--slate-soft); }

/* ── Performance view ── */
.perf-view {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.perf-kpi-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 0.65rem;
}

.perf-kpi {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  flex: 1 1 220px;
  min-width: 0;
  max-width: 100%;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.55rem 0.7rem;
  box-shadow: var(--card-shadow);
}

.perf-kpi-main {
  min-width: 0;
}

.perf-kpi-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.15rem;
  flex-shrink: 0;
  text-align: right;
}

.perf-kpi-label {
  display: block;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--slate);
  margin-bottom: 0.1rem;
  white-space: nowrap;
}

.perf-kpi-value {
  display: block;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
  color: var(--ink);
}

.perf-kpi-meta {
  display: block;
  font-size: 0.66rem;
  color: var(--muted);
  white-space: nowrap;
}

.perf-kpi-obj {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.3rem;
  font-size: 0.68rem;
  font-weight: 650;
  color: #2563eb;
  white-space: nowrap;
}

.perf-kpi-obj .badge {
  min-width: 2.6rem;
  padding: 0.12rem 0.35rem;
  font-size: 0.62rem;
}

.perf-kpi--month {
  box-shadow: inset 3px 0 0 var(--brand), var(--card-shadow);
}

.perf-kpi--ytd {
  box-shadow: inset 3px 0 0 #2563eb, var(--card-shadow);
}

.perf-kpi--courants {
  box-shadow: inset 3px 0 0 #64748b, var(--card-shadow);
}

.perf-kpi--epargne {
  box-shadow: inset 3px 0 0 #16a34a, var(--card-shadow);
}

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
  padding: 0.8rem 1rem;
  background: #fff;
  color: var(--ink);
  border-bottom: 2px solid var(--brand);
}

.panel-head-title {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.panel-head h3 {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--ink);
}

.panel-head-meta {
  font-size: 0.72rem;
  color: var(--muted);
}

.panel-head--split {
  flex-wrap: wrap;
  gap: 0.65rem;
}

.perf-mode-toggle {
  display: inline-flex;
  padding: 3px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  gap: 2px;
  flex-shrink: 0;
}

.perf-mode-toggle button {
  padding: 0.35rem 0.85rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.perf-mode-toggle button:hover {
  color: var(--ink);
  background: #fff;
}

.perf-mode-toggle button.active {
  color: #fff;
  background: var(--brand);
  box-shadow: 0 1px 3px rgba(220, 38, 38, 0.25);
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
  padding: 0.65rem 0.9rem;
  border-bottom: 1px solid #eef2f6;
  text-align: left;
}

.perf-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: var(--head-bg);
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #fff;
  font-weight: 600;
  white-space: nowrap;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  border-bottom: none;
  text-align: center;
  padding: 0.7rem 0.9rem;
}

.perf-table thead th:first-child {
  text-align: left;
}

.perf-table tbody tr:nth-child(even) {
  background: #fafbfc;
}

.perf-table tbody tr:hover {
  background: #f4f6f8;
}

.perf-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.perf-table tbody .col-highlight {
  background: transparent;
  font-weight: 600;
  color: var(--ink);
}

.perf-table thead .col-highlight {
  background: var(--brand-dark);
  color: #fff;
}

.perf-table .row-current {
  background: #fff !important;
  box-shadow: inset 3px 0 0 var(--brand);
}

.perf-table .row-current:hover {
  background: #fafafa !important;
}

.perf-table .row-current .col-highlight {
  color: var(--brand);
}

.month-tag {
  display: inline-flex;
  min-width: 2.4rem;
  justify-content: center;
  padding: 0.15rem 0.45rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: var(--slate);
  background: #f1f5f9;
}

.month-tag--current {
  color: #fff;
  background: var(--brand);
}

.perf-table--territory tbody tr:nth-child(even) {
  background: transparent;
}

.perf-table--territory .territory-row td {
  background: #f5f5f5;
  color: var(--ink);
  font-weight: 600;
  font-size: 0.84rem;
  border-bottom: 1px solid #eee;
  box-shadow: inset 3px 0 0 var(--brand);
}

.perf-table--territory .territory-row:hover td {
  background: #efefef;
}

.perf-table--territory .territory-row--open td {
  background: #f0f0f0;
  border-bottom-color: #e5e5e5;
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
  color: var(--ink);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-size: 0.78rem;
}

.perf-table--territory .territory-row .col-highlight {
  background: transparent;
  color: var(--ink);
  font-weight: 700;
}

.perf-table--territory .agency-row .col-highlight {
  background: transparent;
  font-weight: 500;
  color: var(--slate);
}

.perf-table--territory .agency-row td {
  background: #fff;
  color: var(--slate);
  font-weight: 400;
  font-size: 0.82rem;
  border-bottom: 1px solid #f1f5f9;
  box-shadow: none;
}

.perf-table--territory .agency-row:hover td {
  background: #fafbfc;
}

.perf-table--territory .agency-row td:first-child {
  background: #fff;
  border-left: 3px solid #f1f5f9;
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
  background: var(--row-dark);
  color: #fff;
}

.perf-tfoot td {
  border-bottom: none;
  padding: 0.75rem 0.85rem;
  font-variant-numeric: tabular-nums;
}

.perf-tfoot .col-highlight {
  background: transparent;
  color: #fff;
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
  background: var(--brand);
  border-color: var(--brand);
  color: #fff;
}

.expand-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
}

.perf-table--territory .territory-row .expand-btn {
  border-color: #ccc;
  background: #fff;
  color: var(--slate);
}

.perf-table--territory .territory-row .expand-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
  background: #fff;
}

.perf-table--territory .territory-row .expand-btn.open {
  background: var(--brand);
  border-color: var(--brand);
  color: #fff;
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
  .kpi-grid--5 .kpi {
    flex: 1 1 calc(33.333% - 0.45rem);
  }
  .dash-row--2,
  .dash-row--chart {
    grid-template-columns: 1fr;
  }
  .kpi-mini,
  .perf-kpi-grid {
    flex-direction: column;
  }

  .perf-kpi {
    flex-basis: auto;
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
  .toolbar-nav {
    width: 100%;
  }
  .view-tabs {
    width: 100%;
    display: flex;
  }
  .view-tab {
    flex: 1;
    text-align: center;
  }
  .kpi-grid--5 .kpi,
  .kpi-mini {
    flex: 1 1 100%;
  }

  .perf-kpi-grid {
    flex-direction: column;
  }
}

.co-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.45);
}

.co-modal {
  width: min(760px, 100%);
  max-height: min(90vh, 820px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.co-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.95rem 1.1rem;
  border-bottom: 1px solid var(--line);
}

.co-modal-head h2 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.co-modal-close {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 8px;
  background: #f1f5f9;
  color: var(--slate);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
}

.co-modal-tabs {
  display: flex;
  gap: 0.35rem;
  padding: 0.65rem 1.1rem 0;
}

.co-modal-tabs button {
  border: none;
  background: transparent;
  padding: 0.45rem 0.7rem;
  font-size: 0.82rem;
  font-weight: 650;
  color: var(--muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.co-modal-tabs button.active {
  color: var(--brand);
  border-bottom-color: var(--brand);
}

.co-modal-body {
  padding: 0.9rem 1.1rem 1rem;
  overflow: auto;
  min-height: 0;
}

.co-modal-intro {
  margin: 0 0 0.85rem;
  font-size: 0.82rem;
  color: var(--muted);
}

.co-modal-envelope {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem 0.65rem;
  margin: -0.2rem 0 0.65rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #f8fbff;
}

.co-modal-envelope.is-over {
  border-color: #fecaca;
  background: #fff7f7;
}

.co-modal-envelope--muted {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  background: #f8fafc;
  border-color: var(--line);
}

.envelope-item {
  display: inline-flex;
  align-items: baseline;
  gap: 0.35rem;
}

.envelope-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}

.envelope-value {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--ink);
}

.envelope-value--obj {
  color: #2563eb;
}

.envelope-value--ok {
  color: var(--green-dark);
}

.envelope-value--over {
  color: var(--brand);
}

.envelope-sep {
  color: #cbd5e1;
  font-weight: 700;
}

.co-modal-error {
  margin: 0.75rem 0 0;
  color: var(--brand-dark);
  font-size: 0.82rem;
  font-weight: 600;
}

.co-modal-ok {
  margin: 0.75rem 0 0;
  color: var(--green-dark);
  font-size: 0.82rem;
  font-weight: 600;
}

.seuil-editor {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.seuil-editor li {
  display: grid;
  grid-template-columns: 1.1rem minmax(8rem, auto) 1fr;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 0.75rem;
  border: 1px solid var(--line);
  border-radius: 10px;
}

.seuil-editor label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 650;
  font-size: 0.84rem;
}

.seuil-editor input {
  width: 4.5rem;
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0 0.45rem;
  font-size: 0.88rem;
}

.seuil-label,
.seuil-fixed {
  font-size: 0.82rem;
  color: var(--ink);
}

.obj-editor-wrap {
  overflow: auto;
  max-height: 22rem;
  border: 1px solid var(--line);
  border-radius: 10px;
}

.obj-editor {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.obj-editor th,
.obj-editor td {
  padding: 0.3rem 0.55rem;
  border-bottom: 1px solid #eef2f6;
  text-align: left;
}

.obj-editor thead th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}

.obj-editor .num {
  text-align: right;
  width: 8.5rem;
}

.obj-input {
  width: 5.5rem;
  min-height: 28px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0 0.4rem;
  text-align: right;
  font-size: 0.82rem;
}

.co-modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 0.55rem;
  padding: 0.8rem 1.1rem;
  border-top: 1px solid var(--line);
  background: #f8fafc;
}

.co-modal-foot .btn-refresh {
  background: #dc2626;
  border-color: #dc2626;
  color: #fff;
}

.co-modal-foot .btn-refresh:hover:not(:disabled) {
  background: #b91c1c;
  border-color: #b91c1c;
}

.btn-ghost {
  min-height: 38px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  padding: 0 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-settings:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}
</style>
