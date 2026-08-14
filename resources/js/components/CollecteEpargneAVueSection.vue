<template>
  <div class="collecte-epargne-a-vue-section">
    <div class="section-header">
      <div class="title-block">
        <h2 class="section-title">Collecte d'épargne à vue</h2>
        <p class="section-subtitle">{{ periodTitle }}</p>
      </div>
      <div class="period-selector">
        <label class="period-label">
          Période
          <select v-model.number="selectedMonth" class="month-select" @change="loadData(false)">
            <option v-for="(month, index) in months" :key="index" :value="index + 1">
              {{ month }}
            </option>
          </select>
        </label>
        <select v-model.number="selectedYear" class="year-select" @change="loadData(false)">
          <option v-for="year in years" :key="year" :value="year">
            {{ year }}
          </option>
        </select>
        <button
          type="button"
          class="btn-refresh"
          :disabled="loading"
          title="Recharge le snapshot du matin (rapide)"
          @click="loadData(false)"
        >
          Actualiser
        </button>
        <button
          type="button"
          class="btn-recalc"
          :disabled="loading || recalculating"
          title="Recalcule depuis Flexcube et met à jour le snapshot (lent)"
          @click="forceRecalc"
        >
          {{ recalculating ? 'Recalcul…' : 'Recalculer Flexcube' }}
        </button>
        <button
          type="button"
          class="btn-freeze"
          :disabled="loading || freezing"
          title="Figer les objectifs du mois sélectionné (normalement au 1er du mois)"
          @click="freezeObjectifs"
        >
          {{ freezing ? 'Figement…' : 'Figer objectifs' }}
        </button>
      </div>
    </div>

    <div class="epv-view-tabs">
      <button
        type="button"
        class="epv-view-tab"
        :class="{ active: viewMode === 'dashboard' }"
        :disabled="!hasTerritoires && !loading"
        @click="viewMode = 'dashboard'"
      >
        Dashboard
      </button>
      <button
        type="button"
        class="epv-view-tab"
        :class="{ active: viewMode === 'collecte' }"
        @click="viewMode = 'collecte'"
      >
        Collecte d'épargne à vue
      </button>
      <button
        type="button"
        class="epv-view-tab"
        :class="{ active: viewMode === 'evolution' }"
        :disabled="!hasTerritoires && !loading"
        @click="viewMode = 'evolution'"
      >
        Évolution
      </button>
    </div>

    <div v-if="loading" class="loading-message">
      {{ loadingHint }}
    </div>
    <div v-else-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>

    <div v-if="!loading && !errorMessage && hasTerritoires && viewMode === 'collecte'" class="kpi-strip">
      <div class="kpi-card">
        <span class="kpi-label">Objectif </span>
        <strong class="kpi-value">{{ formatCurrency(grandTotal.objectif) }}</strong>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Réalisation</span>
        <strong class="kpi-value">{{ formatCurrency(grandTotal.collecteM) }}</strong>
      </div>
      <div class="kpi-card kpi-card--accent">
        <span class="kpi-label">Taux de réalisation</span>
        <strong class="kpi-value" :class="troClass(grandTotal.tro)">{{ formatTro(grandTotal.tro) }}</strong>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Écart (Réal. − Obj.)</span>
        <strong class="kpi-value" :class="ecartClass(grandTotal.collecteM - grandTotal.objectif)">
          {{ formatCurrency(grandTotal.collecteM - grandTotal.objectif) }}
        </strong>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Total dépôts</span>
        <strong class="kpi-value">{{ formatCurrency(grandTotal.totalDepot) }}</strong>
      </div>
    </div>

    <div v-if="viewMode === 'collecte'" class="panel">
      <div class="panel-header">
        <h3 class="panel-title">Collecte d'épargne à vue</h3>
        <span v-if="hasTerritoires" class="panel-meta">
          Réalisation mesurée par rapport à l’objectif mensuel figé — territoire → agence → CAF → client
        </span>
      </div>

      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th class="col-tree">Agence</th>
              <th>Code CAF</th>
              <th>Chargé d'affaire</th>
              <th>Matricule</th>
              <th>N° compte</th>
              <th class="col-left">Client</th>
              <th class="col-num">Mt financé</th>
              <th class="col-num">Objectif fixé</th>
              <th class="col-num">Encours crédit</th>
              <th class="col-num">Échéance</th>
              <th class="col-num">Total dépôt</th>
              <th class="col-num">Réalisation</th>
              <th class="col-num">Taux réal.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!loading && !errorMessage && !hasTerritoires" class="no-data-row">
              <td colspan="13">Aucune donnée disponible pour la période sélectionnée.</td>
            </tr>

            <tr
              v-if="hasTerritoires"
              class="level-1-row"
              @click="toggleExpand('TERRITOIRE')"
            >
              <td class="level-1">
                <button class="expand-btn" type="button" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <span>TERRITOIRE</span>
              </td>
              <td colspan="5" class="muted">—</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.cumMontantFinance) }}</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.objectif) }}</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.encoursCredit) }}</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.mtEcheance) }}</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.totalDepot) }}</td>
              <td class="col-num">{{ formatCurrency(territoireTotal.collecteM) }}</td>
              <td class="col-num"><span :class="troBadge(territoireTotal.tro)">{{ formatTro(territoireTotal.tro) }}</span></td>
            </tr>

            <template v-if="expandedSections.TERRITOIRE">
              <template v-for="(territory, territoryKey) in hierarchicalData.TERRITOIRE" :key="territoryKey">
                <template v-if="territoryKey !== 'grand_compte'">
                  <tr
                    class="level-2-row"
                    @click="toggleExpand(`TERRITOIRE_${territoryKey}`); setActiveLevel('zone', territoryKey, territory.name)"
                  >
                    <td class="level-2">
                      <button
                        class="expand-btn"
                        type="button"
                        @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)"
                      >
                        {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                      </button>
                      <span>{{ territory.name }}</span>
                    </td>
                    <td colspan="5" class="muted">—</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.cumMontantFinance) }}</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.objectif) }}</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.encoursCredit) }}</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.mtEcheance) }}</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.totalDepot) }}</td>
                    <td class="col-num">{{ formatCurrency(territory.totals?.collecteM) }}</td>
                    <td class="col-num"><span :class="troBadge(territory.totals?.tro)">{{ formatTro(territory.totals?.tro) }}</span></td>
                  </tr>

                  <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                    <template
                      v-for="(agency, index) in (territory.agencies || [])"
                      :key="agencyKey(agency, index)"
                    >
                      <tr
                        class="level-3-row"
                        :class="{ selected: isSelectedAgency(agency, territoryKey) }"
                        @click="selectAgency(agency, territoryKey)"
                      >
                        <td class="level-3">
                          <button
                            v-if="(agency.chargeAffaireDetails || []).length"
                            class="expand-btn"
                            type="button"
                            @click.stop="toggleExpand(agencyExpandKey(territoryKey, agency, index))"
                          >
                            {{ expandedSections[agencyExpandKey(territoryKey, agency, index)] ? '−' : '+' }}
                          </button>
                          <span class="agency-name">{{ agencyDisplayName(agency) }}</span>
                        </td>
                        <td>{{ agencyCodeGestion(agency) }}</td>
                        <td class="col-left">{{ agencyCharge(agency) }}</td>
                        <td class="muted">—</td>
                        <td class="muted">—</td>
                        <td class="muted">—</td>
                        <td class="col-num">{{ formatCurrency(agency.cumMontantFinance) }}</td>
                        <td class="col-num">{{ formatCurrency(agency.objectif) }}</td>
                        <td class="col-num">{{ formatCurrency(agency.encoursCredit) }}</td>
                        <td class="col-num">{{ formatCurrency(agency.mtEcheance) }}</td>
                        <td class="col-num">{{ formatCurrency(agency.totalDepot) }}</td>
                        <td class="col-num">{{ formatCurrency(agency.collecteM) }}</td>
                        <td class="col-num"><span :class="troBadge(agency.tro)">{{ formatTro(agency.tro) }}</span></td>
                      </tr>

                      <template v-if="expandedSections[agencyExpandKey(territoryKey, agency, index)]">
                        <template
                          v-for="(charge, cIdx) in (agency.chargeAffaireDetails || [])"
                          :key="`${agencyKey(agency, index)}-${cIdx}`"
                        >
                          <tr
                            class="level-4-row"
                            @click.stop="toggleExpand(cafExpandKey(territoryKey, agency, index, cIdx))"
                          >
                            <td class="level-4">
                              <button
                                v-if="(charge.clients || []).length"
                                class="expand-btn expand-btn--sm"
                                type="button"
                                @click.stop="toggleExpand(cafExpandKey(territoryKey, agency, index, cIdx))"
                              >
                                {{ expandedSections[cafExpandKey(territoryKey, agency, index, cIdx)] ? '−' : '+' }}
                              </button>
                              <span class="branch-chip">{{ agency.BRANCH_CODE || agency.branch_code }}</span>
                            </td>
                            <td><code class="code-caf">{{ charge.codeGestion || charge.CODE_CAF || '—' }}</code></td>
                            <td class="col-left">{{ charge.chargeAffaire || charge.CHARGE_AFFAIRE || '—' }}</td>
                            <td class="muted">—</td>
                            <td class="muted">—</td>
                            <td class="muted">{{ (charge.clients || []).length }} client(s)</td>
                            <td class="col-num">{{ formatCurrency(charge.cumMontantFinance) }}</td>
                            <td class="col-num">{{ formatCurrency(charge.objectif) }}</td>
                            <td class="col-num">{{ formatCurrency(charge.encoursCredit) }}</td>
                            <td class="col-num">{{ formatCurrency(charge.mtEcheance) }}</td>
                            <td class="col-num">{{ formatCurrency(charge.totalDepot) }}</td>
                            <td class="col-num">{{ formatCurrency(charge.collecteM) }}</td>
                            <td class="col-num"><span :class="troBadge(charge.tro)">{{ formatTro(charge.tro) }}</span></td>
                          </tr>

                          <template v-if="expandedSections[cafExpandKey(territoryKey, agency, index, cIdx)]">
                            <tr
                              v-for="(client, clIdx) in (charge.clients || [])"
                              :key="`${agencyKey(agency, index)}-${cIdx}-c-${clIdx}`"
                              class="level-5-row"
                            >
                              <td class="level-5 muted">Client</td>
                              <td><code class="code-caf">{{ client.CODE_CAF || charge.codeGestion }}</code></td>
                              <td class="col-left">{{ client.CHARGE_AFFAIRE || charge.chargeAffaire }}</td>
                              <td>{{ client.MATRICULE_CLIENT || '—' }}</td>
                              <td><code class="compte">{{ client.NUMERO_COMPTE || '—' }}</code></td>
                              <td class="col-left client-name">{{ client.NOM_CLIENT || '—' }}</td>
                              <td class="col-num">{{ formatCurrency(client.CUM_MONTANT_FINANCE) }}</td>
                              <td class="col-num">{{ formatCurrency(client.OBJ_COL_EPV_VUE) }}</td>
                              <td class="col-num">{{ formatCurrency(client.CUM_ENCOURS_CREDIT) }}</td>
                              <td class="col-num">{{ formatCurrency(client.MONTANT_ECHEANCE) }}</td>
                              <td class="col-num">{{ formatCurrency(client.TOTAL_DEPOT) }}</td>
                              <td class="col-num">{{ formatCurrency(client.COL_EP_VUE) }}</td>
                              <td class="col-num"><span :class="troBadge(client.tro)">{{ formatTro(client.tro) }}</span></td>
                            </tr>
                          </template>
                        </template>
                      </template>
                    </template>
                  </template>
                </template>
              </template>
            </template>

            <template v-if="grandCompte">
              <tr class="grand-compte-row" @click="toggleExpand('GRAND_COMPTE')">
                <td class="level-2">
                  <button
                    v-if="(grandCompte.chargeAffaireDetails || []).length"
                    class="expand-btn"
                    type="button"
                    @click.stop="toggleExpand('GRAND_COMPTE')"
                  >
                    {{ expandedSections.GRAND_COMPTE ? '−' : '+' }}
                  </button>
                  <span>Grand compte ({{ grandCompte.BRANCH_CODE || '526' }})</span>
                </td>
                <td>{{ agencyCodeGestion(grandCompte) }}</td>
                <td class="col-left">{{ agencyCharge(grandCompte) }}</td>
                <td class="muted">—</td>
                <td class="muted">—</td>
                <td class="muted">—</td>
                <td class="col-num">{{ formatCurrency(grandCompte.cumMontantFinance) }}</td>
                <td class="col-num">{{ formatCurrency(grandCompte.objectif) }}</td>
                <td class="col-num">{{ formatCurrency(grandCompte.encoursCredit) }}</td>
                <td class="col-num">{{ formatCurrency(grandCompte.mtEcheance) }}</td>
                <td class="col-num">{{ formatCurrency(grandCompte.totalDepot) }}</td>
                <td class="col-num">{{ formatCurrency(grandCompte.collecteM) }}</td>
                <td class="col-num"><span :class="troBadge(grandCompte.tro)">{{ formatTro(grandCompte.tro) }}</span></td>
              </tr>

              <template v-if="expandedSections.GRAND_COMPTE">
                <template
                  v-for="(charge, cIdx) in (grandCompte.chargeAffaireDetails || [])"
                  :key="`gc-${cIdx}`"
                >
                  <tr
                    class="level-4-row"
                    @click.stop="toggleExpand(`GRAND_COMPTE_CAF_${cIdx}`)"
                  >
                    <td class="level-3">
                      <button
                        v-if="(charge.clients || []).length"
                        class="expand-btn expand-btn--sm"
                        type="button"
                        @click.stop="toggleExpand(`GRAND_COMPTE_CAF_${cIdx}`)"
                      >
                        {{ expandedSections[`GRAND_COMPTE_CAF_${cIdx}`] ? '−' : '+' }}
                      </button>
                      <span class="branch-chip">{{ grandCompte.BRANCH_CODE || '526' }}</span>
                    </td>
                    <td><code class="code-caf">{{ charge.codeGestion || charge.CODE_CAF || '—' }}</code></td>
                    <td class="col-left">{{ charge.chargeAffaire || charge.CHARGE_AFFAIRE || '—' }}</td>
                    <td class="muted">—</td>
                    <td class="muted">—</td>
                    <td class="muted">{{ (charge.clients || []).length }} client(s)</td>
                    <td class="col-num">{{ formatCurrency(charge.cumMontantFinance) }}</td>
                    <td class="col-num">{{ formatCurrency(charge.objectif) }}</td>
                    <td class="col-num">{{ formatCurrency(charge.encoursCredit) }}</td>
                    <td class="col-num">{{ formatCurrency(charge.mtEcheance) }}</td>
                    <td class="col-num">{{ formatCurrency(charge.totalDepot) }}</td>
                    <td class="col-num">{{ formatCurrency(charge.collecteM) }}</td>
                    <td class="col-num"><span :class="troBadge(charge.tro)">{{ formatTro(charge.tro) }}</span></td>
                  </tr>

                  <template v-if="expandedSections[`GRAND_COMPTE_CAF_${cIdx}`]">
                    <tr
                      v-for="(client, clIdx) in (charge.clients || [])"
                      :key="`gc-${cIdx}-c-${clIdx}`"
                      class="level-5-row"
                    >
                      <td class="level-4 muted">Client</td>
                      <td><code class="code-caf">{{ client.CODE_CAF || charge.codeGestion }}</code></td>
                      <td class="col-left">{{ client.CHARGE_AFFAIRE || charge.chargeAffaire }}</td>
                      <td>{{ client.MATRICULE_CLIENT || '—' }}</td>
                      <td><code class="compte">{{ client.NUMERO_COMPTE || '—' }}</code></td>
                      <td class="col-left client-name">{{ client.NOM_CLIENT || '—' }}</td>
                      <td class="col-num">{{ formatCurrency(client.CUM_MONTANT_FINANCE) }}</td>
                      <td class="col-num">{{ formatCurrency(client.OBJ_COL_EPV_VUE) }}</td>
                      <td class="col-num">{{ formatCurrency(client.CUM_ENCOURS_CREDIT) }}</td>
                      <td class="col-num">{{ formatCurrency(client.MONTANT_ECHEANCE) }}</td>
                      <td class="col-num">{{ formatCurrency(client.TOTAL_DEPOT) }}</td>
                      <td class="col-num">{{ formatCurrency(client.COL_EP_VUE) }}</td>
                      <td class="col-num"><span :class="troBadge(client.tro)">{{ formatTro(client.tro) }}</span></td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>

            <tr v-if="hasTerritoires" class="total-row">
              <td>TOTAL</td>
              <td colspan="5" class="muted">—</td>
              <td class="col-num">{{ formatCurrency(grandTotal.cumMontantFinance) }}</td>
              <td class="col-num">{{ formatCurrency(grandTotal.objectif) }}</td>
              <td class="col-num">{{ formatCurrency(grandTotal.encoursCredit) }}</td>
              <td class="col-num">{{ formatCurrency(grandTotal.mtEcheance) }}</td>
              <td class="col-num">{{ formatCurrency(grandTotal.totalDepot) }}</td>
              <td class="col-num">{{ formatCurrency(grandTotal.collecteM) }}</td>
              <td class="col-num"><span :class="troBadge(grandTotal.tro)">{{ formatTro(grandTotal.tro) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="hasTerritoires && viewMode === 'evolution'" class="chart-evolution-section">
      <div class="chart-header">
        <div class="chart-title-section">
          <h3 class="chart-section-title">{{ chartTitle }}</h3>
          <div v-if="activeLevel.type !== 'total'" class="breadcrumb">
            <span class="breadcrumb-item" @click="resetToTotal">Total</span>
            <template v-if="activeLevel.type === 'zone' || activeLevel.type === 'agency'">
              <span class="breadcrumb-separator">/</span>
              <span class="breadcrumb-item">{{ activeLevel.zoneName || activeLevel.zone }}</span>
            </template>
            <template v-if="activeLevel.type === 'agency'">
              <span class="breadcrumb-separator">/</span>
              <span class="breadcrumb-item active">{{ activeLevel.name }}</span>
            </template>
          </div>
        </div>
        <div class="chart-actions">
          <button type="button" class="export-btn" @click="exportChart('png')">PNG</button>
          <button type="button" class="export-btn" @click="exportChart('pdf')">PDF</button>
          <button type="button" class="export-btn" @click="exportCsv">CSV</button>
        </div>
      </div>

      <div class="chart-view-tabs">
        <button
          type="button"
          :class="['chart-view-tab', { active: chartViewMode === 'graph' }]"
          @click="chartViewMode = 'graph'"
        >
          Graphique
        </button>
        <button
          type="button"
          :class="['chart-view-tab', { active: chartViewMode === 'performance' }]"
          @click="chartViewMode = 'performance'"
        >
          Performance
        </button>
      </div>

      <div v-if="chartViewMode === 'graph'">
        <div class="chart-toolbar">
          <div class="chart-tabs">
            <button
              v-for="t in chartTypes"
              :key="t.value"
              type="button"
              :class="['chart-tab', { active: selectedChartType === t.value }]"
              @click="selectedChartType = t.value"
            >
              {{ t.label }}
            </button>
          </div>
        </div>

        <div class="chart-wrapper-container">
          <PythonChart
            :key="`epv-${selectedChartType}-${activeLevel.type}-${activeLevel.zone || ''}-${activeLevel.name || ''}`"
            :chartType="resolvedChartType"
            :chartData="currentChartData"
            :height="520"
            ref="chartComponent"
          />
        </div>
      </div>

      <div v-else class="performance-panel">
        <div class="perf-cards">
          <div class="perf-card">
            <span class="label">Objectif {{ objectifsFiges ? 'figé' : 'live' }}</span>
            <strong>{{ formatCurrency(activeMetrics.objectif) }}</strong>
          </div>
          <div class="perf-card">
            <span class="label">Réalisation</span>
            <strong>{{ formatCurrency(activeMetrics.collecteM) }}</strong>
          </div>
          <div class="perf-card highlight">
            <span class="label">Taux de réalisation</span>
            <strong :class="troClass(activeMetrics.tro)">{{ formatTro(activeMetrics.tro) }}</strong>
          </div>
          <div class="perf-card">
            <span class="label">Écart (Réalisation − Objectif)</span>
            <strong :class="ecartClass(activeMetrics.collecteM - activeMetrics.objectif)">
              {{ formatCurrency(activeMetrics.collecteM - activeMetrics.objectif) }}
            </strong>
          </div>
        </div>

        <div class="perf-toolbar">
          <div class="perf-level-tabs">
            <button
              type="button"
              :class="['perf-level-tab', { active: perfLevel === 'territoire' }]"
              @click="setPerfLevel('territoire')"
            >
              Territoires
            </button>
            <button
              type="button"
              :class="['perf-level-tab', { active: perfLevel === 'agence' }]"
              @click="setPerfLevel('agence')"
            >
              Agences
            </button>
            <button
              type="button"
              :class="['perf-level-tab', { active: perfLevel === 'caf' }]"
              @click="setPerfLevel('caf')"
            >
              Chargés d'affaires
            </button>
          </div>
          <div class="perf-breadcrumb" v-if="perfFilterLabel">
            <button type="button" class="perf-crumb" @click="clearPerfFilter">Tous</button>
            <span class="perf-crumb-sep">/</span>
            <span class="perf-crumb-current">{{ perfFilterLabel }}</span>
          </div>
        </div>

        <div class="perf-table-wrap">
          <table class="perf-table">
            <thead>
              <tr>
                <th class="col-rank">#</th>
                <th>{{ perfNameHeader }}</th>
                <th v-if="perfLevel !== 'territoire'" class="col-parent">{{ perfParentHeader }}</th>
                <th class="col-num">Objectif</th>
                <th class="col-num">Réalisation</th>
                <th class="col-num">Écart</th>
                <th class="col-tro">Taux</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!performanceRows.length">
                <td :colspan="perfLevel === 'territoire' ? 6 : 7" class="perf-empty">
                  Aucune donnée pour ce niveau.
                </td>
              </tr>
              <tr
                v-for="(row, idx) in performanceRows"
                :key="row.id"
                :class="{ clickable: row.drillable }"
                @click="row.drillable && drillPerfRow(row)"
              >
                <td class="col-rank">
                  <span :class="['rank-badge', rankBadgeClass(idx)]">{{ idx + 1 }}</span>
                </td>
                <td class="col-name">
                  <span class="perf-name">{{ row.name }}</span>
                  <span v-if="row.subtitle" class="perf-sub">{{ row.subtitle }}</span>
                </td>
                <td v-if="perfLevel !== 'territoire'" class="col-parent">{{ row.parent }}</td>
                <td class="col-num">{{ formatCurrency(row.objectif) }}</td>
                <td class="col-num">{{ formatCurrency(row.collecteM) }}</td>
                <td class="col-num" :class="ecartClass(row.ecart)">{{ formatCurrency(row.ecart) }}</td>
                <td class="col-tro">
                  <div class="tro-cell">
                    <div class="tro-bar-track">
                      <div
                        class="tro-bar-fill"
                        :class="troClass(row.tro)"
                        :style="{ width: troBarWidth(row.tro) }"
                      />
                    </div>
                    <span :class="['tro-value', troClass(row.tro)]">{{ formatTro(row.tro) }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div
      v-if="!loading && !errorMessage && hasTerritoires && viewMode === 'dashboard'"
      ref="dashboardRoot"
      class="epv-dashboard"
      :style="dashboardStyle"
    >
      <div class="dash-kpi-grid">
        <div class="dash-kpi objectif">
          <span class="dash-kpi-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg>
          </span>
          <div class="dash-kpi-body">
            <span class="dash-kpi-label">Objectif figé</span>
            <strong class="dash-kpi-value">{{ formatCurrency(grandTotal.objectif) }} <small>FCFA</small></strong>
          </div>
        </div>
        <div class="dash-kpi collecte">
          <span class="dash-kpi-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 7H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
          </span>
          <div class="dash-kpi-body">
            <span class="dash-kpi-label">Collecte réalisée</span>
            <strong class="dash-kpi-value">{{ formatCurrency(grandTotal.collecteM) }} <small>FCFA</small></strong>
          </div>
        </div>
        <div class="dash-kpi taux">
          <span class="dash-kpi-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>
          </span>
          <div class="dash-kpi-body">
            <span class="dash-kpi-label">Taux de réalisation</span>
            <strong class="dash-kpi-value" :class="troClass(grandTotal.tro)">{{ formatTro(grandTotal.tro) }}</strong>
          </div>
        </div>
        <div class="dash-kpi ecart">
          <span class="dash-kpi-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7l6 6 4-4 8 8"/><path d="M14 17h7v-7"/></svg>
          </span>
          <div class="dash-kpi-body">
            <span class="dash-kpi-label">Écart à l’objectif</span>
            <strong class="dash-kpi-value" :class="ecartClass(grandTotal.collecteM - grandTotal.objectif)">
              {{ formatCurrency(grandTotal.collecteM - grandTotal.objectif) }} <small>FCFA</small>
            </strong>
          </div>
        </div>
        <div class="dash-kpi comptes">
          <span class="dash-kpi-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
          </span>
          <div class="dash-kpi-body">
            <span class="dash-kpi-label">Nombre de clients</span>
            <strong class="dash-kpi-value">{{ formatCurrency(dashboardClientCount) }}</strong>
          </div>
        </div>
      </div>

      <div class="dash-charts-row">
        <div class="dash-card dash-chart-main">
          <div class="dash-card-head">
            <h4>Courbe de suivi — Évolution du mois</h4>
            <div class="dash-mini-stats">
              <div class="dash-chip collecte">
                <span>Réalisé</span>
                <strong>{{ formatCurrency(grandTotal.collecteM) }}</strong>
              </div>
              <div class="dash-chip objectif">
                <span>Objectif</span>
                <strong>{{ formatCurrency(grandTotal.objectif) }}</strong>
              </div>
              <div class="dash-chip taux">
                <span>Taux</span>
                <strong :class="troClass(grandTotal.tro)">{{ formatTro(grandTotal.tro) }}</strong>
              </div>
            </div>
          </div>
          <PythonChart
            :key="`dash-line-${selectedMonth}-${selectedYear}`"
            chartType="multiseries"
            :chartData="dashboardLineChartData"
            :height="240"
          />
        </div>
        <div class="dash-card dash-chart-side">
          <div class="dash-card-head">
            <h4>Répartition de la collecte</h4>
          </div>
          <PythonChart
            :key="`dash-pie-${selectedMonth}-${selectedYear}`"
            chartType="pie"
            :chartData="dashboardPieChartData"
            :height="240"
          />
        </div>
        <div class="dash-card dash-resume">
          <div class="dash-card-head">
            <h4>Résumé période</h4>
          </div>
          <ul class="dash-resume-list">
          
            <li class="resume-caf">
              <span class="dash-resume-icon" aria-hidden="true">🥇</span>
              <div class="dash-resume-text">
                <span class="dash-resume-label">Meilleur CAF</span>
                <strong class="dash-resume-value">{{ dashboardBestCaf?.name || '—' }}</strong>
              </div>
              <span v-if="dashboardBestCaf" :class="troBadge(dashboardBestCaf.tro)">
                {{ formatTro(dashboardBestCaf.tro) }}
              </span>
            </li>
            <li class="resume-agency">
              <span class="dash-resume-icon" aria-hidden="true">🏆</span>
              <div class="dash-resume-text">
                <span class="dash-resume-label">Meilleure agence</span>
                <strong class="dash-resume-value">{{ dashboardBestAgency?.name || '—' }}</strong>
              </div>
              <span v-if="dashboardBestAgency" :class="troBadge(dashboardBestAgency.tro)">
                {{ formatTro(dashboardBestAgency.tro) }}
              </span>
            </li>
            <li class="resume-zone">
              <span class="dash-resume-icon" aria-hidden="true">🎖️</span>
              <div class="dash-resume-text">
                <span class="dash-resume-label">Meilleur territoire</span>
                <strong class="dash-resume-value">{{ dashboardBestZone?.name || '—' }}</strong>
              </div>
              <span v-if="dashboardBestZone" :class="troBadge(dashboardBestZone.tro)">
                {{ formatTro(dashboardBestZone.tro) }}
              </span>
            </li>
          </ul>
        </div>
      </div>

      <div class="dash-tables-row">
        <div class="dash-card">
          <div class="dash-card-head"><h4>Réalisation par CAF</h4></div>
          <div class="dash-rank-split">
            <div>
              <div class="dash-rank-title top"><span class="dash-rank-dot top"></span>Top 5</div>
              <ol class="dash-rank-list">
                <li v-for="(row, idx) in dashboardTopCafs" :key="`top-caf-${row.id}`">
                  <span class="rank rank-top">{{ idx + 1 }}</span>
                  <div class="meta">
                    <strong>{{ row.name }}</strong>
                    <span>{{ row.parent }}</span>
                  </div>
                  <span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                </li>
                <li v-if="!dashboardTopCafs.length" class="empty">Aucune donnée</li>
              </ol>
            </div>
            <div>
              <div class="dash-rank-title flop"><span class="dash-rank-dot flop"></span>Flop 5</div>
              <ol class="dash-rank-list">
                <li v-for="(row, idx) in dashboardFlopCafs" :key="`flop-caf-${row.id}`">
                  <span class="rank rank-flop">{{ idx + 1 }}</span>
                  <div class="meta">
                    <strong>{{ row.name }}</strong>
                    <span>{{ row.parent }}</span>
                  </div>
                  <span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                </li>
                <li v-if="!dashboardFlopCafs.length" class="empty">Aucune donnée</li>
              </ol>
            </div>
          </div>
        </div>

        <div class="dash-card">
          <div class="dash-card-head"><h4>Réalisation par agence</h4></div>
          <div class="dash-rank-split">
            <div>
              <div class="dash-rank-title top"><span class="dash-rank-dot top"></span>Top 5</div>
              <ol class="dash-rank-list">
                <li v-for="(row, idx) in dashboardTopAgencies" :key="`top-${row.id}`">
                  <span class="rank rank-top">{{ idx + 1 }}</span>
                  <div class="meta">
                    <strong>{{ row.name }}</strong>
                  </div>
                  <span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                </li>
                <li v-if="!dashboardTopAgencies.length" class="empty">Aucune donnée</li>
              </ol>
            </div>
            <div>
              <div class="dash-rank-title flop"><span class="dash-rank-dot flop"></span>Flop 5</div>
              <ol class="dash-rank-list">
                <li v-for="(row, idx) in dashboardFlopAgencies" :key="`flop-${row.id}`">
                  <span class="rank rank-flop">{{ idx + 1 }}</span>
                  <div class="meta">
                    <strong>{{ row.name }}</strong>
                  </div>
                  <span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span>
                </li>
                <li v-if="!dashboardFlopAgencies.length" class="empty">Aucune donnée</li>
              </ol>
            </div>
          </div>
        </div>

        <div class="dash-card">
          <div class="dash-card-head"><h4>Réalisation par territoire</h4></div>
          <div class="dash-table-wrap">
            <table class="dash-table">
              <thead>
                <tr>
                  <th>Territoire</th>
                  <th class="col-num">Objectif</th>
                  <th class="col-num">Réalisé</th>
                  <th class="col-num">Taux</th>
                  <th class="col-num">Écart</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in dashboardZoneRows" :key="row.id">
                  <td><strong>{{ row.name }}</strong></td>
                  <td class="col-num">{{ formatCurrency(row.objectif) }}</td>
                  <td class="col-num">{{ formatCurrency(row.collecteM) }}</td>
                  <td class="col-num"><span :class="troBadge(row.tro)">{{ formatTro(row.tro) }}</span></td>
                  <td class="col-num" :class="ecartClass(row.ecart)">{{ formatCurrency(row.ecart) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <p class="dash-footnote">
        Données du snapshot quotidien (mise à jour automatique chaque jour à 06h00).
      </p>
    </div>

    <div
      v-if="!loading && !errorMessage && !hasTerritoires && viewMode === 'dashboard'"
      class="dash-empty-state"
    >
      Aucune donnée disponible pour la période sélectionnée.
    </div>
  </div>
</template>

<script>
import PythonChart from './charts/PythonChart.vue';

export default {
  name: 'CollecteEpargneAVueSection',
  components: { PythonChart },
  data() {
    const now = new Date();
    const currentYear = now.getFullYear();
    return {
      loading: false,
      freezing: false,
      recalculating: false,
      errorMessage: '',
      dataSource: '',
      dataSnapshotAt: '',
      objectifsFiges: false,
      objectifsSource: 'live',
      objectifsSnapshotAt: '',
      objectifsApplied: 0,
      hierarchicalData: { TERRITOIRE: {} },
      selectedMonth: now.getMonth() + 1,
      selectedYear: currentYear,
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
      ],
      years: Array.from({ length: 6 }, (_, i) => currentYear - i),
      expandedSections: {
        TERRITOIRE: true,
        TERRITOIRE_territoire_dakar_ville: false,
        TERRITOIRE_territoire_dakar_banlieue: false,
        TERRITOIRE_territoire_province_centre_sud: false,
        TERRITOIRE_territoire_province_nord: false,
      },
      activeLevel: { type: 'total', category: 'TERRITOIRE' },
      viewMode: 'dashboard',
      dashboardHeight: null,
      chartViewMode: 'graph',
      perfLevel: 'territoire',
      perfTerritoryKey: null,
      perfAgencyName: null,
      selectedChartType: 'bar',
      chartTypes: [
        { value: 'bar', label: 'Barres' },
        { value: 'line', label: 'Ligne' },
        { value: 'pie', label: 'Circulaire' },
      ],
    };
  },
  computed: {
    periodTitle() {
      return `Résultat global — ${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
    },
    loadingHint() {
      if (this.recalculating) {
        return 'Recalcul Flexcube en cours… (peut prendre 1 à 3 min)';
      }
      return 'Chargement du snapshot du matin…';
    },
    hasTerritoires() {
      const t = this.hierarchicalData?.TERRITOIRE || {};
      return Object.keys(t).some((k) => k !== 'grand_compte' && (t[k]?.agencies || []).length);
    },
    territoireEntries() {
      const t = this.hierarchicalData?.TERRITOIRE || {};
      return Object.entries(t).filter(([k]) => k !== 'grand_compte');
    },
    territoireTotal() {
      const totals = {
        cumMontantFinance: 0,
        encoursCredit: 0,
        mtEcheance: 0,
        objectif: 0,
        collecteM: 0,
        totalDepot: 0,
        tro: 0,
      };
      for (const [, territory] of this.territoireEntries) {
        const tt = territory.totals || {};
        totals.cumMontantFinance += Number(tt.cumMontantFinance) || 0;
        totals.encoursCredit += Number(tt.encoursCredit) || 0;
        totals.mtEcheance += Number(tt.mtEcheance) || 0;
        totals.objectif += Number(tt.objectif) || 0;
        totals.collecteM += Number(tt.collecteM) || 0;
        totals.totalDepot += Number(tt.totalDepot) || 0;
      }
      totals.tro = totals.objectif > 0 ? (totals.collecteM / totals.objectif) * 100 : 0;
      return totals;
    },
    grandCompte() {
      const gc = this.hierarchicalData?.TERRITOIRE?.grand_compte;
      return gc?.agencies?.[0] || null;
    },
    grandTotal() {
      const t = { ...this.territoireTotal };
      if (this.grandCompte) {
        t.cumMontantFinance += Number(this.grandCompte.cumMontantFinance) || 0;
        t.encoursCredit += Number(this.grandCompte.encoursCredit) || 0;
        t.mtEcheance += Number(this.grandCompte.mtEcheance) || 0;
        t.objectif += Number(this.grandCompte.objectif) || 0;
        t.collecteM += Number(this.grandCompte.collecteM) || 0;
        t.totalDepot += Number(this.grandCompte.totalDepot) || 0;
        t.tro = t.objectif > 0 ? (t.collecteM / t.objectif) * 100 : 0;
      }
      return t;
    },
    chartTitle() {
      if (this.activeLevel.type === 'agency') return `Évolution — ${this.activeLevel.name}`;
      if (this.activeLevel.type === 'zone') return `Évolution — ${this.activeLevel.zoneName || this.activeLevel.zone}`;
      return 'Évolution — Total';
    },
    activeMetrics() {
      if (this.activeLevel.type === 'agency') {
        const zone = this.hierarchicalData.TERRITOIRE?.[this.activeLevel.zone];
        const agency = (zone?.agencies || []).find((a) => a.name === this.activeLevel.name);
        if (agency) {
          return {
            objectif: Number(agency.objectif) || 0,
            collecteM: Number(agency.collecteM) || 0,
            tro: Number(agency.tro) || 0,
            mtEcheance: Number(agency.mtEcheance) || 0,
            totalDepot: Number(agency.totalDepot) || 0,
            encoursCredit: Number(agency.encoursCredit) || 0,
          };
        }
      }
      if (this.activeLevel.type === 'zone') {
        const zone = this.hierarchicalData.TERRITOIRE?.[this.activeLevel.zone];
        const tt = zone?.totals || {};
        return {
          objectif: Number(tt.objectif) || 0,
          collecteM: Number(tt.collecteM) || 0,
          tro: Number(tt.tro) || 0,
          mtEcheance: Number(tt.mtEcheance) || 0,
          totalDepot: Number(tt.totalDepot) || 0,
          encoursCredit: Number(tt.encoursCredit) || 0,
        };
      }
      return this.grandTotal;
    },
    perfNameHeader() {
      if (this.perfLevel === 'agence') return 'Agence';
      if (this.perfLevel === 'caf') return "Chargé d'affaires";
      return 'Territoire';
    },
    perfParentHeader() {
      if (this.perfLevel === 'caf') return 'Agence';
      return 'Territoire';
    },
    perfFilterLabel() {
      if (this.perfAgencyName) return this.perfAgencyName;
      if (this.perfTerritoryKey) {
        return this.hierarchicalData.TERRITOIRE?.[this.perfTerritoryKey]?.name || this.perfTerritoryKey;
      }
      return '';
    },
    performanceRows() {
      const rows = [];
      for (const [territoryKey, territory] of this.territoireEntries) {
        if (this.perfTerritoryKey && this.perfTerritoryKey !== territoryKey) continue;
        const tName = territory.name || territoryKey;
        const tt = territory.totals || {};

        if (this.perfLevel === 'territoire') {
          const objectif = Number(tt.objectif) || 0;
          const collecteM = Number(tt.collecteM) || 0;
          rows.push({
            id: `t-${territoryKey}`,
            name: tName,
            subtitle: `${(territory.agencies || []).length} agence(s)`,
            parent: '',
            objectif,
            collecteM,
            ecart: collecteM - objectif,
            tro: Number(tt.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
            drillable: true,
            territoryKey,
          });
          continue;
        }

        for (const agency of territory.agencies || []) {
          const aName = agency.name || agency.AGENCE || agency.BRANCH_NAME || '—';
          if (this.perfAgencyName && this.perfAgencyName !== aName) continue;

          if (this.perfLevel === 'agence') {
            const objectif = Number(agency.objectif) || 0;
            const collecteM = Number(agency.collecteM) || 0;
            rows.push({
              id: `a-${territoryKey}-${aName}`,
              name: aName,
              subtitle: this.agencyCodeGestion(agency),
              parent: tName,
              objectif,
              collecteM,
              ecart: collecteM - objectif,
              tro: Number(agency.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
              drillable: (agency.chargeAffaireDetails || []).length > 0,
              territoryKey,
              agencyName: aName,
            });
            continue;
          }

          for (const charge of agency.chargeAffaireDetails || []) {
            const objectif = Number(charge.objectif) || 0;
            const collecteM = Number(charge.collecteM) || 0;
            rows.push({
              id: `c-${territoryKey}-${aName}-${charge.codeGestion || charge.chargeAffaire}`,
              name: charge.chargeAffaire || '—',
              subtitle: charge.codeGestion || '',
              parent: aName,
              objectif,
              collecteM,
              ecart: collecteM - objectif,
              tro: Number(charge.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
              drillable: false,
              territoryKey,
              agencyName: aName,
            });
          }
        }
      }

      return rows.sort((a, b) => b.tro - a.tro);
    },
    resolvedChartType() {
      if (this.selectedChartType === 'bar') return 'groupedbar';
      if (this.selectedChartType === 'line') return 'multiseries';
      return this.selectedChartType;
    },
    comparisonScopeLabel() {
      if (this.activeLevel.type === 'agency') return "Chargé d'affaires";
      if (this.activeLevel.type === 'zone') return 'Agence';
      return 'Territoire';
    },
    comparisonSeries() {
      let items = [];

      if (this.activeLevel.type === 'agency') {
        const zone = this.hierarchicalData.TERRITOIRE?.[this.activeLevel.zone];
        const agency = (zone?.agencies || []).find((a) => a.name === this.activeLevel.name);
        items = (agency?.chargeAffaireDetails || []).map((c) => ({
          label: c.chargeAffaire || c.codeGestion || '—',
          objectif: Number(c.objectif) || 0,
          collecte: Number(c.collecteM) || 0,
        }));
        if (!items.length && agency) {
          items = [{
            label: this.activeLevel.name,
            objectif: Number(agency.objectif) || 0,
            collecte: Number(agency.collecteM) || 0,
          }];
        }
      } else if (this.activeLevel.type === 'zone') {
        const zone = this.hierarchicalData.TERRITOIRE?.[this.activeLevel.zone];
        items = (zone?.agencies || []).map((a) => ({
          label: a.name || a.BRANCH_CODE || '—',
          objectif: Number(a.objectif) || 0,
          collecte: Number(a.collecteM) || 0,
        }));
      } else {
        items = this.territoireEntries.map(([, t]) => ({
          label: t.name,
          objectif: Number(t.totals?.objectif) || 0,
          collecte: Number(t.totals?.collecteM) || 0,
        }));
      }

      return {
        labels: items.map((i) => i.label),
        series: {
          Objectif: items.map((i) => i.objectif),
          Collecte: items.map((i) => i.collecte),
        },
      };
    },
    pieChartData() {
      const { labels, series } = this.comparisonSeries;
      const collectes = series.Collecte || [];
      const items = labels
        .map((label, i) => ({ label, value: Number(collectes[i]) || 0 }))
        .filter((item) => item.value > 0)
        .sort((a, b) => b.value - a.value);

      const total = items.reduce((sum, item) => sum + item.value, 0);
      if (!total) {
        return { labels: [], values: [] };
      }

      const topLimit = 8;
      const minShare = 0.04;
      const top = [];
      let others = 0;
      items.forEach((item, index) => {
        if (index < topLimit && item.value / total >= minShare) {
          top.push(item);
        } else {
          others += item.value;
        }
      });
      if (others > 0) {
        top.push({ label: `Autres (${items.length - top.length} CAF)`, value: others });
      }

      return {
        labels: top.map((item) => item.label),
        values: top.map((item) => item.value),
      };
    },
    currentChartData() {
      const ylabel = 'Montant (FCFA)';

      if (this.selectedChartType === 'pie') {
        const { labels, values } = this.pieChartData;
        return {
          labels,
          values,
          title: `${this.chartTitle} — Répartition de la collecte`,
        };
      }

      const { labels, series } = this.comparisonSeries;
      return {
        labels,
        series,
        title: `${this.chartTitle} — Objectif vs Collecte`,
        xlabel: this.comparisonScopeLabel,
        ylabel,
        colors: ['#2563EB', '#16A34A'],
      };
    },
    dashboardClientCount() {
      let count = 0;
      for (const [, territory] of this.territoireEntries) {
        for (const agency of territory.agencies || []) {
          for (const charge of agency.chargeAffaireDetails || []) {
            count += (charge.clients || []).length;
          }
        }
      }
      if (this.grandCompte) {
        for (const charge of this.grandCompte.chargeAffaireDetails || []) {
          count += (charge.clients || []).length;
        }
      }
      return count;
    },
    dashboardAgencyRows() {
      const rows = [];
      for (const [territoryKey, territory] of this.territoireEntries) {
        for (const agency of territory.agencies || []) {
          const objectif = Number(agency.objectif) || 0;
          const collecteM = Number(agency.collecteM) || 0;
          rows.push({
            id: `${territoryKey}-${agency.name || agency.BRANCH_CODE}`,
            name: agency.name || agency.BRANCH_CODE || '—',
            parent: territory.name,
            objectif,
            collecteM,
            ecart: collecteM - objectif,
            tro: Number(agency.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
          });
        }
      }
      return rows.sort((a, b) => b.tro - a.tro);
    },
    dashboardTopAgencies() {
      return this.dashboardAgencyRows.slice(0, 5);
    },
    dashboardFlopAgencies() {
      return [...this.dashboardAgencyRows].sort((a, b) => a.tro - b.tro).slice(0, 5);
    },
    dashboardCafRows() {
      const rows = [];
      for (const [, territory] of this.territoireEntries) {
        for (const agency of territory.agencies || []) {
          for (const charge of agency.chargeAffaireDetails || []) {
            const objectif = Number(charge.objectif) || 0;
            const collecteM = Number(charge.collecteM) || 0;
            rows.push({
              id: `${agency.name}-${charge.codeGestion || charge.chargeAffaire}`,
              name: charge.chargeAffaire || charge.codeGestion || '—',
              parent: agency.name || agency.BRANCH_CODE || '',
              objectif,
              collecteM,
              ecart: collecteM - objectif,
              tro: Number(charge.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
            });
          }
        }
      }
      return rows.sort((a, b) => b.tro - a.tro);
    },
    dashboardTopCafs() {
      return this.dashboardCafRows.slice(0, 5);
    },
    dashboardFlopCafs() {
      return [...this.dashboardCafRows].sort((a, b) => a.tro - b.tro).slice(0, 5);
    },
    dashboardBestAgency() {
      return this.dashboardTopAgencies[0] || null;
    },
    dashboardBestCaf() {
      return this.dashboardTopCafs[0] || null;
    },
    dashboardBestZone() {
      return this.dashboardZoneRows[0] || null;
    },
    dashboardZoneRows() {
      return this.territoireEntries.map(([key, territory]) => {
        const tt = territory.totals || {};
        const objectif = Number(tt.objectif) || 0;
        const collecteM = Number(tt.collecteM) || 0;
        return {
          id: key,
          name: territory.name,
          objectif,
          collecteM,
          ecart: collecteM - objectif,
          tro: Number(tt.tro) || (objectif > 0 ? (collecteM / objectif) * 100 : 0),
        };
      }).sort((a, b) => b.tro - a.tro);
    },
    dashboardLineChartData() {
      const daysInMonth = new Date(this.selectedYear, this.selectedMonth, 0).getDate();
      const now = new Date();
      const isCurrentMonth =
        this.selectedMonth === now.getMonth() + 1 && this.selectedYear === now.getFullYear();
      const lastDay = isCurrentMonth ? now.getDate() : daysInMonth;
      const labels = Array.from(
        { length: lastDay },
        (_, i) => `${String(i + 1).padStart(2, '0')}/${String(this.selectedMonth).padStart(2, '0')}`
      );
      const objectif = Number(this.grandTotal.objectif) || 0;
      const collecte = Number(this.grandTotal.collecteM) || 0;
      return {
        labels,
        series: {
          Objectif: labels.map(() => objectif),
          Collecte: labels.map((_, i) => (i === labels.length - 1 ? collecte : 0)),
        },
        title: `Évolution ${this.months[this.selectedMonth - 1]} ${this.selectedYear}`,
        xlabel: 'Jour du mois',
        ylabel: 'Montant (FCFA)',
        colors: ['#2563EB', '#16A34A'],
      };
    },
    dashboardPieChartData() {
      const rows = this.dashboardZoneRows.filter((r) => r.collecteM > 0);
      return {
        labels: rows.map((r) => r.name),
        values: rows.map((r) => r.collecteM),
        title: 'Répartition de la collecte',
      };
    },
    dashboardStyle() {
      return this.dashboardHeight ? { height: this.dashboardHeight } : {};
    },
  },
  mounted() {
    this.loadData();
    window.addEventListener('resize', this.updateDashboardHeight);
    this.updateDashboardHeight();
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updateDashboardHeight);
  },
  watch: {
    viewMode() {
      this.$nextTick(this.updateDashboardHeight);
    },
    loading() {
      this.$nextTick(this.updateDashboardHeight);
    },
  },
  methods: {
    // La hauteur disponible dépend de l'entête d'application, qui n'est pas connue en CSS seul.
    updateDashboardHeight() {
      const el = this.$refs.dashboardRoot;
      if (!el || window.innerWidth <= 1100) {
        this.dashboardHeight = null;
        return;
      }
      const available = window.innerHeight - el.getBoundingClientRect().top - 16;
      this.dashboardHeight = available > 520 ? `${Math.round(available)}px` : null;
    },
    agencyDisplayName(agency) {
      return agency.name || agency.AGENCE || agency.BRANCH_NAME || agency.BRANCH_CODE || '—';
    },
    agencyKey(agency, index) {
      return `${agency.BRANCH_CODE || agency.branch_code || agency.name || 'a'}-${index}`;
    },
    agencyExpandKey(territoryKey, agency, index) {
      return `TERRITOIRE_${territoryKey}_${this.agencyKey(agency, index)}`;
    },
    cafExpandKey(territoryKey, agency, index, cIdx) {
      return `${this.agencyExpandKey(territoryKey, agency, index)}_CAF_${cIdx}`;
    },
    agencyCodeGestion(agency) {
      const details = agency.chargeAffaireDetails || [];
      if (details.length === 1) return details[0].codeGestion || '—';
      if (details.length > 1) return `${details.length} CAF`;
      return '—';
    },
    agencyCharge(agency) {
      const details = agency.chargeAffaireDetails || [];
      if (details.length === 1) return details[0].chargeAffaire || '—';
      if (details.length > 1) return 'Plusieurs CAF';
      return '—';
    },
    toggleExpand(key) {
      this.expandedSections = {
        ...this.expandedSections,
        [key]: !this.expandedSections[key],
      };
    },
    setActiveLevel(type, zone, zoneName) {
      this.activeLevel = { type, category: 'TERRITOIRE', zone, zoneName };
    },
    selectAgency(agency, territoryKey) {
      this.activeLevel = {
        type: 'agency',
        category: 'TERRITOIRE',
        zone: territoryKey,
        zoneName: this.hierarchicalData.TERRITOIRE?.[territoryKey]?.name,
        name: agency.name || agency.AGENCE || agency.BRANCH_NAME,
      };
    },
    isSelectedAgency(agency, territoryKey) {
      return (
        this.activeLevel.type === 'agency' &&
        this.activeLevel.zone === territoryKey &&
        this.activeLevel.name === (agency.name || agency.AGENCE || agency.BRANCH_NAME)
      );
    },
    resetToTotal() {
      this.activeLevel = { type: 'total', category: 'TERRITOIRE' };
    },
    setPerfLevel(level) {
      this.perfLevel = level;
      if (level === 'territoire') {
        this.perfTerritoryKey = null;
        this.perfAgencyName = null;
      } else if (level === 'agence') {
        this.perfAgencyName = null;
      }
    },
    clearPerfFilter() {
      this.perfTerritoryKey = null;
      this.perfAgencyName = null;
      if (this.perfLevel === 'caf') this.perfLevel = 'agence';
      else if (this.perfLevel === 'agence') this.perfLevel = 'territoire';
    },
    drillPerfRow(row) {
      if (this.perfLevel === 'territoire') {
        this.perfTerritoryKey = row.territoryKey;
        this.perfLevel = 'agence';
        this.setActiveLevel('zone', row.territoryKey, row.name);
      } else if (this.perfLevel === 'agence') {
        this.perfTerritoryKey = row.territoryKey;
        this.perfAgencyName = row.agencyName;
        this.perfLevel = 'caf';
        this.selectAgency(
          { name: row.agencyName },
          row.territoryKey
        );
      }
    },
    troBarWidth(v) {
      const n = Number(v) || 0;
      return `${Math.max(0, Math.min(100, n))}%`;
    },
    rankBadgeClass(idx) {
      if (idx === 0) return 'rank-gold';
      if (idx === 1) return 'rank-silver';
      if (idx === 2) return 'rank-bronze';
      return '';
    },
    formatCurrency(v) {
      const n = Number(v);
      if (!Number.isFinite(n)) return '—';
      return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n);
    },
    formatTro(v) {
      const n = Number(v);
      if (!Number.isFinite(n)) return '—';
      return `${n.toFixed(1).replace('.', ',')} %`;
    },
    troClass(v) {
      const n = Number(v) || 0;
      if (n >= 80) return 'tro-good';
      if (n >= 40) return 'tro-mid';
      return 'tro-low';
    },
    troBadge(v) {
      return ['tro-badge', this.troClass(v)];
    },
    ecartClass(v) {
      const n = Number(v) || 0;
      if (n > 0) return 'tro-good';
      if (n < 0) return 'tro-low';
      return '';
    },
    async loadData(forceRefresh = false) {
      this.loading = true;
      this.errorMessage = '';
      try {
        const params = {
          month: this.selectedMonth,
          year: this.selectedYear,
        };
        if (forceRefresh) {
          params.refresh = 1;
        }
        const response = await window.axios.get('/api/oracle/data/collecte-epargne-a-vue', {
          params,
          timeout: forceRefresh ? 300000 : 60000,
        });
        const payload = response.data || {};
        this.hierarchicalData = payload.hierarchicalData || { TERRITOIRE: {} };
        this.dataSource = payload.data_source || '';
        this.dataSnapshotAt =
          (payload.data_snapshot && payload.data_snapshot.refreshed_at) || '';
        this.objectifsFiges = !!payload.objectifs_figes;
        this.objectifsSource = payload.objectifs_source || 'live';
        this.objectifsApplied = payload.objectifs_applied || 0;
        this.objectifsSnapshotAt =
          (payload.objectifs_snapshot && payload.objectifs_snapshot.refreshed_at) || '';
        this.resetToTotal();
      } catch (err) {
        let msg =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          "Impossible de charger la collecte d'épargne à vue";
        if (err?.code === 'ECONNABORTED' || String(msg).toLowerCase().includes('timeout')) {
          msg = forceRefresh
            ? 'Le recalcul Flexcube a pris trop de temps. Réessayez plus tard.'
            : 'Le chargement du snapshot a pris trop de temps. Réessayez.';
        }
        this.errorMessage = msg;
        this.hierarchicalData = { TERRITOIRE: {} };
        this.dataSource = '';
        this.dataSnapshotAt = '';
        this.objectifsFiges = false;
      } finally {
        this.loading = false;
      }
    },
    async forceRecalc() {
      if (!window.confirm(
        `Recalculer depuis Flexcube pour ${this.months[this.selectedMonth - 1]} ${this.selectedYear} ?\n` +
        'Cette opération est longue (1–3 min) et met à jour le snapshot du jour.'
      )) {
        return;
      }
      this.recalculating = true;
      try {
        await this.loadData(true);
      } finally {
        this.recalculating = false;
      }
    },
    async freezeObjectifs() {
      if (!window.confirm(
        `Figer les objectifs OBJ_COL_EPV_VUE pour ${this.months[this.selectedMonth - 1]} ${this.selectedYear} ?\n` +
        'Cette action remplace le snapshot du mois.'
      )) {
        return;
      }
      this.freezing = true;
      this.errorMessage = '';
      try {
        await window.axios.post('/api/oracle/backup/objectif-epv-vue', null, {
          params: { month: this.selectedMonth, year: this.selectedYear },
          timeout: 300000,
        });
        await this.loadData();
      } catch (err) {
        this.errorMessage =
          err?.response?.data?.message ||
          err?.response?.data?.error ||
          err?.message ||
          'Échec du figement des objectifs';
      } finally {
        this.freezing = false;
      }
    },
    async exportChart(format) {
      const chart = this.$refs.chartComponent;
      if (chart && typeof chart.exportChart === 'function') {
        chart.exportChart(format);
      }
    },
    exportCsv() {
      const rows = [[
        'CODE_AGENCE',
        'BRANCH_NAME',
        'CODE_CAF',
        'CHARGE_AFFAIRE',
        'MATRICULE_CLIENT',
        'NUMERO_COMPTE',
        'NOM_CLIENT',
        'CUM_MONTANT_FINANCE',
        'CUM_ENCOURS_CREDIT',
        'OBJ_COL_EPV_VUE',
        'MONTANT_ECHEANCE',
        'TOTAL_DEPOT',
        'COL_EP_VUE',
      ]];
      for (const [, territory] of this.territoireEntries) {
        for (const agency of territory.agencies || []) {
          for (const charge of agency.chargeAffaireDetails || []) {
            for (const client of charge.clients || []) {
              rows.push([
                client.CODE_AGENCE || agency.BRANCH_CODE,
                client.BRANCH_NAME || agency.name,
                client.CODE_CAF,
                client.CHARGE_AFFAIRE,
                client.MATRICULE_CLIENT,
                client.NUMERO_COMPTE,
                client.NOM_CLIENT,
                client.CUM_MONTANT_FINANCE,
                client.CUM_ENCOURS_CREDIT,
                client.OBJ_COL_EPV_VUE,
                client.MONTANT_ECHEANCE,
                client.TOTAL_DEPOT,
                client.COL_EP_VUE,
              ]);
            }
          }
        }
      }
      const csv = rows.map((r) => r.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(';')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `collecte-epargne-a-vue-${this.selectedMonth}-${this.selectedYear}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    },
  },
};
</script>

<style scoped>
.collecte-epargne-a-vue-section {
  --epv-ink: #1f2937;
  --epv-muted: #6b7280;
  --epv-border: #e5e7eb;
  --epv-red: #b91c1c;
  --epv-green: #0f766e;
  --epv-green-soft: #ecfdf5;
  padding: 1.25rem 1.5rem 2.5rem;
  color: var(--epv-ink);
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--epv-border);
}

.title-block {
  min-width: 240px;
}

.section-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--epv-ink);
}

.epv-view-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 1.25rem;
  padding: 8px;
  background: #f9fafb;
  border-radius: 8px;
  border-bottom: 2px solid #e5e7eb;
}

