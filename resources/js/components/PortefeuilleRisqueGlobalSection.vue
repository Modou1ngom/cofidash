<template>
  <div class="par-global-section">
    <div class="section-header">
      <h2 class="section-title">Evolution du Portefeuille à risque % - {{ getPeriodTitle() }}</h2>
      <div class="period-selector">
        <div class="period-group">
          <label class="period-label">Mois de référence</label>
          <select v-model="selectedMonthRef" class="month-select" @change="handlePeriodChange">
            <option v-for="(month, index) in months" :key="'ref-m-' + index" :value="index + 1">
              {{ month }}
            </option>
          </select>
          <select v-model="selectedYearRef" class="year-select" @change="handlePeriodChange">
            <option v-for="year in years" :key="'ref-y-' + year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>
        <div class="period-group">
          <label class="period-label">Mois en cours</label>
          <select v-model="selectedMonth" class="month-select" @change="handleMonthChange">
            <option v-for="(month, index) in months" :key="index" :value="index + 1">
              {{ month }}
            </option>
          </select>
          <select v-model="selectedYear" class="year-select" @change="handleYearChange">
            <option v-for="year in years" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Barre de navigation -->
    <div class="navigation-tabs">
      <button 
        class="nav-tab entrees-par-tab entrees-par0-tab"
        :class="{ active: activeTab === 'entrees-par0' }"
        @click="activeTab = 'entrees-par0'"
      >
        Entrées PAR0
      </button>
      <button 
        class="nav-tab entrees-par-tab entrees-par30-tab"
        :class="{ active: activeTab === 'entrees-par30' }"
        @click="activeTab = 'entrees-par30'"
      >
        Entrées PAR30
      </button>
      <button 
        class="nav-tab entrees-par-tab entrees-par90-tab"
        :class="{ active: activeTab === 'entrees-par90' }"
        @click="activeTab = 'entrees-par90'"
      >
        Entrées PAR90
      </button>
      <button 
        class="nav-tab entrees-par-tab entrees-par180-tab"
        :class="{ active: activeTab === 'entrees-par180' }"
        @click="activeTab = 'entrees-par180'"
      >
        Entrées PAR180
      </button>
      <button 
        class="nav-tab entrees-par-tab entrees-par360-tab"
        :class="{ active: activeTab === 'entrees-par360' }"
        @click="activeTab = 'entrees-par360'"
      >
        Entrées PAR360
      </button>
      <button 
        class="nav-tab par-agence-tab"
        :class="{ active: activeTab === 'par-agence' }"
        @click="activeTab = 'par-agence'"
      >
        PAR AGENCE
      </button>
      <button 
        class="nav-tab par-caf-tab"
        :class="{ active: activeTab === 'par-caf' }"
        @click="activeTab = 'par-caf'"
      >
        PAR | CAF
      </button>
      <button 
        class="nav-tab flop-30-tab"
        :class="{ active: activeTab === 'flop-30' }"
        @click="activeTab = 'flop-30'"
      >
        FLOP 30
      </button>
      <button 
        class="nav-tab top-50-tab"
        :class="{ active: activeTab === 'top-50' }"
        @click="activeTab = 'top-50'"
      >
        TOP 50
      </button>
    </div>
    
    <!-- Résultat Global -->
    <div class="global-result-section">
      <div v-if="loading" class="loading-message">
        <p>🔄 Chargement des données ...</p>
        <p style="font-size: 12px; color: #666; margin-top: 5px;">
          ⏱️ Cette opération peut prendre jusqu'à 5 minutes en raison de la complexité des calculs.
        </p>
      </div>
      <div v-if="errorMessage" class="error-message">
        <p>⚠️ {{ errorMessage }}</p>
      </div>
    </div>

    <!-- Tableau PAR | CAF -->
    <div v-if="activeTab === 'par-caf'" class="par-caf-container">
      <div class="par-caf-content">
        <!-- Tableau principal -->
        <div class="par-caf-table-container">
          <div class="caf-header">
            <div class="caf-selector">
              <span>CAF</span>
              <span class="dropdown-icon">▼</span>
            </div>
          </div>
          <div class="table-wrapper">
            <table class="par-caf-table">
              <thead>
                <tr>
                  <th v-if="showAgencyColumn" class="agency-col">AGENCE</th>
                  <th class="name-col">CAF</th>
                  <th class="number-col">NBRE DE DOSSIERS</th>
                  <th class="amount-col">Encours de crédit</th>
                  <th class="amount-col par-0-header">Encours PAR 0</th>
                  <th class="par-col par-0-header">PAR 0</th>
                  <th class="amount-col par-30-header">Encours PAR 30</th>
                  <th class="par-col par-30-header">PAR 30</th>
                  <th class="amount-col par-90-header">Encours PAR 90</th>
                  <th class="par-col par-90-header">PAR 90</th>
                  <th class="amount-col par-180-header">Encours PAR 180</th>
                  <th class="par-col par-180-header">PAR 180</th>
                  <th class="amount-col par-360-header">Encours PAR 360</th>
                  <th class="par-col par-360-header">PAR 360</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="cafLoading">
                  <tr>
                    <td :colspan="showAgencyColumn ? 14 : 13" style="text-align: center; padding: 20px;">
                      🔄 Chargement des données CAF...
                    </td>
                  </tr>
                  <tr v-for="i in 49" :key="'par-caf-empty-' + i" class="caf-row caf-row-empty" :class="{ 'caf-row-alt': i % 2 === 0 }">
                    <td v-if="showAgencyColumn" class="agency-cell">–</td>
                    <td class="name-cell">–</td>
                    <td class="number-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="amount-cell">–</td>
                    <td class="par-cell">–</td>
                    <td class="par-cell">–</td>
                    <td class="par-cell">–</td>
                    <td class="par-cell">–</td>
                    <td class="par-cell">–</td>
                  </tr>
                </template>
                <template v-else>
                  <tr v-for="(item, index) in parCafRows" :key="item.empty ? 'par-caf-row-' + index : getCafRowKey(item, index)" class="caf-row" :class="{ 'caf-row-alt': index % 2 === 1, 'caf-row-empty': item.empty }">
                    <td v-if="showAgencyColumn" class="agency-cell">{{ item.empty ? '–' : (item.agence || '–') }}</td>
                    <td class="name-cell">{{ item.empty ? '–' : item.nom }}</td>
                    <td class="number-cell">{{ item.empty ? '–' : formatNumber(item.nbreDossiers) }}</td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursCredit) }}</td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursPar0) }}</td>
                    <td class="par-cell">
                      <template v-if="item.empty">–</template>
                      <template v-else>
                        <span class="par-value">{{ formatPercent(getCafPar(item, 'par0')) }}</span>
                        <span :class="getParIndicatorClass(getCafPar(item, 'par0'))"></span>
                      </template>
                    </td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursPar30) }}</td>
                    <td class="par-cell">
                      <template v-if="item.empty">–</template>
                      <template v-else>
                        <span class="par-value">{{ formatPercent(getCafPar(item, 'par30')) }}</span>
                        <span :class="getParIndicatorClass(getCafPar(item, 'par30'))"></span>
                      </template>
                    </td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursPar90) }}</td>
                    <td class="par-cell">
                      <template v-if="item.empty">–</template>
                      <template v-else>
                        <span class="par-value">{{ formatPercent(getCafPar(item, 'par90')) }}</span>
                        <span :class="getParIndicatorClass(getCafPar(item, 'par90'))"></span>
                      </template>
                    </td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursPar180) }}</td>
                    <td class="par-cell">
                      <template v-if="item.empty">–</template>
                      <template v-else>
                        <span class="par-value">{{ formatPercent(getCafPar(item, 'par180')) }}</span>
                        <span :class="getParIndicatorClass(getCafPar(item, 'par180'))"></span>
                      </template>
                    </td>
                    <td class="amount-cell">{{ item.empty ? '–' : formatCurrency(item.encoursPar360) }}</td>
                    <td class="par-cell">
                      <template v-if="item.empty">–</template>
                      <template v-else>
                        <span class="par-value">{{ formatPercent(getCafPar(item, 'par360')) }}</span>
                        <span :class="getParIndicatorClass(getCafPar(item, 'par360'))"></span>
                      </template>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Panneau filtre par agence (optionnel) -->
        <div class="agency-panel">
          <div class="agency-panel-banner">
            <h3 class="agency-panel-title">Filtrer par agence (optionnel)</h3>
          </div>
          <div class="agency-panel-content">
            <div class="agency-header">
              <span class="agency-header-label">AGENCE</span>
              <div class="agency-header-icons">
                <span class="agency-icon checklist-icon">☑</span>
                <span class="agency-icon filter-icon">🔽</span>
              </div>
            </div>
            <div class="agency-list">
              <button
                v-for="agency in filteredAgencies"
                :key="agency"
                class="agency-button"
                :class="{ active: selectedAgency === agency }"
                @click="selectAgency(agency)"
              >
                {{ agency }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Page FLOP 30 : tableau détaillé des 30 CAF les plus à risque -->
    <div v-if="activeTab === 'flop-30'" class="flop-30-container">
      <div class="flop-30-header">
        <h3 class="flop-30-title">Portefeuille Risque – FLOP 30 (30 CAF les plus à risque)</h3>
        <p class="flop-30-subtitle">Classement par ratio de risque (PAR 0). Données pour la période {{ getPeriodTitle() }}.</p>
      </div>
      <div class="table-wrapper flop-30-table-wrapper">
        <table class="flop-30-table">
          <thead>
            <tr>
              <th class="flop-rang">RANG</th>
              <th class="flop-caf">CAF</th>
              <th class="flop-num">NBRE DE DOSSIERS</th>
              <th class="flop-amount">Encours de crédit</th>
              <th class="flop-num">NBRE DE DOSSIERS IMPAYÉS</th>
              <th class="flop-amount">ENCOURS IMPAYÉS</th>
              <th class="flop-pct">RATIO NBRE DOSSIERS IMPAYÉS</th>
              <th class="flop-pct">RATIO ENCOURS IMPAYÉS</th>
              <th class="flop-par par-0-header">PAR 0</th>
              <th class="flop-par par-30-header">PAR 30</th>
              <th class="flop-par par-90-header">PAR 90</th>
              <th class="flop-par par-180-header">PAR 180</th>
              <th class="flop-par par-360-header">PAR 360</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="cafLoading && flop30Data.length === 0">
              <tr>
                <td class="flop-rang">1</td>
                <td colspan="12" class="flop-loading">🔄 Chargement des données...</td>
              </tr>
              <tr v-for="i in 29" :key="'flop-empty-' + i" class="flop-row flop-row-empty" :class="{ 'flop-row-alt': i % 2 === 0 }">
                <td class="flop-rang">{{ i + 2 }}</td>
                <td class="flop-caf">–</td>
                <td class="flop-num">–</td>
                <td class="flop-amount">–</td>
                <td class="flop-num">–</td>
                <td class="flop-amount">–</td>
                <td class="flop-pct">–</td>
                <td class="flop-pct">–</td>
                <td class="flop-par">–</td>
                <td class="flop-par">–</td>
                <td class="flop-par">–</td>
                <td class="flop-par">–</td>
                <td class="flop-par">–</td>
              </tr>
            </template>
            <template v-else>
              <tr v-for="(item, idx) in flop30Rows" :key="item.empty ? 'flop-row-' + item.rang : getCafRowKey(item, idx)" class="flop-row" :class="{ 'flop-row-alt': idx % 2 === 1, 'flop-row-empty': item.empty }">
                <td class="flop-rang">{{ item.rang }}</td>
                <td class="flop-caf">{{ item.empty ? '–' : (item.agence ? item.agence + ' – ' + item.nom : item.nom) }}</td>
                <td class="flop-num">{{ item.empty ? '–' : formatNumber(item.nbreDossiers) }}</td>
                <td class="flop-amount">{{ item.empty ? '–' : formatCurrency(item.encoursCredit) }}</td>
                <td class="flop-num">{{ item.empty ? '–' : (item.nbreDossiersImpayes != null ? formatNumber(item.nbreDossiersImpayes) : '–') }}</td>
                <td class="flop-amount">{{ item.empty ? '–' : formatCurrency(item.encoursImpayes != null ? item.encoursImpayes : item.encoursCredit) }}</td>
                <td class="flop-pct">{{ item.empty ? '–' : (item.ratioNbreImpayes != null ? formatPercent(item.ratioNbreImpayes) : '–') }}</td>
                <td class="flop-pct">{{ item.empty ? '–' : formatPercent(item.ratioEncoursImpayes != null ? item.ratioEncoursImpayes : getCafPar(item, 'par0')) }}</td>
                <td class="flop-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par0')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par0'))"></span>
                  </template>
                </td>
                <td class="flop-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par30')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par30'))"></span>
                  </template>
                </td>
                <td class="flop-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par90')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par90'))"></span>
                  </template>
                </td>
                <td class="flop-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par180')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par180'))"></span>
                  </template>
                </td>
                <td class="flop-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par360')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par360'))"></span>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Page TOP 50 : tableau des 50 CAF les moins à risque -->
    <div v-if="activeTab === 'top-50'" class="top-50-container">
      <div class="top-50-header">
        <h3 class="top-50-title">Portefeuille Risque – TOP 50 (50 CAF les moins à risque)</h3>
        <p class="top-50-subtitle">Classement par ratio de risque (PAR 0, du plus faible au plus élevé). Période {{ getPeriodTitle() }}.</p>
      </div>
      <div class="table-wrapper top-50-table-wrapper">
        <table class="top-50-table">
          <thead>
            <tr>
              <th class="top-rang">RANG</th>
              <th class="top-caf">CAF</th>
              <th class="top-num">NBRE DE DOSSIERS</th>
              <th class="top-amount">Encours de crédit</th>
              <th class="top-par par-0-header">PAR 0</th>
              <th class="top-par par-30-header">PAR 30</th>
              <th class="top-par par-90-header">PAR 90</th>
              <th class="top-par par-180-header">PAR 180</th>
              <th class="top-par par-360-header">PAR 360</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="cafLoading && top50Data.length === 0">
              <tr>
                <td class="top-rang">1</td>
                <td colspan="8" class="top-loading">🔄 Chargement des données...</td>
              </tr>
              <tr v-for="i in 49" :key="'empty-' + i" class="top-row top-row-empty" :class="{ 'top-row-alt': i % 2 === 0 }">
                <td class="top-rang">{{ i + 2 }}</td>
                <td class="top-caf">–</td>
                <td class="top-num">–</td>
                <td class="top-amount">–</td>
                <td class="top-par">–</td>
                <td class="top-par">–</td>
                <td class="top-par">–</td>
                <td class="top-par">–</td>
                <td class="top-par">–</td>
              </tr>
            </template>
            <template v-else>
              <tr v-for="(item, idx) in top50Rows" :key="item.empty ? 'row-' + item.rang : getCafRowKey(item, idx)" class="top-row" :class="{ 'top-row-alt': idx % 2 === 1, 'top-row-empty': item.empty }">
                <td class="top-rang">{{ item.rang }}</td>
                <td class="top-caf">{{ item.empty ? '–' : (item.agence ? item.agence + ' – ' + item.nom : item.nom) }}</td>
                <td class="top-num">{{ item.empty ? '–' : formatNumber(item.nbreDossiers) }}</td>
                <td class="top-amount">{{ item.empty ? '–' : formatCurrency(item.encoursCredit) }}</td>
                <td class="top-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par0')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par0'))"></span>
                  </template>
                </td>
                <td class="top-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par30')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par30'))"></span>
                  </template>
                </td>
                <td class="top-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par90')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par90'))"></span>
                  </template>
                </td>
                <td class="top-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par180')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par180'))"></span>
                  </template>
                </td>
                <td class="top-par">
                  <template v-if="item.empty">–</template>
                  <template v-else>
                    <span class="par-value">{{ formatPercent(getCafPar(item, 'par360')) }}</span>
                    <span :class="getParIndicatorClass(getCafPar(item, 'par360'))"></span>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pages Entrées PAR 0 / 30 / 90 / 180 / 360 -->
    <div v-if="entreesParTabs.includes(activeTab)" class="entrees-par-page-container">
      <div class="entrees-par-header">
        <h3 class="entrees-par-title">{{ getEntreesParTitle(activeTab) }}</h3>
        <p class="entrees-par-subtitle">Données pour la période {{ getPeriodTitle() }} (mois en cours).</p>
      </div>
      <div class="entrees-par-content">
        <p v-if="entreesParError" class="entrees-par-error">⚠️ {{ entreesParError }}</p>
        <div v-else-if="entreesParLoading" class="entrees-par-loading">🔄 Chargement des entrées PAR et provisions...</div>
        <div v-else class="entrees-par-table-wrapper">
          <table class="entrees-par-table">
            <thead>
              <tr>
                <th>N° Prêt</th>
                <th>BLOC</th>
                <th>Statut déclassement</th>
                <th>Nom client</th>
                <th>Date mise en place</th>
                <th>Agence</th>
                <th>Production (vol.)</th>
                <th>1re échéance</th>
                <th>Encours total</th>
                <th>Encours sain</th>
                <th>Encours impayé</th>
                <th>Durée impayé (j)</th>
                <th>Provisions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="entreesParList.length === 0">
                <td colspan="13" class="entrees-par-empty">Aucune entrée pour ce palier.</td>
              </tr>
              <tr v-for="(row, idx) in entreesParList" :key="row.NO_PRET || row.no_pret || `entrees-par-row-${idx}`">
                <td>{{ row.NO_PRET ?? row.no_pret ?? '–' }}</td>
                <td>{{ row.BLOC ?? row.bloc ?? '–' }}</td>
                <td>{{ row.STATUT_DECLASSEMENT ?? row.statut_declassement ?? '–' }}</td>
                <td>{{ row.NOM_CLIENT ?? row.nom_client ?? '–' }}</td>
                <td>{{ formatDate(row.DATE_MISE_EN_PLACE ?? row.date_mise_en_place) }}</td>
                <td>{{ row.AGENCE ?? row.agence ?? '–' }}</td>
                <td class="number-cell">{{ formatCurrency(row.PRODUCTION_EN_VOLUME ?? row.production_en_volume) }}</td>
                <td>{{ formatDate(row.DATE_PREM_ECHEANCE ?? row.date_prem_echeance) }}</td>
                <td class="number-cell">{{ formatCurrency(row.ENCOURS_TOTAL ?? row.encours_total) }}</td>
                <td class="number-cell">{{ formatCurrency(row.ENCOURS_SAIN ?? row.encours_sain) }}</td>
                <td class="number-cell">{{ formatCurrency(row.ENCOURS_IMPAYE ?? row.encours_impaye) }}</td>
                <td class="number-cell">{{ row.DUREE_IMPAYE_A_DATE ?? row.duree_impaye_a_date ?? '–' }}</td>
                <td class="number-cell">{{ formatCurrency(row.PROVISIONS ?? row.provisions) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tableau PAR AGENCE : AGENCES | ENCOURS | DOSSIERS | PAR 0..360 (date ref, date M, Var) | Provisions -->
    <div v-if="activeTab === 'par-agence'" class="table-container">
      <table class="par-global-table par-agence-table">
        <thead>
          <tr>
            <th rowspan="2" class="territory-col">AGENCES</th>
            <th rowspan="2" class="par-agence-col-encours">ENCOURS</th>
            <th rowspan="2" class="par-agence-col-dossiers">DOSSIERS</th>
            <th colspan="3" class="par-header par-0">PAR 0</th>
            <th colspan="3" class="par-header par-30">PAR 30</th>
            <th colspan="3" class="par-header par-90">PAR 90</th>
            <th colspan="3" class="par-header par-180">PAR 180</th>
            <th colspan="3" class="par-header par-360">PAR 360</th>
            <th rowspan="2" class="par-agence-col-provisions">Provisions</th>
          </tr>
          <tr>
            <th class="par-sub-header par-0">{{ getParAgenceDateShort(selectedMonthRef, selectedYearRef) }}</th>
            <th class="par-sub-header par-0">{{ getParAgenceDateShort(selectedMonth, selectedYear) }}</th>
            <th class="par-sub-header par-0">Variation</th>
            <th class="par-sub-header par-30">{{ getParAgenceDateShort(selectedMonthRef, selectedYearRef) }}</th>
            <th class="par-sub-header par-30">{{ getParAgenceDateShort(selectedMonth, selectedYear) }}</th>
            <th class="par-sub-header par-30">Variation</th>
            <th class="par-sub-header par-90">{{ getParAgenceDateShort(selectedMonthRef, selectedYearRef) }}</th>
            <th class="par-sub-header par-90">{{ getParAgenceDateShort(selectedMonth, selectedYear) }}</th>
            <th class="par-sub-header par-90">Variation</th>
            <th class="par-sub-header par-180">{{ getParAgenceDateShort(selectedMonthRef, selectedYearRef) }}</th>
            <th class="par-sub-header par-180">{{ getParAgenceDateShort(selectedMonth, selectedYear) }}</th>
            <th class="par-sub-header par-180">Variation</th>
            <th class="par-sub-header par-360">{{ getParAgenceDateShort(selectedMonthRef, selectedYearRef) }}</th>
            <th class="par-sub-header par-360">{{ getParAgenceDateShort(selectedMonth, selectedYear) }}</th>
            <th class="par-sub-header par-360">Variation</th>
          </tr>
        </thead>
        <tbody>
          <!-- Chargement : 1 ligne message + lignes vides + Total général -->
          <template v-if="loading">
            <tr class="no-data-row">
              <td colspan="19" style="text-align: center; padding: 20px;">
                🔄 Chargement des données...
              </td>
            </tr>
            <tr v-for="i in 24" :key="'par-agence-empty-' + i" class="agency-row par-agence-row-empty">
              <td class="agency-cell">–</td>
              <td class="par-agence-encours">–</td>
              <td class="par-agence-dossiers">–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td class="par-agence-provisions">–</td>
            </tr>
            <tr class="total-row">
              <td class="total-label"><strong>Total général</strong></td>
              <td class="par-agence-encours">–</td>
              <td class="par-agence-dossiers">–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td class="par-agence-provisions">–</td>
            </tr>
          </template>
          <!-- Pas de données : lignes vides + Total général -->
          <template v-else-if="!parAgenceHasData">
            <tr v-for="i in parAgenceEmptyRowCount" :key="'par-agence-empty-' + i" class="agency-row par-agence-row-empty">
              <td class="agency-cell">–</td>
              <td class="par-agence-encours">–</td>
              <td class="par-agence-dossiers">–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td>–</td><td>–</td><td>–</td>
              <td class="par-agence-provisions">–</td>
            </tr>
            <tr class="total-row">
              <td class="total-label"><strong>Total général</strong></td>
              <td class="par-agence-encours">–</td>
              <td class="par-agence-dossiers">–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td><strong>–</strong></td><td><strong>–</strong></td><td>–</td>
              <td class="par-agence-provisions">–</td>
            </tr>
          </template>
          <!-- Données présentes : territoires, agences, point services, Total général -->
          <template v-else>
            <!-- TERRITOIRE -->
            <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
              <tr class="territory-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                <td class="territory-cell">
                  <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                    {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                  </button>
                  <strong>{{ territory.name }}</strong>
                </td>
                <td class="par-agence-encours">–</td>
                <td class="par-agence-dossiers">–</td>
                <!-- PAR 0 -->
                <td><strong>{{ formatPercentValue(territory.totals?.par0M1 || 0) }}</strong></td>
                <td><strong>{{ formatPercentValue(territory.totals?.par0M || 0) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(territory.totals?.par0M1 || 0, territory.totals?.par0M || 0))">
                  <strong>{{ formatVariation(calculatePercent(territory.totals?.par0M1 || 0, territory.totals?.par0M || 0)) }}</strong>
                </td>
                <!-- PAR 30 -->
                <td><strong>{{ formatPercentValue(territory.totals?.par30M1 || 0) }}</strong></td>
                <td><strong>{{ formatPercentValue(territory.totals?.par30M || 0) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(territory.totals?.par30M1 || 0, territory.totals?.par30M || 0))">
                  <strong>{{ formatVariation(calculatePercent(territory.totals?.par30M1 || 0, territory.totals?.par30M || 0)) }}</strong>
                </td>
                <!-- PAR 90 -->
                <td><strong>{{ formatPercentValue(territory.totals?.par90M1 || 0) }}</strong></td>
                <td><strong>{{ formatPercentValue(territory.totals?.par90M || 0) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(territory.totals?.par90M1 || 0, territory.totals?.par90M || 0))">
                  <strong>{{ formatVariation(calculatePercent(territory.totals?.par90M1 || 0, territory.totals?.par90M || 0)) }}</strong>
                </td>
                <!-- PAR 180 -->
                <td><strong>{{ formatPercentValue(territory.totals?.par180M1 || 0) }}</strong></td>
                <td><strong>{{ formatPercentValue(territory.totals?.par180M || 0) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(territory.totals?.par180M1 || 0, territory.totals?.par180M || 0))">
                  <strong>{{ formatVariation(calculatePercent(territory.totals?.par180M1 || 0, territory.totals?.par180M || 0)) }}</strong>
                </td>
                <!-- PAR 360 -->
                <td><strong>{{ formatPercentValue(territory.totals?.par360M1 || 0) }}</strong></td>
                <td><strong>{{ formatPercentValue(territory.totals?.par360M || 0) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(territory.totals?.par360M1 || 0, territory.totals?.par360M || 0))">
                  <strong>{{ formatVariation(calculatePercent(territory.totals?.par360M1 || 0, territory.totals?.par360M || 0)) }}</strong>
                </td>
                <td class="par-agence-provisions">–</td>
              </tr>
              <!-- Agences dans chaque territoire -->
              <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                <template v-for="(agency, index) in (territory.agencies || [])" :key="getAgencyKey(agency, index)">
                  <tr class="agency-row">
                    <td class="agency-cell">
                      {{ agency.name || agency.AGENCE || getAgencyName(agency) }}
                    </td>
                    <td class="par-agence-encours">
                      <div class="par-agence-bar-wrap">
                        <span class="par-agence-value">{{ getAgencyEncours(agency) != null ? formatCurrency(getAgencyEncours(agency)) : '–' }}</span>
                        <div class="par-agence-bar par-agence-bar-encours" :style="{ width: getBarPercent(getAgencyEncours(agency), parAgenceMaxEncours) + '%' }"></div>
                      </div>
                    </td>
                    <td class="par-agence-dossiers">
                      <div class="par-agence-bar-wrap">
                        <span class="par-agence-value">{{ getAgencyDossiers(agency) != null ? formatNumber(getAgencyDossiers(agency)) : '–' }}</span>
                        <div class="par-agence-bar par-agence-bar-dossiers" :style="{ width: getBarPercent(getAgencyDossiers(agency), parAgenceMaxDossiers) + '%' }"></div>
                      </div>
                    </td>
                    <!-- PAR 0 -->
                    <td><span class="par-agence-cell-content">{{ formatPercentValue(getAgencyValue(agency, 'PAR_0_M_1')) }}</span><span :class="getRecapIndicatorClass(getAgencyValue(agency, 'PAR_0_M_1'), 'par0')"></span></td>
                    <td><span class="par-agence-cell-content">{{ formatPercentValue(getAgencyValue(agency, 'PAR_0_M')) }}</span><span :class="getRecapIndicatorClass(getAgencyValue(agency, 'PAR_0_M'), 'par0')"></span></td>
                    <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M')))">
                      <span class="par-agence-cell-content">{{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M'))) }}</span>
                      <span :class="getRecapVarIndicatorClass(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M')))"></span>
                    </td>
                    <!-- PAR 30 -->
                    <td><span class="par-agence-cell-content">{{ formatPercentValue(getAgencyValue(agency, 'PAR_30_M_1')) }}</span><span :class="getRecapIndicatorClass(getAgencyValue(agency, 'PAR_30_M_1'), 'par30')"></span></td>
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_30_M')) }}</td>
                    <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_30_M_1'), getAgencyValue(agency, 'PAR_30_M')))">
                      {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_30_M_1'), getAgencyValue(agency, 'PAR_30_M'))) }}
                    </td>
                    <!-- PAR 90 -->
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_90_M_1')) }}</td>
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_90_M')) }}</td>
                    <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_90_M_1'), getAgencyValue(agency, 'PAR_90_M')))">
                      {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_90_M_1'), getAgencyValue(agency, 'PAR_90_M'))) }}
                    </td>
                    <!-- PAR 180 -->
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_180_M_1')) }}</td>
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_180_M')) }}</td>
                    <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_180_M_1'), getAgencyValue(agency, 'PAR_180_M')))">
                      {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_180_M_1'), getAgencyValue(agency, 'PAR_180_M'))) }}
                    </td>
                    <!-- PAR 360 -->
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_360_M_1')) }}</td>
                    <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_360_M')) }}</td>
                    <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_360_M_1'), getAgencyValue(agency, 'PAR_360_M')))">
                      {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_360_M_1'), getAgencyValue(agency, 'PAR_360_M'))) }}
                    </td>
                    <td class="par-agence-provisions">
                      <div class="par-agence-bar-wrap">
                        <span class="par-agence-value">{{ getAgencyProvisions(agency) != null ? formatCurrency(getAgencyProvisions(agency)) : '–' }}</span>
                        <div class="par-agence-bar par-agence-bar-provisions" :style="{ width: getBarPercent(getAgencyProvisions(agency), parAgenceMaxProvisions) + '%' }"></div>
                      </div>
                    </td>
                  </tr>
                </template>
              </template>
            </template>
            
            <!-- POINT SERVICES -->
            <template v-if="filteredHierarchicalData['POINT SERVICES'] && Object.keys(filteredHierarchicalData['POINT SERVICES']).length > 0">
              <tr class="territory-row" @click="toggleExpand('POINT SERVICES')">
                <td class="territory-cell">
                  <button class="expand-btn" @click.stop="toggleExpand('POINT SERVICES')">
                    {{ expandedSections['POINT SERVICES'] ? '−' : '+' }}
                  </button>
                  <strong>POINT SERVICES</strong>
                </td>
                <td class="par-agence-encours">–</td>
                <td class="par-agence-dossiers">–</td>
                <!-- PAR 0 -->
                <td><strong>{{ formatPercentValue(pointServicesTotal.par0M1) }}</strong></td>
                <td><strong>{{ formatPercentValue(pointServicesTotal.par0M) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(pointServicesTotal.par0M1, pointServicesTotal.par0M))">
                  <strong>{{ formatVariation(calculatePercent(pointServicesTotal.par0M1, pointServicesTotal.par0M)) }}</strong>
                </td>
                <!-- PAR 30 -->
                <td><strong>{{ formatPercentValue(pointServicesTotal.par30M1) }}</strong></td>
                <td><strong>{{ formatPercentValue(pointServicesTotal.par30M) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(pointServicesTotal.par30M1, pointServicesTotal.par30M))">
                  <strong>{{ formatVariation(calculatePercent(pointServicesTotal.par30M1, pointServicesTotal.par30M)) }}</strong>
                </td>
                <!-- PAR 90 -->
                <td><strong>{{ formatPercentValue(pointServicesTotal.par90M1) }}</strong></td>
                <td><strong>{{ formatPercentValue(pointServicesTotal.par90M) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(pointServicesTotal.par90M1, pointServicesTotal.par90M))">
                  <strong>{{ formatVariation(calculatePercent(pointServicesTotal.par90M1, pointServicesTotal.par90M)) }}</strong>
                </td>
                <!-- PAR 180 -->
                <td><strong>{{ formatPercentValue(pointServicesTotal.par180M1) }}</strong></td>
                <td><strong>{{ formatPercentValue(pointServicesTotal.par180M) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(pointServicesTotal.par180M1, pointServicesTotal.par180M))">
                  <strong>{{ formatVariation(calculatePercent(pointServicesTotal.par180M1, pointServicesTotal.par180M)) }}</strong>
                </td>
                <!-- PAR 360 -->
                <td><strong>{{ formatPercentValue(pointServicesTotal.par360M1) }}</strong></td>
                <td><strong>{{ formatPercentValue(pointServicesTotal.par360M) }}</strong></td>
                <td :class="getVariationClass(calculatePercent(pointServicesTotal.par360M1, pointServicesTotal.par360M))">
                  <strong>{{ formatVariation(calculatePercent(pointServicesTotal.par360M1, pointServicesTotal.par360M)) }}</strong>
                </td>
                <td class="par-agence-provisions">–</td>
              </tr>
              <!-- Agences des points de service -->
              <template v-if="expandedSections['POINT SERVICES']">
                <template v-for="(servicePoint, servicePointKey) in filteredHierarchicalData['POINT SERVICES']" :key="servicePointKey">
                  <template v-if="servicePoint.agencies && servicePoint.agencies.length > 0">
                    <template v-for="(agency, index) in servicePoint.agencies" :key="getAgencyKey(agency, index)">
                      <tr class="agency-row">
                        <td class="agency-cell">
                          {{ agency.name || agency.AGENCE || getAgencyName(agency) }}
                        </td>
                        <td class="par-agence-encours">
                          <div class="par-agence-bar-wrap">
                            <span class="par-agence-value">{{ getAgencyEncours(agency) != null ? formatCurrency(getAgencyEncours(agency)) : '–' }}</span>
                            <div class="par-agence-bar par-agence-bar-encours" :style="{ width: getBarPercent(getAgencyEncours(agency), parAgenceMaxEncours) + '%' }"></div>
                          </div>
                        </td>
                        <td class="par-agence-dossiers">
                          <div class="par-agence-bar-wrap">
                            <span class="par-agence-value">{{ getAgencyDossiers(agency) != null ? formatNumber(getAgencyDossiers(agency)) : '–' }}</span>
                            <div class="par-agence-bar par-agence-bar-dossiers" :style="{ width: getBarPercent(getAgencyDossiers(agency), parAgenceMaxDossiers) + '%' }"></div>
                          </div>
                        </td>
                        <!-- PAR 0 -->
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_0_M_1')) }}</td>
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_0_M')) }}</td>
                        <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M')))">
                          {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M'))) }}
                        </td>
                        <!-- PAR 30 -->
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_30_M_1')) }}</td>
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_30_M')) }}</td>
                        <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_30_M_1'), getAgencyValue(agency, 'PAR_30_M')))">
                          {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_30_M_1'), getAgencyValue(agency, 'PAR_30_M'))) }}
                        </td>
                        <!-- PAR 90 -->
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_90_M_1')) }}</td>
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_90_M')) }}</td>
                        <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_90_M_1'), getAgencyValue(agency, 'PAR_90_M')))">
                          {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_90_M_1'), getAgencyValue(agency, 'PAR_90_M'))) }}
                        </td>
                        <!-- PAR 180 -->
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_180_M_1')) }}</td>
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_180_M')) }}</td>
                        <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_180_M_1'), getAgencyValue(agency, 'PAR_180_M')))">
                          {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_180_M_1'), getAgencyValue(agency, 'PAR_180_M'))) }}
                        </td>
                        <!-- PAR 360 -->
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_360_M_1')) }}</td>
                        <td>{{ formatPercentValue(getAgencyValue(agency, 'PAR_360_M')) }}</td>
                        <td :class="getVariationClass(calculatePercent(getAgencyValue(agency, 'PAR_360_M_1'), getAgencyValue(agency, 'PAR_360_M')))">
                          {{ formatVariation(calculatePercent(getAgencyValue(agency, 'PAR_360_M_1'), getAgencyValue(agency, 'PAR_360_M'))) }}
                        </td>
                        <td class="par-agence-provisions">
                          <div class="par-agence-bar-wrap">
                            <span class="par-agence-value">{{ getAgencyProvisions(agency) != null ? formatCurrency(getAgencyProvisions(agency)) : '–' }}</span>
                            <div class="par-agence-bar par-agence-bar-provisions" :style="{ width: getBarPercent(getAgencyProvisions(agency), parAgenceMaxProvisions) + '%' }"></div>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </template>
            
            <!-- TOTAL GÉNÉRAL -->
            <tr class="total-row">
              <td class="total-label"><strong>Total général</strong></td>
              <td class="par-agence-encours">–</td>
              <td class="par-agence-dossiers">–</td>
              <!-- PAR 0 -->
              <td><strong>{{ formatPercentValue(totalGeneral.par0M1) }}</strong></td>
              <td><strong>{{ formatPercentValue(totalGeneral.par0M) }}</strong></td>
              <td :class="getVariationClass(totalGeneral.par0Percent)">
                <strong>{{ formatVariation(totalGeneral.par0Percent) }}</strong>
              </td>
              <!-- PAR 30 -->
              <td><strong>{{ formatPercentValue(totalGeneral.par30M1) }}</strong></td>
              <td><strong>{{ formatPercentValue(totalGeneral.par30M) }}</strong></td>
              <td :class="getVariationClass(totalGeneral.par30Percent)">
                <strong>{{ formatVariation(totalGeneral.par30Percent) }}</strong>
              </td>
              <!-- PAR 90 -->
              <td><strong>{{ formatPercentValue(totalGeneral.par90M1) }}</strong></td>
              <td><strong>{{ formatPercentValue(totalGeneral.par90M) }}</strong></td>
              <td :class="getVariationClass(totalGeneral.par90Percent)">
                <strong>{{ formatVariation(totalGeneral.par90Percent) }}</strong>
              </td>
              <!-- PAR 180 -->
              <td><strong>{{ formatPercentValue(totalGeneral.par180M1) }}</strong></td>
              <td><strong>{{ formatPercentValue(totalGeneral.par180M) }}</strong></td>
              <td :class="getVariationClass(totalGeneral.par180Percent)">
                <strong>{{ formatVariation(totalGeneral.par180Percent) }}</strong>
              </td>
              <!-- PAR 360 -->
              <td><strong>{{ formatPercentValue(totalGeneral.par360M1) }}</strong></td>
              <td><strong>{{ formatPercentValue(totalGeneral.par360M) }}</strong></td>
              <td :class="getVariationClass(totalGeneral.par360Percent)">
                <strong>{{ formatVariation(totalGeneral.par360Percent) }}</strong>
              </td>
              <td class="par-agence-provisions">–</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'PortefeuilleRisqueGlobalSection',
  data() {
    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentYear = now.getFullYear();
    const refMonth = currentMonth === 1 ? 12 : currentMonth - 1;
    const refYear = currentMonth === 1 ? currentYear - 1 : currentYear;
    return {
      selectedMonth: currentMonth,
      selectedYear: currentYear,
      selectedMonthRef: refMonth,
      selectedYearRef: refYear,
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      loading: false,
      cafLoading: false,
      errorMessage: null,
      hierarchicalDataFromBackend: {
        TERRITOIRE: {},
        'POINT SERVICES': {}
      },
      expandedSections: {},
      activeTab: 'par-caf',
      selectedAgency: 'Toutes les agences',
      agencySearch: '',
      cafData: [],
      allAgenciesKey: 'Toutes les agences',
      agencies: [
        'AGENCE KAOLACK',
        'AGENCE LINGUERE\'LA',
        'AGENCE LOUGA',
        'AGENCE MARISTES',
        'AGENCE MBOUR',
        'AGENCE OUROSSOGUI',
        'AGENCE PARCELLES',
        'AGENCE PIKINE',
        'AGENCE PRINCIPALE',
        'AGENCE RUFISQUE',
        'AGENCE SAINT-LOUIS',
        'AGENCE THIES',
        'AGENCE ZIGUINCHOR'
      ],
      entreesParList: [],
      entreesParLoading: false,
      entreesParError: null
    };
  },
  computed: {
    entreesParTabs() {
      return ['entrees-par0', 'entrees-par30', 'entrees-par90', 'entrees-par180', 'entrees-par360'];
    },
    currentEntreesParBucket() {
      const map = { 'entrees-par0': 0, 'entrees-par30': 30, 'entrees-par90': 90, 'entrees-par180': 180, 'entrees-par360': 360 };
      return map[this.activeTab] ?? 0;
    },
    years() {
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let i = currentYear - 5; i <= currentYear + 2; i++) {
        years.push(i);
      }
      return years;
    },
    filteredAgencies() {
      const list = [this.allAgenciesKey, ...this.agencies];
      if (!this.agencySearch) {
        return list;
      }
      const search = this.agencySearch.toLowerCase();
      if (this.allAgenciesKey.toLowerCase().includes(search)) {
        return [this.allAgenciesKey, ...this.agencies.filter(agency =>
          agency.toLowerCase().includes(search)
        )];
      }
      return this.agencies.filter(agency =>
        agency.toLowerCase().includes(search)
      );
    },
    showAgencyColumn() {
      return this.cafData.length > 0 && this.cafData.some(item => item.agence);
    },
    tableColspan() {
      return this.showAgencyColumn ? 9 : 8;
    },
    /** Max ENCOURS / DOSSIERS / Provisions sur toutes les agences (pour barres PAR AGENCE). */
    parAgenceMaxEncours() {
      let max = 0;
      this.parAgenceAllAgencies.forEach(agency => {
        const v = this.getAgencyEncours(agency);
        if (v != null && v > max) max = v;
      });
      return max || 1;
    },
    parAgenceMaxDossiers() {
      let max = 0;
      this.parAgenceAllAgencies.forEach(agency => {
        const v = this.getAgencyDossiers(agency);
        if (v != null && v > max) max = v;
      });
      return max || 1;
    },
    parAgenceMaxProvisions() {
      let max = 0;
      this.parAgenceAllAgencies.forEach(agency => {
        const v = this.getAgencyProvisions(agency);
        if (v != null && v > max) max = v;
      });
      return max || 1;
    },
    /** True si on a au moins un territoire ou des agences point de service (données PAR AGENCE). */
    parAgenceHasData() {
      const h = this.filteredHierarchicalData || {};
      const territories = h.TERRITOIRE && Object.keys(h.TERRITOIRE).length > 0;
      if (territories) return true;
      const ps = h['POINT SERVICES'];
      if (ps && ps.service_points && (ps.service_points.agencies || []).length > 0) return true;
      return false;
    },
    /** Nombre de lignes vides à afficher quand pas de données (tableau toujours visible). */
    parAgenceEmptyRowCount() {
      return 25;
    },
    /** Liste plate de toutes les agences (territoires + points de service) pour max barres. */
    parAgenceAllAgencies() {
      const list = [];
      const h = this.filteredHierarchicalData || {};
      (h.TERRITOIRE && Object.values(h.TERRITOIRE))?.forEach(territory => {
        (territory.agencies || []).forEach(agency => list.push(agency));
      });
      const ps = h['POINT SERVICES'];
      if (ps && ps.service_points && ps.service_points.agencies) {
        ps.service_points.agencies.forEach(agency => list.push(agency));
      }
      return list;
    },
    /** Toujours 50 lignes pour le tableau PAR | CAF (données ou placeholders) */
    parCafRows() {
      const data = this.cafData || [];
      const rows = [];
      for (let i = 0; i < 50; i++) {
        rows.push(data[i] ? { ...data[i] } : { empty: true });
      }
      return rows;
    },
    /** Les 30 CAF les plus à risque (tri par PAR 0 décroissant) pour l'onglet FLOP 30 */
    flop30Data() {
      if (!this.cafData || this.cafData.length === 0) return [];
      const sorted = [...this.cafData].sort((a, b) => {
        const par0A = this.getCafPar(a, 'par0') || 0;
        const par0B = this.getCafPar(b, 'par0') || 0;
        return par0B - par0A;
      });
      return sorted.slice(0, 30).map((item, idx) => {
        const par0 = this.getCafPar(item, 'par0') || 0;
        const encours = this.toSingleNumber(item.encoursCredit) || 0;
        return {
          ...item,
          rang: idx + 1,
          encoursImpayes: item.encoursImpayes != null ? item.encoursImpayes : encours,
          ratioEncoursImpayes: item.ratioEncoursImpayes != null ? item.ratioEncoursImpayes : par0,
          nbreDossiersImpayes: item.nbreDossiersImpayes,
          ratioNbreImpayes: item.ratioNbreImpayes
        };
      });
    },
    /** Toujours 30 lignes pour le tableau FLOP 30 (données ou placeholders) */
    flop30Rows() {
      const data = this.flop30Data;
      const rows = [];
      for (let i = 0; i < 30; i++) {
        if (data[i]) {
          const item = data[i];
          rows.push({ ...item, rang: i + 1 });
        } else {
          rows.push({ rang: i + 1, empty: true });
        }
      }
      return rows;
    },
    /** Les 50 CAF les moins à risque (tri par PAR 0 croissant) pour l'onglet TOP 50 */
    top50Data() {
      if (!this.cafData || this.cafData.length === 0) return [];
      const sorted = [...this.cafData].sort((a, b) => {
        const par0A = this.getCafPar(a, 'par0') || 0;
        const par0B = this.getCafPar(b, 'par0') || 0;
        return par0A - par0B;
      });
      return sorted.slice(0, 50).map((item, idx) => ({
        ...item,
        rang: idx + 1
      }));
    },
    /** Toujours 50 lignes pour le tableau TOP 50 (données ou placeholders) */
    top50Rows() {
      const data = this.top50Data;
      const rows = [];
      for (let i = 0; i < 50; i++) {
        rows.push(data[i] ? { ...data[i], rang: i + 1 } : { rang: i + 1, empty: true });
      }
      return rows;
    },
    filteredHierarchicalData() {
      return this.hierarchicalData || {
        TERRITOIRE: {},
        'POINT SERVICES': {}
      };
    },
    hierarchicalData() {
      if (this.hierarchicalDataFromBackend && typeof this.hierarchicalDataFromBackend === 'object') {
        try {
          return JSON.parse(JSON.stringify(this.hierarchicalDataFromBackend));
        } catch (e) {
          return this.hierarchicalDataFromBackend;
        }
      }
      return {
        TERRITOIRE: {},
        'POINT SERVICES': {}
      };
    },
    pointServicesTotal() {
      if (!this.filteredHierarchicalData || !this.filteredHierarchicalData['POINT SERVICES']) {
        return {
          par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
          par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
          par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0,
          par180M1: 0, par180M: 0, par180Ecart: 0, par180Percent: 0,
          par360M1: 0, par360M: 0, par360Ecart: 0, par360Percent: 0
        };
      }
      
      let total = {
        par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
        par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
        par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0,
        par180M1: 0, par180M: 0, par180Ecart: 0, par180Percent: 0,
        par360M1: 0, par360M: 0, par360Ecart: 0, par360Percent: 0
      };
      
      Object.values(this.filteredHierarchicalData['POINT SERVICES']).forEach(servicePoint => {
        if (servicePoint.totals) {
          total.par0M1 += servicePoint.totals.par0M1 || 0;
          total.par0M += servicePoint.totals.par0M || 0;
          total.par30M1 += servicePoint.totals.par30M1 || 0;
          total.par30M += servicePoint.totals.par30M || 0;
          total.par90M1 += servicePoint.totals.par90M1 || 0;
          total.par90M += servicePoint.totals.par90M || 0;
          total.par180M1 += servicePoint.totals.par180M1 || 0;
          total.par180M += servicePoint.totals.par180M || 0;
          total.par360M1 += servicePoint.totals.par360M1 || 0;
          total.par360M += servicePoint.totals.par360M || 0;
        } else if (servicePoint.agencies) {
          servicePoint.agencies.forEach(agency => {
            total.par0M1 += this.getAgencyValue(agency, 'PAR_0_M_1') || 0;
            total.par0M += this.getAgencyValue(agency, 'PAR_0_M') || 0;
            total.par30M1 += this.getAgencyValue(agency, 'PAR_30_M_1') || 0;
            total.par30M += this.getAgencyValue(agency, 'PAR_30_M') || 0;
            total.par90M1 += this.getAgencyValue(agency, 'PAR_90_M_1') || 0;
            total.par90M += this.getAgencyValue(agency, 'PAR_90_M') || 0;
            total.par180M1 += this.getAgencyValue(agency, 'PAR_180_M_1') || 0;
            total.par180M += this.getAgencyValue(agency, 'PAR_180_M') || 0;
            total.par360M1 += this.getAgencyValue(agency, 'PAR_360_M_1') || 0;
            total.par360M += this.getAgencyValue(agency, 'PAR_360_M') || 0;
          });
        }
      });
      
      total.par0Ecart = total.par0M - total.par0M1;
      total.par30Ecart = total.par30M - total.par30M1;
      total.par90Ecart = total.par90M - total.par90M1;
      total.par180Ecart = total.par180M - total.par180M1;
      total.par360Ecart = total.par360M - total.par360M1;
      
      total.par0Percent = total.par0M1 !== 0 ? (total.par0Ecart / total.par0M1) * 100 : 0;
      total.par30Percent = total.par30M1 !== 0 ? (total.par30Ecart / total.par30M1) * 100 : 0;
      total.par90Percent = total.par90M1 !== 0 ? (total.par90Ecart / total.par90M1) * 100 : 0;
      total.par180Percent = total.par180M1 !== 0 ? (total.par180Ecart / total.par180M1) * 100 : 0;
      total.par360Percent = total.par360M1 !== 0 ? (total.par360Ecart / total.par360M1) * 100 : 0;
      
      return total;
    },
    totalGeneral() {
      const territoire = this.territoireTotal;
      const pointServices = this.pointServicesTotal;
      
      const par0M1 = territoire.par0M1 + pointServices.par0M1;
      const par0M = territoire.par0M + pointServices.par0M;
      const par0Ecart = par0M - par0M1;
      const par0Percent = par0M1 !== 0 ? (par0Ecart / par0M1) * 100 : 0;
      
      const par30M1 = territoire.par30M1 + pointServices.par30M1;
      const par30M = territoire.par30M + pointServices.par30M;
      const par30Ecart = par30M - par30M1;
      const par30Percent = par30M1 !== 0 ? (par30Ecart / par30M1) * 100 : 0;
      
      const par90M1 = territoire.par90M1 + pointServices.par90M1;
      const par90M = territoire.par90M + pointServices.par90M;
      const par90Ecart = par90M - par90M1;
      const par90Percent = par90M1 !== 0 ? (par90Ecart / par90M1) * 100 : 0;
      
      const par180M1 = territoire.par180M1 + pointServices.par180M1;
      const par180M = territoire.par180M + pointServices.par180M;
      const par180Ecart = par180M - par180M1;
      const par180Percent = par180M1 !== 0 ? (par180Ecart / par180M1) * 100 : 0;
      
      const par360M1 = territoire.par360M1 + pointServices.par360M1;
      const par360M = territoire.par360M + pointServices.par360M;
      const par360Ecart = par360M - par360M1;
      const par360Percent = par360M1 !== 0 ? (par360Ecart / par360M1) * 100 : 0;
      
      return {
        par0M1, par0M, par0Ecart, par0Percent,
        par30M1, par30M, par30Ecart, par30Percent,
        par90M1, par90M, par90Ecart, par90Percent,
        par180M1, par180M, par180Ecart, par180Percent,
        par360M1, par360M, par360Ecart, par360Percent
      };
    },
    /** Lignes du tableau RECAP : Encours, PAR 0..360, Provisions, Volume d'impayé */
    recapRows() {
      const tot = this.totalGeneral();
      const encoursM = this.cafData && this.cafData.length > 0
        ? this.cafData.reduce((s, i) => s + (this.toSingleNumber(i.encoursCredit) || 0), 0)
        : null;
      const encoursM1 = null; // non fourni par l'API actuelle
      const encoursVar = encoursM != null && encoursM1 != null && encoursM1 !== 0
        ? ((encoursM - encoursM1) / encoursM1) * 100
        : null;
      return [
        { key: 'encours', label: 'Encours de Crédit', valueM: encoursM, valueM1: encoursM1, varPercent: encoursVar, rowClass: '', isCurrency: true },
        { key: 'par0', label: 'PAR 0', valueM: tot.par0M, valueM1: tot.par0M1, varPercent: tot.par0Percent, rowClass: 'recap-row-par0', isCurrency: false },
        { key: 'par30', label: 'PAR 30', valueM: tot.par30M, valueM1: tot.par30M1, varPercent: tot.par30Percent, rowClass: 'recap-row-par30', isCurrency: false },
        { key: 'par90', label: 'PAR 90', valueM: tot.par90M, valueM1: tot.par90M1, varPercent: tot.par90Percent, rowClass: 'recap-row-par90', isCurrency: false },
        { key: 'par180', label: 'PAR 180', valueM: tot.par180M, valueM1: tot.par180M1, varPercent: tot.par180Percent, rowClass: 'recap-row-par180', isCurrency: false },
        { key: 'par360', label: 'PAR 360', valueM: tot.par360M, valueM1: tot.par360M1, varPercent: tot.par360Percent, rowClass: 'recap-row-par360', isCurrency: false },
        { key: 'provisions', label: 'Provisions', valueM: null, valueM1: null, varPercent: null, rowClass: '', isCurrency: true },
        { key: 'volume_impaye', label: 'Volume d\'impayé', valueM: null, valueM1: null, varPercent: null, rowClass: '', isCurrency: true }
      ];
    },
    territoireTotal() {
      if (!this.filteredHierarchicalData || !this.filteredHierarchicalData.TERRITOIRE) {
        return {
          par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
          par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
          par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0,
          par180M1: 0, par180M: 0, par180Ecart: 0, par180Percent: 0,
          par360M1: 0, par360M: 0, par360Ecart: 0, par360Percent: 0
        };
      }
      
      let total = {
        par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
        par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
        par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0,
        par180M1: 0, par180M: 0, par180Ecart: 0, par180Percent: 0,
        par360M1: 0, par360M: 0, par360Ecart: 0, par360Percent: 0
      };
      
      Object.values(this.filteredHierarchicalData.TERRITOIRE).forEach(territory => {
        if (territory.totals) {
          total.par0M1 += territory.totals.par0M1 || 0;
          total.par0M += territory.totals.par0M || 0;
          total.par30M1 += territory.totals.par30M1 || 0;
          total.par30M += territory.totals.par30M || 0;
          total.par90M1 += territory.totals.par90M1 || 0;
          total.par90M += territory.totals.par90M || 0;
          total.par180M1 += territory.totals.par180M1 || 0;
          total.par180M += territory.totals.par180M || 0;
          total.par360M1 += territory.totals.par360M1 || 0;
          total.par360M += territory.totals.par360M || 0;
        }
      });
      
      total.par0Ecart = total.par0M - total.par0M1;
      total.par30Ecart = total.par30M - total.par30M1;
      total.par90Ecart = total.par90M - total.par90M1;
      total.par180Ecart = total.par180M - total.par180M1;
      total.par360Ecart = total.par360M - total.par360M1;
      
      total.par0Percent = total.par0M1 !== 0 ? (total.par0Ecart / total.par0M1) * 100 : 0;
      total.par30Percent = total.par30M1 !== 0 ? (total.par30Ecart / total.par30M1) * 100 : 0;
      total.par90Percent = total.par90M1 !== 0 ? (total.par90Ecart / total.par90M1) * 100 : 0;
      total.par180Percent = total.par180M1 !== 0 ? (total.par180Ecart / total.par180M1) * 100 : 0;
      total.par360Percent = total.par360M1 !== 0 ? (total.par360Ecart / total.par360M1) * 100 : 0;
      
      return total;
    }
  },
  watch: {
    activeTab(newVal) {
      if ((newVal === 'par-caf' || newVal === 'flop-30' || newVal === 'top-50') && !this.cafLoading && this.cafData.length === 0) {
        this.fetchCafData(this.selectedAgency);
      }
      if (this.entreesParTabs.includes(newVal)) {
        this.fetchEntreesParData();
      }
    },
    selectedMonth() {
      if (this.entreesParTabs.includes(this.activeTab)) this.fetchEntreesParData();
    },
    selectedYear() {
      if (this.entreesParTabs.includes(this.activeTab)) this.fetchEntreesParData();
    }
  },
  mounted() {
    this.fetchData();
    if (this.activeTab === 'par-caf') {
      this.fetchCafData(this.selectedAgency);
    }
  },
  methods: {
    getPeriodTitle() {
      return `${this.getDateRefLabel()} / ${this.getDateMLabel()}`;
    },
    getEntreesParTitle(tab) {
      const labels = { 'entrees-par0': 'Entrées PAR0', 'entrees-par30': 'Entrées PAR30', 'entrees-par90': 'Entrées PAR90', 'entrees-par180': 'Entrées PAR180', 'entrees-par360': 'Entrées PAR360' };
      return labels[tab] || 'Entrées PAR';
    },
    getEntreesParLabel(tab) {
      const labels = { 'entrees-par0': 'PAR0', 'entrees-par30': 'PAR30', 'entrees-par90': 'PAR90', 'entrees-par180': 'PAR180', 'entrees-par360': 'PAR360' };
      return labels[tab] || '';
    },
    getEntreesParBucket(tab) {
      const map = { 'entrees-par0': 0, 'entrees-par30': 30, 'entrees-par90': 90, 'entrees-par180': 180, 'entrees-par360': 360 };
      return map[tab] ?? 0;
    },
    async fetchEntreesParData() {
      if (!this.entreesParTabs.includes(this.activeTab)) return;
      const par = this.getEntreesParBucket(this.activeTab);
      this.entreesParLoading = true;
      this.entreesParError = null;
      try {
        const response = await axios.get('/api/oracle/data/entrees-par', {
          params: {
            month: this.selectedMonth,
            year: this.selectedYear,
            par,
            _t: Date.now()
          },
          timeout: 300000
        });
        const payload = response.data || {};
        this.entreesParList = Array.isArray(payload.data) ? payload.data : (Array.isArray(payload) ? payload : []);
      } catch (err) {
        console.error('Erreur chargement entrées PAR:', err);
        this.entreesParError = err.response?.data?.detail || err.response?.data?.message || err.response?.data?.error || 'Erreur lors du chargement des entrées PAR.';
        this.entreesParList = [];
      } finally {
        this.entreesParLoading = false;
      }
    },
    handlePeriodChange() {
      this.fetchData();
      this.fetchCafData(this.selectedAgency);
    },
    async fetchData() {
      this.loading = true;
      this.errorMessage = null;
      
      try {
        const response = await axios.get('/api/oracle/data/portefeuille-risque', {
          params: {
            month: this.selectedMonth,
            year: this.selectedYear,
            month_ref: this.selectedMonthRef,
            year_ref: this.selectedYearRef,
            _t: Date.now()
          },
          timeout: 300000
        });
        
        if (response.data && response.data.hierarchicalData) {
          this.hierarchicalDataFromBackend = response.data.hierarchicalData;
        } else {
          this.hierarchicalDataFromBackend = {
            TERRITOIRE: {},
            'POINT SERVICES': {}
          };
        }
      } catch (err) {
        console.error('Erreur lors de la récupération des données PAR:', err);
        this.errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Erreur lors de la récupération des données';
        this.hierarchicalDataFromBackend = {
          TERRITOIRE: {},
          'POINT SERVICES': {}
        };
      } finally {
        this.loading = false;
      }
    },
    handleMonthChange() {
      this.fetchData();
      this.fetchCafData(this.selectedAgency);
    },
    handleYearChange() {
      this.fetchData();
      this.fetchCafData(this.selectedAgency);
    },
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    getAgencyKey(agency, index) {
      return agency.name || agency.AGENCE || agency.CODE_AGENCE || `agency-${index}`;
    },
    getAgencyName(agency) {
      return agency.name || agency.AGENCE || agency.NOM_AGENCE || '-';
    },
    getAgencyValue(agency, field) {
      if (agency.totals) {
        const totalMap = {
          'PAR_0_M_1': 'par0M1',
          'PAR_0_M': 'par0M',
          'PAR_30_M_1': 'par30M1',
          'PAR_30_M': 'par30M',
          'PAR_90_M_1': 'par90M1',
          'PAR_90_M': 'par90M',
          'PAR_180_M_1': 'par180M1',
          'PAR_180_M': 'par180M',
          'PAR_360_M_1': 'par360M1',
          'PAR_360_M': 'par360M'
        };
        
        const totalKey = totalMap[field];
        if (totalKey && agency.totals[totalKey] !== undefined) {
          return agency.totals[totalKey];
        }
      }
      
      if (agency.data && agency.data.length > 0) {
        return agency.data.reduce((sum, row) => {
          const value = row[field] || row[field.toUpperCase()] || 0;
          return sum + (parseFloat(value) || 0);
        }, 0);
      }
      
      const value = agency[field] || 
                   agency[field.toUpperCase()] ||
                  0;
      return value === null || value === undefined ? 0 : parseFloat(value) || 0;
    },
    /** Encours pour une agence (backend peut exposer ENCOURS_M ou encours_credit). */
    getAgencyEncours(agency) {
      if (!agency) return null;
      const v = agency.totals?.encoursM ?? agency.totals?.encours ?? agency.ENCOURS_M ?? agency.encours_credit;
      if (v != null && v !== '') return this.toSingleNumber(v);
      return null;
    },
    /** Nombre de dossiers pour une agence. */
    getAgencyDossiers(agency) {
      if (!agency) return null;
      const v = agency.totals?.dossiers ?? agency.totals?.nbreDossiers ?? agency.NBRE_DOSSIERS ?? agency.nbre_dossiers;
      if (v != null && v !== '') return Math.max(0, parseInt(this.toSingleNumber(v), 10));
      return null;
    },
    /** Provisions pour une agence. */
    getAgencyProvisions(agency) {
      if (!agency) return null;
      const v = agency.totals?.provisions ?? agency.PROVISIONS ?? agency.provisions;
      if (v != null && v !== '') return this.toSingleNumber(v);
      return null;
    },
    /** Pourcentage pour la barre horizontale (max > 0). */
    getBarPercent(value, max) {
      if (value == null || !max || max <= 0) return 0;
      return Math.min(100, (this.toSingleNumber(value) / max) * 100);
    },
    formatPercentValue(value) {
      if (value === null || value === undefined || value === '-') return '0,00%';
      const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
      const percentValue = numValue > 100 ? numValue / 1000 : numValue;
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
        useGrouping: true
      }).format(percentValue) + '%';
    },
    formatVariation(value) {
      if (value === null || value === undefined || value === '-') return '0,00';
      const percentValue = typeof value === 'number' ? value : parseFloat(value) || 0;
      const sign = percentValue > 0 ? '+' : '';
      return sign + new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(percentValue);
    },
    calculatePercent(m1, m) {
      if (!m1 || m1 === 0 || m1 === null || m1 === undefined) return 0;
      if (m === null || m === undefined) return 0;
      const ecart = m - m1;
      return (ecart / m1) * 100;
    },
    getVariationClass(value) {
      if (value === null || value === undefined || value === '-' || value === 0) return '';
      return value > 0 ? 'variation-red' : 'variation-green';
    },
    /** Icône statut pour les cellules PAR (vert = bon, orange = attention, rouge = critique) */
    getRecapIndicatorClass(value, key) {
      if (value == null || value === '') return 'recap-indicator neutral';
      const num = this.toSingleNumber(value);
      if (key && key.startsWith('par')) {
        if (num <= 5) return 'recap-indicator green';
        if (num <= 15) return 'recap-indicator orange';
        return 'recap-indicator red';
      }
      return 'recap-indicator neutral';
    },
    /** Icône pour la colonne Var : vert si baisse (négatif), rouge si hausse (positif) pour les PAR */
    getRecapVarIndicatorClass(varPercent) {
      if (varPercent == null || varPercent === '') return 'recap-indicator neutral';
      return this.toSingleNumber(varPercent) <= 0 ? 'recap-indicator green' : 'recap-indicator red';
    },
    getDateM1Label() {
      return this.getDateRefLabel();
    },
    getDateRefLabel() {
      return `${this.months[this.selectedMonthRef - 1]} ${this.selectedYearRef}`;
    },
    getDateMLabel() {
      return `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
    },
    /** Dernier jour du mois au format DD/MM/YYYY pour les en-têtes RECAP */
    getRecapDateLabel(month, year) {
      if (!month || !year) return '–';
      const lastDay = new Date(year, month, 0).getDate();
      const d = String(lastDay).padStart(2, '0');
      const m = String(month).padStart(2, '0');
      return `${d}/${m}/${year}`;
    },
    /** Format court pour PAR AGENCE : "31-déc", "24-févr" (jour + mois abrégé) */
    getParAgenceDateShort(month, year) {
      if (!month || !year) return '–';
      const lastDay = new Date(year, month, 0).getDate();
      const abbr = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc'];
      const m = abbr[month - 1] || '';
      return `${lastDay}-${m}`;
    },
    formatNumber(value) {
      if (value === null || value === undefined) return '0';
      const n = this.toSingleNumber(value);
      return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n);
    },
    formatCurrency(value) {
      if (value === null || value === undefined) return '0';
      const n = this.toSingleNumber(value);
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(n);
    },
    formatDate(value) {
      if (value == null || value === '') return '–';
      try {
        const d = typeof value === 'string' ? new Date(value) : value;
        if (Number.isNaN(d.getTime())) return String(value);
        return new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(d);
      } catch (_) {
        return String(value);
      }
    },
    formatPercent(value) {
      const numValue = this.toSingleNumber(value);
      if (value === null || value === undefined || value === '') return '–';
      if (Number.isNaN(numValue)) return '–';
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(numValue) + '%';
    },
    getParIndicatorClass(value) {
      const numValue = this.toSingleNumber(value);
      if (value === null || value === undefined || value === '') return 'par-indicator neutral';
      return numValue > 5 ? 'par-indicator red' : 'par-indicator green';
    },
    getCafRowKey(item, index) {
      return item.agence && item.nom ? `${item.agence}|${item.nom}|${index}` : `caf-${index}`;
    },
    /** Valeur PAR pour une colonne CAF (gère par0, par_0, par30, par_30, etc.) */
    getCafPar(item, key) {
      if (!item || !key) return 0;
      const k = key.replace(/([a-zA-Z]+)(\d+)/, '$1_$2'); // par30 -> par_30
      const kUpper = (key.includes('_') ? key : k).toUpperCase(); // PAR_30
      const v = item[key] ?? item[k] ?? item[kUpper];
      return this.toSingleNumber(v);
    },
    selectAgency(agency) {
      this.selectedAgency = agency;
      this.fetchCafData(agency);
    },
    isAllAgencies(agency) {
      return !agency || agency === this.allAgenciesKey;
    },
    toSingleNumber(v) {
      if (v == null || v === '') return 0;
      if (Array.isArray(v)) return (v.length > 0 ? Number(v[0]) : 0) || 0;
      const n = Number(v);
      return Number.isNaN(n) ? 0 : n;
    },
    normalizeCafItem(item) {
      const enc = this.toSingleNumber(item.encoursCredit ?? item.encours_credit) || 0;
      const pctFromMontant = (m) => (enc > 0 ? (this.toSingleNumber(m) / enc) * 100 : 0);
      const out = {
        nom: String(typeof item.nom === 'string' ? item.nom : (item.CHARGE_AFFAIRE ?? item.charge_affaire ?? '-')).trim(),
        nbreDossiers: Math.max(0, parseInt(this.toSingleNumber(item.nbreDossiers ?? item.nbre_dossiers), 10) || 0),
        encoursCredit: enc,
        par0: this.toSingleNumber(item.par0 ?? item.par_0 ?? (item.par0_montant != null ? pctFromMontant(item.par0_montant) : undefined)) || 0,
        par30: this.toSingleNumber(item.par30 ?? item.par_30 ?? (item.par30_montant != null ? pctFromMontant(item.par30_montant) : undefined)) || 0,
        par90: this.toSingleNumber(item.par90 ?? item.par_90 ?? (item.par90_montant != null ? pctFromMontant(item.par90_montant) : undefined)) || 0,
        par180: this.toSingleNumber(item.par180 ?? item.par_180 ?? (item.par180_montant != null ? pctFromMontant(item.par180_montant) : undefined)) || 0,
        par360: this.toSingleNumber(item.par360 ?? item.par_360 ?? (item.par360_montant != null ? pctFromMontant(item.par360_montant) : undefined)) || 0
      };
      if (item.encoursImpayes != null) out.encoursImpayes = this.toSingleNumber(item.encoursImpayes);
      if (item.ratioEncoursImpayes != null) out.ratioEncoursImpayes = this.toSingleNumber(item.ratioEncoursImpayes);
      if (item.ratioNbreImpayes != null) out.ratioNbreImpayes = this.toSingleNumber(item.ratioNbreImpayes);
      if (item.agence != null) out.agence = item.agence;
      // Encours par palier PAR (montants) : support camelCase (API), snake_case ou champs bruts PAR_*_M.
      const p0m = item.encoursPar0 ?? item.encours_par0 ?? item.PAR_0_M ?? item.par_0_m;
      const p30m = item.encoursPar30 ?? item.encours_par30 ?? item.PAR_30_M ?? item.par_30_m;
      const p90m = item.encoursPar90 ?? item.encours_par90 ?? item.PAR_90_M ?? item.par_90_m;
      const p180m = item.encoursPar180 ?? item.encours_par180 ?? item.PAR_180_M ?? item.par_180_m;
      const p360m = item.encoursPar360 ?? item.encours_par360 ?? item.PAR_360_M ?? item.par_360_m;
      if (p0m != null) out.encoursPar0 = this.toSingleNumber(p0m);
      if (p30m != null) out.encoursPar30 = this.toSingleNumber(p30m);
      if (p90m != null) out.encoursPar90 = this.toSingleNumber(p90m);
      if (p180m != null) out.encoursPar180 = this.toSingleNumber(p180m);
      if (p360m != null) out.encoursPar360 = this.toSingleNumber(p360m);
      return out;
    },
    /** Clé de regroupement CAF : normalisée (minuscules, espaces réduits) pour fusionner les doublons. */
    cafMergeKey(nom) {
      return (String(nom || '').trim() || '-').toLowerCase().replace(/\s+/g, ' ');
    },
    /** Fusionne les lignes CAF ayant le même nom (une seule ligne par CAF, PAR en moyenne pondérée par l'encours). Les par0/par30/... sont déjà en % (0-100), donc moyenne pondérée = (sum(par_i * enc_i) / totalEnc), sans multiplier par 100. */
    mergeCafRowsByName(items) {
      if (!Array.isArray(items) || items.length === 0) return items;
      const byKey = {};
      items.forEach((it) => {
        const nom = (it.nom || '-').trim() || '-';
        const key = this.cafMergeKey(nom);
        if (!byKey[key]) {
          byKey[key] = { nom, nbreDossiers: 0, encoursCredit: 0, encoursImpayesSum: 0, ratioNbreImpayesWeighted: 0, encoursPar0Sum: 0, encoursPar30Sum: 0, encoursPar90Sum: 0, encoursPar180Sum: 0, encoursPar360Sum: 0, par0Sum: 0, par30Sum: 0, par90Sum: 0, par180Sum: 0, par360Sum: 0 };
        }
        const r = byKey[key];
        const enc = Number(it.encoursCredit) || 0;
        r.nbreDossiers += Number(it.nbreDossiers) || 0;
        r.encoursCredit += enc;
        r.encoursImpayesSum += Number(it.encoursImpayes) || 0;
        r.encoursPar0Sum += Number(it.encoursPar0) || 0;
        r.encoursPar30Sum += Number(it.encoursPar30) || 0;
        r.encoursPar90Sum += Number(it.encoursPar90) || 0;
        r.encoursPar180Sum += Number(it.encoursPar180) || 0;
        r.encoursPar360Sum += Number(it.encoursPar360) || 0;
        const ratioNb = this.toSingleNumber(it.ratioNbreImpayes);
        if (enc > 0 && ratioNb != null && !Number.isNaN(ratioNb)) r.ratioNbreImpayesWeighted += ratioNb * enc;
        r.par0Sum += (this.toSingleNumber(it.par0) || 0) * enc;
        r.par30Sum += (this.toSingleNumber(it.par30) || 0) * enc;
        r.par90Sum += (this.toSingleNumber(it.par90) || 0) * enc;
        r.par180Sum += (this.toSingleNumber(it.par180) || 0) * enc;
        r.par360Sum += (this.toSingleNumber(it.par360) || 0) * enc;
      });
      return Object.values(byKey).map((r) => {
        const enc = r.encoursCredit || 0;
        const pct = (x) => (enc > 0 ? Math.round((x / enc) * 100) / 100 : 0);
        const ratioEncoursImpayes = enc > 0 && r.encoursImpayesSum != null ? Math.round((r.encoursImpayesSum / enc) * 10000) / 100 : null;
        const ratioNbreImpayes = enc > 0 && r.ratioNbreImpayesWeighted != null ? Math.round((r.ratioNbreImpayesWeighted / enc) * 100) / 100 : null;
        return {
          nom: r.nom,
          nbreDossiers: r.nbreDossiers,
          encoursCredit: r.encoursCredit,
          encoursPar0: r.encoursPar0Sum,
          encoursPar30: r.encoursPar30Sum,
          encoursPar90: r.encoursPar90Sum,
          encoursPar180: r.encoursPar180Sum,
          encoursPar360: r.encoursPar360Sum,
          encoursImpayes: r.encoursImpayesSum,
          ratioEncoursImpayes,
          ratioNbreImpayes,
          par0: pct(r.par0Sum),
          par30: pct(r.par30Sum),
          par90: pct(r.par90Sum),
          par180: pct(r.par180Sum),
          par360: pct(r.par360Sum)
        };
      });
    },
    aggregateRawParToCaf(rawRows, agency) {
      const agencyNorm = (agency || '').toUpperCase().trim().split(/\s+/).pop() || '';
      const match = (row) => {
        const a = (row.AGENCE || row.agence || '').toUpperCase().trim();
        if (!a) return false;
        const tokens = a.split(/\s+/);
        const last = tokens[tokens.length - 1] || '';
        return a.includes(agencyNorm) || agencyNorm.includes(last) || last === agencyNorm;
      };
      const filtered = rawRows.filter(match);
      const byCaf = {};
      filtered.forEach((row) => {
        const nom = row.CHARGE_AFFAIRE || row.charge_affaire || '-';
        if (!byCaf[nom]) {
          byCaf[nom] = { nbreDossiers: 0, encoursCredit: 0, par0M: 0, par30M: 0, par90M: 0, par180M: 0, par360M: 0 };
        }
        const r = byCaf[nom];
        r.nbreDossiers += 1;
        const num = (key) => Number(row[key] ?? row[key.toLowerCase?.()]) || 0;
        const p0 = num('PAR_0_M');
        const p30 = num('PAR_30_M');
        const p90 = num('PAR_90_M');
        const p180 = num('PAR_180_M');
        const p360 = num('PAR_360_M');
        const enc = p0 + p30 + p90 + p180 + p360;
        r.encoursCredit += enc;
        r.par0M += p0;
        r.par30M += p30;
        r.par90M += p90;
        r.par180M += p180;
        r.par360M += p360;
      });
      return Object.entries(byCaf).map(([nom, r]) => {
        const enc = r.encoursCredit || 0;
        const pct = (x) => (enc > 0 ? Math.round((x / enc) * 100 * 100) / 100 : 0);
        return {
          nom,
          nbreDossiers: r.nbreDossiers,
          encoursCredit: r.encoursCredit,
          par0: pct(r.par0M),
          par30: pct(r.par30M),
          par90: pct(r.par90M),
          par180: pct(r.par180M),
          par360: pct(r.par360M)
        };
      });
    },
    async fetchCafData(agency) {
      this.cafLoading = true;
      this.errorMessage = null;
      // Toujours envoyer un paramètre agency : 'all' pour toutes les agences, sinon le nom de l'agence
      const agencyParam = (agency && agency !== this.allAgenciesKey) ? agency : 'all';

      try {
        const params = {
          agency: agencyParam,
          month: this.selectedMonth,
          year: this.selectedYear,
          month_ref: this.selectedMonthRef,
          year_ref: this.selectedYearRef,
          _t: Date.now()
        };
        const response = await axios.get('/api/oracle/data/portefeuille-risque-caf', {
          params,
          timeout: 300000
        });

        const payload = response.data || {};
        let cafList = payload.caf;
        if (!Array.isArray(cafList) && payload.data && Array.isArray(payload.data.caf)) {
          cafList = payload.data.caf;
        }
        if (!Array.isArray(cafList) && Array.isArray(payload.data)) {
          cafList = payload.data;
        }
        if (!Array.isArray(cafList) && Array.isArray(payload)) {
          cafList = payload;
        }

        if (Array.isArray(cafList) && cafList.length > 0) {
          const first = cafList[0];
          const isRawPar = first && (first.CHARGE_AFFAIRE != null || first.AGENCE != null) && first.nom == null && first.nbreDossiers == null;
          let list;
          if (isRawPar) {
            list = this.aggregateRawParToCaf(cafList, agency).map((item) => this.normalizeCafItem(item));
          } else {
            list = cafList.map((item) => this.normalizeCafItem(item));
          }
          const isAllAgencies = agencyParam === 'all';
          this.cafData = isAllAgencies ? list : this.mergeCafRowsByName(list);
        } else {
          this.cafData = [];
        }
      } catch (error) {
        console.error('Erreur lors du chargement des données CAF:', error);
        this.errorMessage = error.response?.data?.detail
          || error.response?.data?.message
          || error.response?.data?.error
          || (error.response?.status === 500 ? 'Erreur du service Python. Vérifiez les logs serveur ou la connexion Oracle.' : 'Erreur lors du chargement des données CAF.');
        this.cafData = [];
      } finally {
        this.cafLoading = false;
      }
    }
  }
}
</script>

<style scoped>
.par-global-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
  letter-spacing: -0.5px;
}

.period-selector {
  display: flex;
  gap: 24px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.period-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.period-label {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.month-select,
.year-select {
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.month-select:hover,
.year-select:hover {
  border-color: #2d6a4f;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.navigation-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  background: white;
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.nav-tab {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  letter-spacing: 0.5px;
}

.nav-tab:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.nav-tab.active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transform: translateY(-1px);
}

/* Entrées PAR : vert foncé → vert clair → jaune → orange → rouge */
.entrees-par0-tab {
  background: linear-gradient(135deg, #15803d 0%, #166534 100%);
  color: white;
}
.entrees-par0-tab.active {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.3);
}
.entrees-par30-tab {
  background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
  color: #14532d;
}
.entrees-par30-tab.active {
  background: linear-gradient(135deg, #86efac 0%, #4ade80 100%);
  box-shadow: 0 0 0 2px rgba(74, 222, 128, 0.4);
}
.entrees-par90-tab {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
  color: #422006;
}
.entrees-par90-tab.active {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  box-shadow: 0 0 0 2px rgba(250, 204, 21, 0.4);
}
.entrees-par180-tab {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: white;
}
.entrees-par180-tab.active {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.3);
}
.entrees-par360-tab {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  color: white;
}
.entrees-par360-tab.active {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3);
}

.par-agence-tab {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.par-agence-tab.active {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.par-caf-tab {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  position: relative;
}

.par-caf-tab.active {
  background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%);
  box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.3);
}

.par-caf-tab.active::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  right: 0;
  height: 3px;
  background: #10b981;
  border-radius: 2px;
}

.flop-30-tab {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.flop-30-tab.active {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3);
}

.top-50-tab {
  background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
}

.top-50-tab.active {
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  box-shadow: 0 0 0 2px rgba(30, 64, 175, 0.3);
}

.global-result-section {
  margin-bottom: 20px;
}

.loading-message {
  background: #f0f9ff;
  border: 1px solid #0ea5e9;
  border-radius: 6px;
  padding: 12px 16px;
  color: #0369a1;
  font-size: 14px;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #ef4444;
  border-radius: 6px;
  padding: 12px 16px;
  color: #dc2626;
  font-size: 14px;
}

/* Page RECAP – tableau indicateurs */
/* Page Entrées PAR */
.entrees-par-page-container {
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
.entrees-par-header {
  padding: 20px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.entrees-par-title {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}
.entrees-par-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}
.entrees-par-content {
  padding: 24px;
}
.entrees-par-placeholder {
  margin: 0;
  color: #64748b;
  font-size: 14px;
}
.entrees-par-error {
  color: #b91c1c;
  margin: 0 0 12px 0;
  font-size: 14px;
}
.entrees-par-loading {
  padding: 24px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}
.entrees-par-table-wrapper {
  overflow-x: auto;
  max-height: 65vh;
  overflow-y: auto;
}
.entrees-par-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.entrees-par-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #1e293b;
  color: white;
}
.entrees-par-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid #334155;
}
.entrees-par-table td {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
}
.entrees-par-table tbody tr:nth-child(even) {
  background: #f8fafc;
}
.entrees-par-table tbody tr:hover {
  background: #f1f5f9;
}
.entrees-par-table .number-cell {
  text-align: right;
}
.entrees-par-table .entrees-par-empty {
  text-align: center;
  color: #64748b;
  padding: 24px;
}

.recap-page-container {
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.recap-table-wrapper {
  overflow-x: auto;
}

.recap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.recap-table thead tr {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}

.recap-table th {
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  color: #1e293b;
}

.recap-table .recap-col-indicateur {
  min-width: 200px;
}

.recap-table .recap-col-date {
  min-width: 140px;
  text-align: right;
}

.recap-table .recap-date-m {
  border-top: 3px solid #22c55e;
}

.recap-table .recap-col-var {
  min-width: 120px;
  text-align: right;
  background: #dc2626;
  color: white;
  font-weight: 600;
}

.recap-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.recap-table .recap-indicateur {
  font-weight: 600;
  color: #1e293b;
}

.recap-table .recap-value {
  text-align: right;
}

.recap-table .recap-value-m {
  border-left: 2px solid #e2e8f0;
}

.recap-table .recap-var {
  text-align: right;
  font-weight: 500;
}

.recap-table .recap-cell-content {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.recap-table .recap-loading {
  text-align: center;
  padding: 24px;
  color: #64748b;
}

/* Lignes colorées par indicateur PAR */
.recap-table .recap-row-par0 {
  background-color: #dcfce7;
}

.recap-table .recap-row-par30 {
  background-color: #ffedd5;
}

.recap-table .recap-row-par90 {
  background-color: #fed7aa;
}

.recap-table .recap-row-par180 {
  background-color: #fecaca;
}

.recap-table .recap-row-par360 {
  background-color: #d6d3d1;
}

/* Icônes statut (cercle vert / orange / rouge) */
.recap-indicator {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.recap-indicator.green {
  background: #22c55e;
  box-shadow: 0 0 0 1px rgba(34, 197, 94, 0.3);
}

.recap-indicator.orange {
  background: #f97316;
  box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.3);
}

.recap-indicator.red {
  background: #dc2626;
  box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.3);
}

.recap-indicator.neutral {
  background: #94a3b8;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.par-global-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  min-width: 1600px;
}

/* Colonnes ENCOURS, DOSSIERS, Provisions (tableau PAR AGENCE) */
.par-agence-table .par-agence-col-encours,
.par-agence-table .par-agence-col-dossiers,
.par-agence-table .par-agence-col-provisions {
  background: #1e293b !important;
  color: #fff;
  font-weight: 600;
  min-width: 140px;
  text-align: right;
  padding-right: 14px;
}

.par-agence-table .par-agence-encours,
.par-agence-table .par-agence-dossiers,
.par-agence-table .par-agence-provisions {
  min-width: 140px;
  text-align: right;
  padding: 10px 14px;
}

.par-agence-bar-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
  min-height: 24px;
}

.par-agence-value {
  min-width: 100px;
  font-variant-numeric: tabular-nums;
}

.par-agence-bar {
  height: 12px;
  min-width: 4px;
  border-radius: 4px;
  max-width: 120px;
}

.par-agence-bar-encours {
  background: linear-gradient(90deg, #fb923c 0%, #f97316 100%);
}

.par-agence-bar-dossiers {
  background: linear-gradient(90deg, #f87171 0%, #dc2626 100%);
}

.par-agence-bar-provisions {
  background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%);
}

.par-agence-table .par-agence-cell-content {
  margin-right: 6px;
}

.par-agence-table tbody tr:not(.total-row):nth-child(odd) {
  background-color: #f0f9ff;
}

.par-agence-table tbody tr:not(.total-row):nth-child(even) {
  background-color: #fff;
}

.par-agence-table tbody tr.total-row {
  border-top: 2px solid #1e293b;
  background-color: #f1f5f9;
  font-weight: 600;
}

.par-agence-table tbody tr.par-agence-row-empty td {
  color: #9ca3af;
}

.par-global-table thead {
  position: sticky;
  top: 0;
  z-index: 10;
}

.par-global-table thead tr:first-child th {
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.par-global-table th {
  padding: 16px 12px;
  text-align: center;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
  white-space: nowrap;
  text-transform: uppercase;
  color: white;
}

.par-global-table th:last-child {
  border-right: none;
}

/* Code couleur pour les en-têtes PAR */
.par-header.par-0 {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

.par-header.par-30 {
  background: linear-gradient(135deg, #86efac 0%, #4ade80 100%);
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

.par-header.par-90 {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

.par-header.par-180 {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

.par-header.par-360 {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

.par-sub-header.par-0 {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.par-sub-header.par-30 {
  background: linear-gradient(135deg, #86efac 0%, #4ade80 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.par-sub-header.par-90 {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.par-sub-header.par-180 {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.par-sub-header.par-360 {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.territory-col {
  text-align: left;
  padding-left: 20px;
  background: #292828 !important;
  color: #ffffff !important;
  border-right: 2px solid #e5e7eb;
}

.agency-col {
  text-align: left;
  padding-left: 20px;
}

.par-global-table tbody tr {
  transition: all 0.2s ease;
}

.par-global-table td {
  padding: 14px 12px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #f3f4f6;
  border-right: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.par-global-table td:last-child {
  border-right: none;
}

.territory-cell {
  text-align: left;
  padding-left: 20px;
}

.agency-cell {
  text-align: left;
  padding-left: 56px;
}

.territory-row {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: white;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.territory-row:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

.agency-row {
  background: #f8fafc;
  font-weight: 500;
  border-left: 4px solid #3b82f6;
  transition: all 0.2s ease;
}

.agency-row:hover {
  background: #e0e7ff;
  border-left-color: #2563eb;
}

.total-row {
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
  color: white;
  font-weight: 700;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.total-row td {
  border-top: 3px solid rgba(255, 255, 255, 0.3);
  border-bottom: none;
  padding: 16px 12px;
  font-size: 14px;
}

.total-label {
  text-align: left;
  padding-left: 20px;
}

.expand-btn {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  flex-shrink: 0;
  transition: all 0.2s ease;
  margin-right: 10px;
  vertical-align: middle;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.variation-red {
  color: #dc2626 !important;
  font-weight: 700;
  font-size: 13px;
}

.territory-row .variation-red {
  color: #ef4444 !important;
}

.variation-green {
  color: #10b981 !important;
  font-weight: 700;
  font-size: 13px;
  position: relative;
}

.variation-green::before {
  content: '☑';
  margin-right: 4px;
  color: #10b981;
}

.no-data-row {
  background: #f9fafb;
  color: #6b7280;
  font-style: italic;
}

/* Amélioration de la séparation visuelle entre les groupes PAR */
.par-global-table th[colspan="3"] {
  border-right: 2px solid rgba(255, 255, 255, 0.3);
}

/* Media Queries pour le responsive */
@media (max-width: 1200px) {
  .par-global-table {
    min-width: 1400px;
    font-size: 12px;
  }
  
  .par-global-table th {
    padding: 12px 8px;
    font-size: 11px;
  }
  
  .par-global-table td {
    padding: 10px 8px;
    font-size: 11px;
  }
}

@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
    padding: 15px;
  }
  
  .section-title {
    font-size: 20px;
    width: 100%;
  }
  
  .period-selector {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .month-select,
  .year-select {
    flex: 1;
    min-width: 120px;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .par-global-table {
    min-width: 1200px;
    font-size: 11px;
  }
}

/* Styles pour PAR | CAF */
.par-caf-container {
  margin-top: 20px;
}

.par-caf-content {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.par-caf-table-container {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.caf-header {
  padding: 15px 20px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.caf-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
  cursor: pointer;
}

.dropdown-icon {
  font-size: 12px;
  color: #6b7280;
}

.table-wrapper {
  overflow-x: auto;
  max-height: 600px;
  overflow-y: auto;
}

.par-caf-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.par-caf-table thead {
  position: sticky;
  top: 0;
  z-index: 10;
  background: white;
}

.par-caf-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 700;
  font-size: 13px;
  text-transform: uppercase;
  color: #1f2937;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
}

.par-caf-table .agency-col {
  min-width: 160px;
  font-weight: 700;
}

.par-caf-table .name-col {
  min-width: 200px;
}

.par-caf-table .number-col {
  text-align: right;
  min-width: 120px;
}

.par-caf-table .amount-col {
  text-align: right;
  min-width: 150px;
}

.par-caf-table .par-col {
  text-align: center;
  min-width: 100px;
  width: 100px;
}

.par-0-header {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  color: white;
}

.par-30-header {
  background: linear-gradient(135deg, #86efac 0%, #4ade80 100%);
  color: white;
}

.par-90-header {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
  color: white;
}

.par-180-header {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: white;
}

.par-360-header {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.par-caf-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.par-caf-table tbody tr:hover {
  background-color: #f9fafb;
}

.par-caf-table tbody tr.caf-row-alt {
  background-color: #f9fafb;
}

.par-caf-table tbody tr.caf-row-empty td {
  color: #9ca3af;
}

.par-caf-table td {
  padding: 12px 16px;
  font-size: 13px;
}

.caf-empty-state {
  text-align: center;
  padding: 28px 20px !important;
  color: #4b5563;
  vertical-align: middle;
}

.caf-empty-message {
  margin: 0 0 8px 0;
  font-weight: 600;
  color: #374151;
}

.caf-empty-hint {
  margin: 0 0 16px 0;
  font-size: 12px;
  color: #6b7280;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}

.caf-retry-btn {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.caf-retry-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.caf-retry-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Page FLOP 30 */
.flop-30-container {
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.flop-30-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-bottom: 2px solid #fecaca;
}

.flop-30-title {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 700;
  color: #991b1b;
}

.flop-30-subtitle {
  margin: 0;
  font-size: 13px;
  color: #b91c1c;
}

.flop-30-table-wrapper {
  overflow-x: auto;
  max-height: 70vh;
  overflow-y: auto;
}

.flop-30-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.flop-30-table thead {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #1f2937;
  color: white;
}

.flop-30-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid #374151;
}

.flop-30-table .flop-rang { width: 60px; text-align: center; }
.flop-30-table .flop-caf { min-width: 180px; }
.flop-30-table .flop-num { min-width: 100px; text-align: right; }
.flop-30-table .flop-amount { min-width: 120px; text-align: right; }
.flop-30-table .flop-pct { min-width: 100px; text-align: right; }
.flop-30-table .flop-par { min-width: 90px; text-align: center; }
.flop-30-table thead .par-0-header { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: #fff; }
.flop-30-table thead .par-30-header { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: #fff; }
.flop-30-table thead .par-90-header { background: linear-gradient(135deg, #facc15 0%, #eab308 100%); color: #1f2937; }
.flop-30-table thead .par-180-header { background: linear-gradient(135deg, #fb923c 0%, #f97316 100%); color: #fff; }
.flop-30-table thead .par-360-header { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: #fff; }

.flop-30-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.15s ease;
}

.flop-30-table tbody tr:hover {
  background-color: #f9fafb;
}

.flop-30-table tbody td {
  padding: 10px 14px;
  border: 1px solid #f3f4f6;
}

.flop-30-table tbody tr.flop-row-alt {
  background-color: #f9fafb;
}

.flop-30-table tbody tr.flop-row-empty td {
  color: #9ca3af;
}

.flop-30-table .flop-loading,
.flop-30-table .flop-empty {
  text-align: center;
  padding: 24px;
  color: #6b7280;
}

.flop-30-table .par-value {
  margin-right: 6px;
}

/* Page TOP 50 */
.top-50-container {
  margin-top: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.top-50-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-bottom: 2px solid #bbf7d0;
}

.top-50-title {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 700;
  color: #166534;
}

.top-50-subtitle {
  margin: 0;
  font-size: 13px;
  color: #15803d;
}

.top-50-table-wrapper {
  overflow-x: auto;
  max-height: 70vh;
  overflow-y: auto;
}

.top-50-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.top-50-table thead {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #14532d;
  color: white;
}

.top-50-table th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid #166534;
}

.top-50-table .top-rang { width: 60px; text-align: center; }
.top-50-table .top-caf { min-width: 200px; }
.top-50-table .top-num { min-width: 100px; text-align: right; }
.top-50-table .top-amount { min-width: 130px; text-align: right; }
.top-50-table .top-par { min-width: 90px; text-align: center; }

.top-50-table tbody tr {
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.15s ease;
}

.top-50-table tbody tr:hover {
  background-color: #f9fafb;
}

.top-50-table tbody tr.top-row-alt {
  background-color: #f9fafb;
}

.top-50-table tbody tr.top-row-alt:hover {
  background-color: #f3f4f6;
}

.top-50-table tbody td {
  padding: 10px 14px;
  border: 1px solid #f3f4f6;
}

.top-50-table tbody tr.top-row-empty td {
  color: #9ca3af;
}

.top-50-table .top-loading,
.top-50-table .top-empty {
  text-align: center;
  padding: 24px;
  color: #6b7280;
}

.top-50-table .par-value {
  margin-right: 6px;
}

.agency-cell {
  font-size: 12px;
  color: #4b5563;
  font-weight: 500;
}

.name-cell {
  font-weight: 500;
  color: #1f2937;
}

.number-cell {
  text-align: right;
  color: #374151;
}

.amount-cell {
  text-align: right;
  color: #374151;
  font-weight: 500;
}

.par-cell {
  text-align: center;
  vertical-align: middle;
  white-space: nowrap;
  min-width: 5rem;
}

.par-cell .par-value {
  margin-right: 6px;
}

.par-value {
  font-weight: 500;
  color: #1f2937;
  display: inline-block;
}

.par-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.par-indicator.green {
  background-color: #10b981;
}

.par-indicator.red {
  background-color: #ef4444;
}

.par-indicator.neutral {
  background-color: #9ca3af;
}

/* Panneau de sélection d'agence */
.agency-panel {
  width: 320px;
  background: white;
  border-radius: 12px;
  border: 4px solid #8b1a1a;
  padding: 0;
  max-height: 700px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.agency-panel-banner {
  background: white;
  border: 3px solid #8b1a1a;
  border-radius: 8px;
  padding: 12px 20px;
  margin: 15px;
  text-align: center;
}

.agency-panel-title {
  font-size: 16px;
  font-weight: 700;
  font-style: italic;
  color: #8b1a1a;
  margin: 0;
  text-align: center;
}

.agency-panel-content {
  background: white;
  border: 3px solid #fdba74;
  border-radius: 8px;
  margin: 0 15px 15px 15px;
  padding: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.agency-header {
  background: #fdba74;
  padding: 10px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #fb923c;
}

.agency-header-label {
  font-size: 14px;
  font-weight: 700;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.agency-header-icons {
  display: flex;
  gap: 10px;
  align-items: center;
}

.agency-icon {
  font-size: 16px;
  cursor: pointer;
  color: #1f2937;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.checklist-icon {
  font-size: 18px;
}

.filter-icon {
  font-size: 14px;
  color: #dc2626;
}

.agency-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 8px;
  gap: 4px;
}

.agency-button {
  width: 100%;
  padding: 10px 12px;
  background: #fdba74;
  border: 1px solid white;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #000;
  text-align: left;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agency-button:hover {
  background: #fb923c;
  border-color: #f97316;
}

.agency-button.active {
  background: #fb923c;
  border-color: #f97316;
  font-weight: 700;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