.epv-view-tab {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.epv-view-tab:hover:not(:disabled) {
  color: #1A4D3A;
  background-color: #f0fdf4;
  border-color: #1A4D3A;
}

.epv-view-tab.active {
  color: #ffffff;
  font-weight: 600;
  background-color: #1A4D3A;
  border-color: #1A4D3A;
  box-shadow: 0 2px 8px rgba(26, 77, 58, 0.3);
}

.epv-view-tab.active:hover {
  background-color: #153d2a;
}

.epv-view-tab:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.section-subtitle {
  margin: 0.35rem 0 0;
  font-size: 0.92rem;
  color: var(--epv-muted);
}

.period-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: flex-end;
}

.period-label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--epv-muted);
}

.month-select,
.year-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fff;
  color: var(--epv-ink);
  min-height: 38px;
}

.btn-refresh {
  min-height: 38px;
  padding: 0.5rem 1rem;
  border: 1px solid var(--epv-green);
  border-radius: 6px;
  background: var(--epv-green);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-recalc {
  min-height: 38px;
  padding: 0.5rem 1rem;
  border: 1px solid #1d4ed8;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-refresh:disabled,
.btn-recalc:disabled,
.btn-freeze:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-freeze {
  min-height: 38px;
  padding: 0.5rem 1rem;
  border: 1px solid #92400e;
  border-radius: 6px;
  background: #fffbeb;
  color: #92400e;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.loading-message,
.error-message {
  border-radius: 8px;
  padding: 0.9rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.92rem;
  font-weight: 500;
}

.loading-message {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.kpi-card {
  background: #fff;
  border: 1px solid var(--epv-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}

.kpi-card--accent {
  background: var(--epv-green-soft);
  border-color: #99f6e4;
}

.kpi-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--epv-muted);
  margin-bottom: 0.35rem;
}

.kpi-value {
  font-size: 1.05rem;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.panel {
  background: #fff;
  border: 1px solid var(--epv-border);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
}

.panel-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.85rem 1.1rem;
  border-bottom: 1px solid var(--epv-border);
  background: #fafafa;
}

.panel-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--epv-green);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.panel-meta {
  font-size: 0.78rem;
  color: var(--epv-muted);
}

.table-container {
  overflow: auto;
  max-height: calc(100vh - 320px);
}

.agencies-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 1280px;
  font-size: 0.8125rem;
}

.agencies-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--epv-red);
  color: #fff;
  padding: 0.7rem 0.55rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
  border-right: 1px solid rgba(255, 255, 255, 0.15);
  text-align: center;
}

.agencies-table thead th.col-tree,
.agencies-table thead th.col-left {
  text-align: left;
  padding-left: 0.9rem;
}

.agencies-table thead th.col-num {
  text-align: right;
}

.agencies-table td {
  padding: 0.55rem 0.55rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
  white-space: nowrap;
  text-align: center;
}

.agencies-table td.col-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum';
}

.agencies-table td.col-left,
.agencies-table td.level-1,
.agencies-table td.level-2,
.agencies-table td.level-3,
.agencies-table td.level-4,
.agencies-table td.level-5 {
  text-align: left;
}

.muted {
  color: #9ca3af;
}

.level-1-row {
  background: #111827;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.level-1-row td {
  border-bottom-color: #1f2937;
}

.level-2-row {
  background: #374151;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.level-2-row td {
  border-bottom-color: #4b5563;
}

.level-3-row {
  background: #fff;
  cursor: pointer;
}

.level-3-row:hover,
.level-4-row:hover,
.level-5-row:hover {
  background: #f0fdf4;
}

.level-3-row.selected {
  background: #ecfdf5;
  box-shadow: inset 3px 0 0 var(--epv-green);
}

.level-4-row {
  background: #f8fafc;
  cursor: pointer;
}

.level-5-row {
  background: #fff;
}

.level-5-row td {
  font-size: 0.78rem;
  color: #374151;
}

.level-1,
.level-2,
.level-3,
.level-4,
.level-5 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-left: 0.9rem !important;
}

.level-2 { padding-left: 1.6rem !important; }
.level-3 { padding-left: 2.4rem !important; }
.level-4 { padding-left: 3.2rem !important; }
.level-5 { padding-left: 4rem !important; }

.agency-name {
  font-weight: 600;
}

.client-name {
  font-weight: 500;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-btn {
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  border: none;
  border-radius: 4px;
  background: #10b981;
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
  line-height: 1;
  cursor: pointer;
}

.expand-btn--sm {
  width: 18px;
  height: 18px;
  flex-basis: 18px;
  font-size: 0.75rem;
}

.branch-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: #e5e7eb;
  color: #374151;
  font-size: 0.72rem;
  font-weight: 700;
}

.code-caf,
.compte {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.75rem;
  background: #f3f4f6;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  color: #1f2937;
}

.level-1-row .expand-btn,
.level-2-row .expand-btn {
  background: #34d399;
  color: #064e3b;
}

.grand-compte-row {
  background: #fffbeb;
  font-weight: 600;
}

.total-row {
  background: #f3f4f6;
  font-weight: 700;
}

.total-row td {
  border-top: 2px solid #9ca3af;
  border-bottom: 2px solid #9ca3af;
}

.no-data-row td {
  text-align: center !important;
  padding: 2.5rem 1rem !important;
  color: var(--epv-muted);
}

.tro-badge {
  display: inline-block;
  min-width: 4.2rem;
  padding: 0.15rem 0.4rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.tro-good {
  color: #047857;
}

.tro-mid {
  color: #b45309;
}

.tro-low {
  color: #b91c1c;
}

.tro-badge.tro-good {
  background: #d1fae5;
  color: #047857;
}

.tro-badge.tro-mid {
  background: #fef3c7;
  color: #b45309;
}

.tro-badge.tro-low {
  background: #fee2e2;
  color: #b91c1c;
}

.chart-evolution-section {
  margin-top: 1.5rem;
  background: #fff;
  border: 1px solid var(--epv-border);
  border-radius: 10px;
  padding: 1rem 1.15rem 1.35rem;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.85rem;
}

.chart-section-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
}

.breadcrumb {
  margin-top: 0.3rem;
  font-size: 0.8rem;
  color: var(--epv-muted);
}

.breadcrumb-item {
  cursor: pointer;
  color: var(--epv-green);
}

.breadcrumb-item.active {
  color: var(--epv-ink);
  cursor: default;
  font-weight: 600;
}

.breadcrumb-separator {
  margin: 0 0.3rem;
  color: #9ca3af;
}

.chart-actions {
  display: flex;
  gap: 0.45rem;
}

.export-btn {
  background: var(--epv-green);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}

.chart-view-tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--epv-border);
  margin-bottom: 0.85rem;
}

.chart-view-tab {
  background: transparent;
  border: none;
  padding: 0.55rem 0.9rem;
  cursor: pointer;
  color: var(--epv-muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  font-weight: 600;
  font-size: 0.875rem;
}

.chart-view-tab.active {
  color: var(--epv-red);
  border-bottom-color: var(--epv-red);
}

.chart-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
}

.chart-tabs {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.chart-tab {
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 6px;
  padding: 0.35rem 0.7rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
}

.chart-tab.active {
  background: var(--epv-green-soft);
  border-color: #5eead4;
  color: #0f766e;
}

.chart-wrapper-container {
  min-height: 420px;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
  padding: 0.5rem;
}

.performance-panel {
  padding: 0.35rem 0 0.75rem;
}

.perf-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.perf-card {
  background: #f9fafb;
  border: 1px solid var(--epv-border);
  border-radius: 8px;
  padding: 0.85rem 1rem;
}

.perf-card.highlight {
  background: var(--epv-green-soft);
  border-color: #99f6e4;
}

.perf-card .label {
  display: block;
  font-size: 0.72rem;
  color: var(--epv-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 600;
  margin-bottom: 0.3rem;
}

.perf-card strong {
  font-size: 1.05rem;
  font-variant-numeric: tabular-nums;
}

.perf-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.perf-level-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.perf-level-tab {
  padding: 0.45rem 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
}

.perf-level-tab.active {
  background: #1A4D3A;
  border-color: #1A4D3A;
  color: #fff;
}

.perf-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--epv-muted);
}

.perf-crumb {
  border: none;
  background: transparent;
  color: #1A4D3A;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.perf-crumb-sep {
  color: #cbd5e1;
}

.perf-crumb-current {
  color: var(--epv-ink);
  font-weight: 600;
}

.perf-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--epv-border);
  border-radius: 10px;
  background: #fff;
}

.perf-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.perf-table thead th {
  text-align: left;
  padding: 0.7rem 0.85rem;
  background: #f8fafc;
  border-bottom: 1px solid var(--epv-border);
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.perf-table tbody td {
  padding: 0.7rem 0.85rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.perf-table tbody tr:last-child td {
  border-bottom: none;
}

.perf-table tbody tr.clickable {
  cursor: pointer;
}

.perf-table tbody tr.clickable:hover {
  background: #f0fdf4;
}

.perf-table .col-rank {
  width: 52px;
}

.perf-table .col-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.perf-table .col-tro {
  min-width: 160px;
}

.perf-table .col-parent {
  color: var(--epv-muted);
  white-space: nowrap;
}

.perf-name {
  display: block;
  font-weight: 600;
  color: var(--epv-ink);
}

.perf-sub {
  display: block;
  font-size: 0.75rem;
  color: var(--epv-muted);
  margin-top: 0.1rem;
}

.perf-empty {
  text-align: center;
  color: var(--epv-muted);
  padding: 1.5rem !important;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 999px;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.75rem;
  font-weight: 700;
}

.rank-badge.rank-gold {
  background: #fef3c7;
  color: #b45309;
}

.rank-badge.rank-silver {
  background: #e2e8f0;
  color: #334155;
}

.rank-badge.rank-bronze {
  background: #ffedd5;
  color: #c2410c;
}

.tro-cell {
  display: flex;
  align-items: center;
  gap: 0.55rem;
}

.tro-bar-track {
  flex: 1;
  height: 7px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
  min-width: 64px;
}

.tro-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #94a3b8;
}

.tro-bar-fill.tro-good {
  background: #0f766e;
}

.tro-bar-fill.tro-mid {
  background: #d97706;
}

.tro-bar-fill.tro-low {
  background: #b91c1c;
}

.tro-value {
  min-width: 3.4rem;
  text-align: right;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  font-size: 0.8125rem;
}

@media (max-width: 1100px) {
  .kpi-strip,
  .perf-cards {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }

  .dash-charts-row,
  .dash-tables-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-strip,
  .perf-cards,
  .dash-kpi-grid {
    grid-template-columns: 1fr;
  }
}

.epv-dashboard {
  display: grid;
  grid-template-rows: auto minmax(0, 1.05fr) minmax(0, 1fr) auto;
  gap: 0.6rem;
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 560px;
  overflow: hidden;
}

.epv-dashboard :deep(.python-chart-container) {
  flex: 1 1 auto;
  min-height: 0;
  height: auto;
}

.epv-dashboard :deep(.chart-wrapper),
.epv-dashboard :deep(.chart-loading),
.epv-dashboard :deep(.chart-error) {
  min-height: 0;
  height: 100%;
}

.dash-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(130px, 1fr));
  gap: 0.7rem;
}

.dash-kpi {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcfe 100%);
  border: 1px solid #e8edf3;
  border-radius: 16px;
  padding: 0.75rem 0.85rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12);
  transition: box-shadow 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
}

.dash-kpi:hover {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
  border-color: #d7e0ea;
}

.dash-kpi-icon {
  flex: 0 0 auto;
  width: 2.45rem;
  height: 2.45rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.dash-kpi-icon svg {
  width: 1.15rem;
  height: 1.15rem;
}

.dash-kpi-body {
  min-width: 0;
}

.dash-kpi.objectif .dash-kpi-icon { background: #eff6ff; color: #2563eb; }
.dash-kpi.collecte .dash-kpi-icon { background: #ecfdf5; color: #059669; }
.dash-kpi.taux .dash-kpi-icon { background: #f0fdfa; color: #0f766e; }
.dash-kpi.ecart .dash-kpi-icon { background: #fef2f2; color: #dc2626; }
.dash-kpi.comptes .dash-kpi-icon { background: #f5f3ff; color: #7c3aed; }

.dash-kpi.objectif { box-shadow: inset 3px 0 0 #2563eb, 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12); }
.dash-kpi.collecte { box-shadow: inset 3px 0 0 #16a34a, 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12); }
.dash-kpi.taux { box-shadow: inset 3px 0 0 #0f766e, 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12); }
.dash-kpi.ecart { box-shadow: inset 3px 0 0 #dc2626, 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12); }
.dash-kpi.comptes { box-shadow: inset 3px 0 0 #7c3aed, 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 20px -12px rgba(15, 23, 42, 0.12); }

.dash-kpi-label {
  display: block;
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  font-weight: 700;
  margin-bottom: 0.18rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-kpi-value {
  font-size: 1.02rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.dash-kpi-value small {
  font-size: 0.68rem;
  color: #94a3b8;
  font-weight: 600;
  margin-left: 0.15rem;
}

.dash-charts-row {
  display: grid;
  grid-template-columns: 1.25fr 0.9fr 0.75fr;
  gap: 0.7rem;
  align-items: stretch;
  min-height: 0;
}

.dash-tables-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.7rem;
  min-height: 0;
}

.dash-card {
  background: #fff;
  border: 1px solid #e8edf3;
  border-radius: 16px;
  padding: 0.75rem 0.9rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 10px 24px -14px rgba(15, 23, 42, 0.15);
}

.dash-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.55rem;
  margin-bottom: 0.55rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
  flex: 0 0 auto;
}

.dash-card-head h4 {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
  position: relative;
  padding-left: 0.65rem;
  letter-spacing: -0.01em;
}

.dash-card-head h4::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0.95rem;
  border-radius: 2px;
  background: linear-gradient(180deg, #1A4D3A 0%, #0f766e 100%);
}

.dash-mini-stats {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.dash-chip {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.28rem 0.55rem;
  border-radius: 10px;
  border: 1px solid transparent;
  min-width: 5.5rem;
}

.dash-chip span {
  display: block;
  font-size: 0.62rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
}

.dash-chip strong {
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: #0f172a;
}

.dash-chip.collecte {
  background: #ecfdf5;
  border-color: #d1fae5;
}

.dash-chip.collecte strong { color: #059669; }

.dash-chip.objectif {
  background: #eff6ff;
  border-color: #dbeafe;
}

.dash-chip.objectif strong { color: #2563eb; }

.dash-chip.taux {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.c-objectif { color: #2563EB; }
.c-collecte { color: #16A34A; }

.dash-table-wrap {
  overflow: auto;
  flex: 1 1 auto;
  min-height: 0;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
}

.dash-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}

.dash-table th,
.dash-table td {
  padding: 0.48rem 0.55rem;
  border-bottom: 1px solid #f1f5f9;
  text-align: left;
}

.dash-table th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  z-index: 1;
}

.dash-table tbody tr:nth-child(even) td {
  background: #fcfdfe;
}

.dash-table tbody tr:hover td {
  background: #f1f5f9;
}

.dash-table tbody tr:last-child td {
  border-bottom: none;
}

.dash-table .col-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.dash-table td strong {
  font-weight: 700;
  color: #1e293b;
}

.dash-sub {
  display: block;
  color: var(--epv-muted);
  font-size: 0.72rem;
  font-weight: 500;
}

.dash-empty {
  text-align: center;
  color: var(--epv-muted);
  padding: 1rem !important;
}

.dash-rank-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

.dash-rank-title {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.4rem;
  padding: 0.2rem 0.35rem;
  border-radius: 6px;
}

.dash-rank-title.top {
  color: #15803d;
  background: #f0fdf4;
}

.dash-rank-title.flop {
  color: #b91c1c;
  background: #fef2f2;
}

.dash-rank-dot {
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 999px;
}

.dash-rank-dot.top { background: #16a34a; }
.dash-rank-dot.flop { background: #dc2626; }

.dash-rank-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.dash-rank-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.38rem 0.45rem;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid transparent;
  transition: background 0.12s ease, border-color 0.12s ease;
}

.dash-rank-list li:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.dash-rank-list .rank {
  width: 1.35rem;
  height: 1.35rem;
  flex: 0 0 auto;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.68rem;
  font-weight: 700;
}

.dash-rank-list .rank.rank-top {
  background: #dcfce7;
  color: #15803d;
}

.dash-rank-list .rank.rank-flop {
  background: #fee2e2;
  color: #b91c1c;
}

.dash-rank-list .meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1 1 auto;
}

.dash-rank-list .tro-badge {
  flex: 0 0 auto;
  min-width: 3.4rem;
  text-align: center;
}

.dash-rank-list .meta strong {
  font-size: 0.74rem;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-rank-list .meta span {
  font-size: 0.66rem;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-rank-list .empty {
  color: var(--epv-muted);
  font-size: 0.8125rem;
  background: transparent;
  border: none;
}

.dash-footnote {
  margin: 0;
  font-size: 0.72rem;
  color: #94a3b8;
}

.dash-empty-state {
  background: #fff;
  border: 1px solid #e8edf3;
  border-radius: 16px;
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--epv-muted);
  font-size: 0.875rem;
}

.dash-resume-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  gap: 0.5rem;
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
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

.dash-resume-list li.resume-caf {
  background: linear-gradient(90deg, #eff6ff 0%, #f8fafc 55%);
  border-color: #dbeafe;
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
  font-size: 0.64rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 700;
  margin-bottom: 0.12rem;
}

.dash-resume-value {
  display: block;
  font-size: 0.8rem;
  color: #0f172a;
  font-weight: 700;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dash-resume-list .tro-badge {
  flex: 0 0 auto;
}

/* En dessous de 1100px les cartes s'empilent : le dashboard ne peut plus tenir sur un écran. */
@media (max-width: 1100px) {
  .epv-dashboard {
    grid-template-rows: none;
    height: auto;
    min-height: 0;
    overflow: visible;
  }

  .epv-dashboard :deep(.python-chart-container),
  .epv-dashboard :deep(.chart-wrapper),
  .epv-dashboard :deep(.chart-loading),
  .epv-dashboard :deep(.chart-error) {
    min-height: 260px;
  }
}
</style>
