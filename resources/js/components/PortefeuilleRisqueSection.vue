<template>
  <div class="collection-section">
    <div class="section-header">
      <h2 class="section-title">Evolution du Portefeuille à risque % - {{ getPeriodTitle() }}</h2>
      <div class="period-selector">
        <select v-model="selectedPeriod" class="period-select" @change="refreshPortefeuilleData">
          <option value="week">Semaine</option>
          <option value="month">Mois</option>
          <option value="year">Année</option>
        </select>
        <template v-if="selectedPeriod === 'week'">
          <input
            type="date"
            v-model="selectedDate"
            class="date-select"
            @change="refreshPortefeuilleData"
          />
        </template>
        <template v-if="selectedPeriod === 'month'">
          <select v-model="selectedMonth" class="month-select" @change="refreshPortefeuilleData">
            <option v-for="(month, index) in months" :key="'m-' + index" :value="index + 1">
              {{ month }}
            </option>
          </select>
          <select v-model="selectedYear" class="year-select" @change="refreshPortefeuilleData">
            <option v-for="year in years" :key="'y-' + year" :value="year">
              {{ year }}
            </option>
          </select>
        </template>
        <template v-if="selectedPeriod === 'year'">
          <select v-model="selectedYear" class="year-select" @change="refreshPortefeuilleData">
            <option v-for="year in years" :key="'ya-' + year" :value="year">
              {{ year }}
            </option>
          </select>
        </template>
      </div>
    </div>
    
    <!-- Menu d'onglets pour basculer entre PAR 0-30, PAR 90-360 et Stock -->
    <div class="tabs-menu">
      <button 
        :class="['tab-button', { active: selectedView === 'par' && selectedParView === '0-30' }]"
        @click="selectedView = 'par'; selectedParView = '0-30'"
      >
        PAR 0 à 30
      </button>
      <button 
        :class="['tab-button', { active: selectedView === 'par' && selectedParView === '90-360' }]"
        @click="selectedView = 'par'; selectedParView = '90-360'"
      >
        PAR 90 à 360
      </button>
      <button 
        :class="['tab-button', { active: selectedView === 'stock' }]"
        @click="handleStockClick"
      >
        Stock
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

    <!-- Tableau Stock -->
    <div v-if="selectedView === 'stock'" class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table stock-table">
          <thead>
            <tr>
              <th style="text-align: left;">BRANCH_NAME</th>
              <th style="text-align: right;">STOCK_PROVISION</th>
              <th style="text-align: right;">PROVISION_COMPTABILISEE</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr class="no-data-row">
                <td colspan="3" style="text-align: center; padding: 20px;">
                  🔄 Chargement des données...
                </td>
              </tr>
              <!-- Afficher la structure même pendant le chargement -->
              <tr class="level-1-row">
                <td class="level-1">
                  <button class="expand-btn">+</button>
                  <strong>TERRITOIRE</strong>
                </td>
                <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
                <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
              </tr>
              <tr class="total-row">
                <td style="text-align: left;"><strong>TOTAL</strong></td>
                <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
                <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
              </tr>
            </template>
            <template v-else>
              <!-- Structure hiérarchique par territoire -->
              <template v-if="stockData && stockData.TERRITOIRE && Object.keys(stockData.TERRITOIRE).length > 0">
                <!-- TERRITOIRE -->
                <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
                  <td class="level-1">
                    <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                      {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                    </button>
                    <strong>TERRITOIRE</strong>
                  </td>
                  <td style="text-align: right;"><strong>{{ formatRawValue(stockTotal.stockProvision) }}</strong></td>
                  <td style="text-align: right;"><strong>{{ formatRawValue(stockTotal.provisionComptabilisee) }}</strong></td>
                </tr>
                <!-- Territoires -->
                <template v-if="expandedSections.TERRITOIRE">
                  <template v-for="(territory, territoryKey) in stockData.TERRITOIRE" :key="territoryKey">
                    <tr class="level-2-row" @click="expandedStockTerritories[territoryKey] = !expandedStockTerritories[territoryKey]">
                      <td class="level-2">
                        <button class="expand-btn" @click.stop="expandedStockTerritories[territoryKey] = !expandedStockTerritories[territoryKey]">
                          {{ expandedStockTerritories[territoryKey] ? '−' : '+' }}
                        </button>
                        <strong>{{ territory.name }}</strong>
                      </td>
                      <td style="text-align: right;"><strong>{{ formatRawValue(territory.totals.stockProvision || 0) }}</strong></td>
                      <td style="text-align: right;"><strong>{{ formatRawValue(territory.totals.provisionComptabilisee || 0) }}</strong></td>
                    </tr>
                    <!-- Agences du territoire -->
                    <template v-if="expandedStockTerritories[territoryKey]">
                      <tr v-for="(agency, index) in territory.agencies" :key="`${territoryKey}-${index}`" class="level-3-row">
                        <td style="text-align: left;">{{ agency.BRANCH_NAME || agency.branch_name || '-' }}</td>
                        <td style="text-align: right;">{{ formatRawValue(agency.STOCK_PROVISION || agency.stock_provision || 0) }}</td>
                        <td style="text-align: right;">{{ formatRawValue(agency.PROVISION_COMPTABILISEE || agency.provision_comptabilisee || 0) }}</td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
              <!-- Fallback: Structure plate -->
              <template v-else-if="stockDataFlat && stockDataFlat.length > 0">
                <tr v-for="(row, index) in stockDataFlat" :key="index" class="level-3-row">
                  <td style="text-align: left;">{{ row.BRANCH_NAME || row.branch_name || '-' }}</td>
                  <td style="text-align: right;">{{ formatRawValue(row.STOCK_PROVISION || row.stock_provision || 0) }}</td>
                  <td style="text-align: right;">{{ formatRawValue(row.PROVISION_COMPTABILISEE || row.provision_comptabilisee || 0) }}</td>
                </tr>
              </template>
              <!-- Affichage même sans données -->
              <template v-else>
                <!-- TERRITOIRE -->
                <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
                  <td class="level-1">
                    <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                      {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                    </button>
                    <strong>TERRITOIRE</strong>
                  </td>
                  <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
                  <td style="text-align: right;"><strong>{{ formatRawValue(0) }}</strong></td>
                </tr>
              </template>
              <!-- Ligne TOTAL -->
              <tr class="total-row">
                <td style="text-align: left;"><strong>TOTAL</strong></td>
                <td style="text-align: right;"><strong>{{ formatRawValue(stockTotal.stockProvision) }}</strong></td>
                <td style="text-align: right;"><strong>{{ formatRawValue(stockTotal.provisionComptabilisee) }}</strong></td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tableau PAR -->
    <div v-if="selectedView === 'par'" class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th rowspan="2" class="agency-col">AGENCE</th>
              <!-- Vue PAR 0-30 -->
              <template v-if="selectedParView === '0-30'">
                <th colspan="4">PAR 0</th>
                <th colspan="4">PAR 30</th>
              </template>
              <!-- Vue PAR 90-360 -->
              <template v-else>
                <th colspan="4">PAR 90</th>
                <th colspan="4">PAR 180</th>
                <th colspan="4">PAR 360</th>
              </template>
            </tr>
            <tr>
              <!-- Vue PAR 0-30 -->
              <template v-if="selectedParView === '0-30'">
                <!-- PAR 0 columns -->
                <th>M-1</th>
                <th>M</th>
                <th>Ecart</th>
                <th>% PTF M</th>
                <!-- PAR 30 columns -->
                <th>M-1</th>
                <th>M</th>
                <th>Ecart</th>
                <th>% PTF M</th>
              </template>
              <!-- Vue PAR 90-360 -->
              <template v-else>
                <!-- PAR 90 columns -->
                <th>M-1</th>
                <th>M</th>
                <th>Ecart</th>
                <th>% PTF M</th>
                <!-- PAR 180 columns -->
                <th>M-1</th>
                <th>M</th>
                <th>Ecart</th>
                <th>% PTF M</th>
                <!-- PAR 360 columns -->
                <th>M-1</th>
                <th>M</th>
                <th>Ecart</th>
                <th>% PTF M</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <!-- Vue PAR 0-30 -->
              <template v-if="selectedParView === '0-30'">
                <!-- PAR 0 -->
                <td><strong>{{ formatValue(territoireTotal.par0M1) }}</strong></td>
                <td><strong>{{ formatValue(territoireTotal.par0M) }}</strong></td>
                <td :class="getEcartClass(territoireTotal.par0Ecart)">
                  <strong>{{ formatEcart(territoireTotal.par0Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(territoireTotal.par0Percent) }}</strong></td>
                <!-- PAR 30 -->
                <td><strong>{{ formatValue(territoireTotal.par30M1) }}</strong></td>
                <td><strong>{{ formatValue(territoireTotal.par30M) }}</strong></td>
                <td :class="getEcartClass(territoireTotal.par30Ecart)">
                  <strong>{{ formatEcart(territoireTotal.par30Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(territoireTotal.par30Percent) }}</strong></td>
              </template>
              <!-- Vue PAR 90-360 -->
              <template v-else>
                <!-- PAR 90 -->
                <td><strong>{{ formatValue(territoireTotal.par90M1) }}</strong></td>
                <td><strong>{{ formatValue(territoireTotal.par90M) }}</strong></td>
                <td :class="getEcartClass(territoireTotal.par90Ecart)">
                  <strong>{{ formatEcart(territoireTotal.par90Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(territoireTotal.par90Percent) }}</strong></td>
                <!-- PAR 180 -->
                <td><strong>{{ formatValue(territoireTotal.par180M1) }}</strong></td>
                <td><strong>{{ formatValue(territoireTotal.par180M) }}</strong></td>
                <td :class="getEcartClass(territoireTotal.par180Ecart)">
                  <strong>{{ formatEcart(territoireTotal.par180Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(territoireTotal.par180Percent) }}</strong></td>
                <!-- PAR 360 -->
                <td><strong>{{ formatValue(territoireTotal.par360M1) }}</strong></td>
                <td><strong>{{ formatValue(territoireTotal.par360M) }}</strong></td>
                <td :class="getEcartClass(territoireTotal.par360Ecart)">
                  <strong>{{ formatEcart(territoireTotal.par360Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(territoireTotal.par360Percent) }}</strong></td>
              </template>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections.TERRITOIRE">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <tr class="level-2-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <!-- Vue PAR 0-30 -->
                  <template v-if="selectedParView === '0-30'">
                    <!-- PAR 0 -->
                    <td><strong>{{ formatValue(territory.totals?.par0M1 || 0) }}</strong></td>
                    <td><strong>{{ formatValue(territory.totals?.par0M || 0) }}</strong></td>
                    <td :class="getEcartClass(territory.totals?.par0Ecart || 0)">
                      <strong>{{ formatEcart(territory.totals?.par0Ecart || 0) }}</strong>
                    </td>
                    <td class="percent-red"><strong>{{ formatPercent(calculatePercent(territory.totals?.par0M1, territory.totals?.par0M)) }}</strong></td>
                    <!-- PAR 30 -->
                    <td><strong>{{ formatValue(territory.totals?.par30M1 || 0) }}</strong></td>
                    <td><strong>{{ formatValue(territory.totals?.par30M || 0) }}</strong></td>
                    <td :class="getEcartClass(territory.totals?.par30Ecart || 0)">
                      <strong>{{ formatEcart(territory.totals?.par30Ecart || 0) }}</strong>
                    </td>
                    <td class="percent-red"><strong>{{ formatPercent(calculatePercent(territory.totals?.par30M1, territory.totals?.par30M)) }}</strong></td>
                  </template>
                  <!-- Vue PAR 90-360 -->
                  <template v-else>
                    <!-- PAR 90 -->
                    <td><strong>{{ formatValue(territory.totals?.par90M1 || 0) }}</strong></td>
                    <td><strong>{{ formatValue(territory.totals?.par90M || 0) }}</strong></td>
                    <td :class="getEcartClass(territory.totals?.par90Ecart || 0)">
                      <strong>{{ formatEcart(territory.totals?.par90Ecart || 0) }}</strong>
                    </td>
                    <td class="percent-red"><strong>{{ formatPercent(calculatePercent(territory.totals?.par90M1, territory.totals?.par90M)) }}</strong></td>
                    <!-- PAR 180 -->
                    <td><strong>{{ formatValue(territory.totals?.par180M1 || 0) }}</strong></td>
                    <td><strong>{{ formatValue(territory.totals?.par180M || 0) }}</strong></td>
                    <td :class="getEcartClass(territory.totals?.par180Ecart || 0)">
                      <strong>{{ formatEcart(territory.totals?.par180Ecart || 0) }}</strong>
                    </td>
                    <td class="percent-red"><strong>{{ formatPercent(calculatePercent(territory.totals?.par180M1, territory.totals?.par180M)) }}</strong></td>
                    <!-- PAR 360 -->
                    <td><strong>{{ formatValue(territory.totals?.par360M1 || 0) }}</strong></td>
                    <td><strong>{{ formatValue(territory.totals?.par360M || 0) }}</strong></td>
                    <td :class="getEcartClass(territory.totals?.par360Ecart || 0)">
                      <strong>{{ formatEcart(territory.totals?.par360Ecart || 0) }}</strong>
                    </td>
                    <td class="percent-red"><strong>{{ formatPercent(calculatePercent(territory.totals?.par360M1, territory.totals?.par360M)) }}</strong></td>
                  </template>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <template v-for="(agency, index) in (territory.agencies || [])" :key="getAgencyKey(agency, index)">
                    <tr class="level-3-row">
                      <td class="level-3">
                        {{ agency.name || agency.AGENCE || getAgencyName(agency) }}
                      </td>
                      <!-- Vue PAR 0-30 -->
                      <template v-if="selectedParView === '0-30'">
                        <!-- PAR 0 -->
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_0_M_1')) }}</td>
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_0_M')) }}</td>
                        <td :class="getEcartClass(getAgencyValue(agency, 'Variation_PAR_0'))">
                          {{ formatEcart(getAgencyValue(agency, 'Variation_PAR_0')) }}
                        </td>
                        <td class="percent-red">{{ formatPercent(calculatePercent(getAgencyValue(agency, 'PAR_0_M_1'), getAgencyValue(agency, 'PAR_0_M'))) }}</td>
                        <!-- PAR 30 -->
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_30_M_1')) }}</td>
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_30_M')) }}</td>
                        <td :class="getEcartClass(getAgencyValue(agency, 'Variation_PAR_30'))">
                          {{ formatEcart(getAgencyValue(agency, 'Variation_PAR_30')) }}
                        </td>
                        <td class="percent-red">{{ formatPercent(calculatePercent(getAgencyValue(agency, 'PAR_30_M_1'), getAgencyValue(agency, 'PAR_30_M'))) }}</td>
                      </template>
                      <!-- Vue PAR 90-360 -->
                      <template v-else>
                        <!-- PAR 90 -->
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_90_M_1')) }}</td>
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_90_M')) }}</td>
                        <td :class="getEcartClass(getAgencyValue(agency, 'Variation_PAR_90'))">
                          {{ formatEcart(getAgencyValue(agency, 'Variation_PAR_90')) }}
                        </td>
                        <td class="percent-red">{{ formatPercent(calculatePercent(getAgencyValue(agency, 'PAR_90_M_1'), getAgencyValue(agency, 'PAR_90_M'))) }}</td>
                        <!-- PAR 180 -->
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_180_M_1')) }}</td>
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_180_M')) }}</td>
                        <td :class="getEcartClass(getAgencyValue(agency, 'Variation_PAR_180'))">
                          {{ formatEcart(getAgencyValue(agency, 'Variation_PAR_180')) }}
                        </td>
                        <td class="percent-red">{{ formatPercent(calculatePercent(getAgencyValue(agency, 'PAR_180_M_1'), getAgencyValue(agency, 'PAR_180_M'))) }}</td>
                        <!-- PAR 360 -->
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_360_M_1')) }}</td>
                        <td>{{ formatValue(getAgencyValue(agency, 'PAR_360_M')) }}</td>
                        <td :class="getEcartClass(getAgencyValue(agency, 'Variation_PAR_360'))">
                          {{ formatEcart(getAgencyValue(agency, 'Variation_PAR_360')) }}
                        </td>
                        <td class="percent-red">{{ formatPercent(calculatePercent(getAgencyValue(agency, 'PAR_360_M_1'), getAgencyValue(agency, 'PAR_360_M'))) }}</td>
                      </template>
                    </tr>
                  </template>
                </template>
              </template>
            </template>

            <!-- Message si aucune donnée dans les territoires -->
            <template v-if="!loading && !errorMessage && Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length === 0">
              <tr class="no-data-row">
                <td colspan="13" style="text-align: center; padding: 40px; color: #666;">
                  <p>Aucune donnée de portefeuille à risque disponible pour la période sélectionnée.</p>
                </td>
              </tr>
            </template>

            <!-- TOTAL (dernière ligne) -->
            <tr class="total-row">
              <td class="agency-name"><strong>TOTAL</strong></td>
              <!-- Vue PAR 0-30 -->
              <template v-if="selectedParView === '0-30'">
                <!-- PAR 0 -->
                <td><strong>{{ formatValue(totalGeneral.par0M1) }}</strong></td>
                <td><strong>{{ formatValue(totalGeneral.par0M) }}</strong></td>
                <td :class="getEcartClass(totalGeneral.par0Ecart)">
                  <strong>{{ formatEcart(totalGeneral.par0Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(totalGeneral.par0Percent) }}</strong></td>
                <!-- PAR 30 -->
                <td><strong>{{ formatValue(totalGeneral.par30M1) }}</strong></td>
                <td><strong>{{ formatValue(totalGeneral.par30M) }}</strong></td>
                <td :class="getEcartClass(totalGeneral.par30Ecart)">
                  <strong>{{ formatEcart(totalGeneral.par30Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(totalGeneral.par30Percent) }}</strong></td>
              </template>
              <!-- Vue PAR 90-360 -->
              <template v-else>
                <!-- PAR 90 -->
                <td><strong>{{ formatValue(totalGeneral.par90M1) }}</strong></td>
                <td><strong>{{ formatValue(totalGeneral.par90M) }}</strong></td>
                <td :class="getEcartClass(totalGeneral.par90Ecart)">
                  <strong>{{ formatEcart(totalGeneral.par90Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(totalGeneral.par90Percent) }}</strong></td>
                <!-- PAR 180 -->
                <td><strong>{{ formatValue(totalGeneral.par180M1) }}</strong></td>
                <td><strong>{{ formatValue(totalGeneral.par180M) }}</strong></td>
                <td :class="getEcartClass(totalGeneral.par180Ecart)">
                  <strong>{{ formatEcart(totalGeneral.par180Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(totalGeneral.par180Percent) }}</strong></td>
                <!-- PAR 360 -->
                <td><strong>{{ formatValue(totalGeneral.par360M1) }}</strong></td>
                <td><strong>{{ formatValue(totalGeneral.par360M) }}</strong></td>
                <td :class="getEcartClass(totalGeneral.par360Ecart)">
                  <strong>{{ formatEcart(totalGeneral.par360Ecart) }}</strong>
                </td>
                <td class="percent-red"><strong>{{ formatPercent(totalGeneral.par360Percent) }}</strong></td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'PortefeuilleRisqueSection',
  props: {
    viewType: {
      type: String,
      default: 'simple' // 'simple' ou 'global'
    }
  },
  data() {
    const now = new Date();
    const currentMonth = now.getMonth() + 1;
    const currentYear = now.getFullYear();
    const y = currentYear;
    const m = String(currentMonth).padStart(2, '0');
    const d = String(now.getDate()).padStart(2, '0');
    return {
      selectedPeriod: 'month',
      selectedDate: `${y}-${m}-${d}`,
      selectedMonth: currentMonth,
      selectedYear: currentYear,
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      loading: false,
      errorMessage: null,
      selectedView: 'par', // 'par' ou 'stock'
      selectedParView: '0-30', // '0-30' ou '90-360'
      hierarchicalDataFromBackend: {
        TERRITOIRE: {}
      },
      expandedSections: {
        TERRITOIRE: false
      },
      expandedStockTerritories: {}, // Pour gérer l'expansion des territoires dans le tableau Stock
      stockData: [], // Structure hiérarchique
      stockDataFlat: [] // Structure plate (fallback)
    };
  },
  computed: {
    years() {
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let i = currentYear - 5; i <= currentYear + 2; i++) {
        years.push(i);
      }
      return years;
    },
    snapshotMonthYear() {
      const p = this.selectedPeriod;
      if (p === 'month') {
        return { month: this.selectedMonth, year: this.selectedYear };
      }
      if (p === 'year') {
        return { month: 12, year: this.selectedYear };
      }
      if (p === 'week' && this.selectedDate) {
        const dt = new Date(`${this.selectedDate}T12:00:00`);
        if (Number.isNaN(dt.getTime())) {
          const n = new Date();
          return { month: n.getMonth() + 1, year: n.getFullYear() };
        }
        return { month: dt.getMonth() + 1, year: dt.getFullYear() };
      }
      const n = new Date();
      return { month: n.getMonth() + 1, year: n.getFullYear() };
    },
    refMonthYear() {
      const { month: m, year: y } = this.snapshotMonthYear;
      if (m === 1) return { month: 12, year: y - 1 };
      return { month: m - 1, year: y };
    },
    filteredHierarchicalData() {
      return this.hierarchicalData || {
        TERRITOIRE: {}
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
        TERRITOIRE: {}
      };
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
      
      // Calculer les pourcentages
      total.par0Percent = total.par0M1 !== 0 ? (total.par0Ecart / total.par0M1) * 100 : 0;
      total.par30Percent = total.par30M1 !== 0 ? (total.par30Ecart / total.par30M1) * 100 : 0;
      total.par90Percent = total.par90M1 !== 0 ? (total.par90Ecart / total.par90M1) * 100 : 0;
      total.par180Percent = total.par180M1 !== 0 ? (total.par180Ecart / total.par180M1) * 100 : 0;
      total.par360Percent = total.par360M1 !== 0 ? (total.par360Ecart / total.par360M1) * 100 : 0;
      
      return total;
    },
    totalGeneral() {
      const territoire = this.territoireTotal;
      
      const par0M1 = territoire.par0M1;
      const par0M = territoire.par0M;
      const par0Ecart = par0M - par0M1;
      const par0Percent = par0M1 !== 0 ? (par0Ecart / par0M1) * 100 : 0;
      
      const par30M1 = territoire.par30M1;
      const par30M = territoire.par30M;
      const par30Ecart = par30M - par30M1;
      const par30Percent = par30M1 !== 0 ? (par30Ecart / par30M1) * 100 : 0;
      
      const par90M1 = territoire.par90M1;
      const par90M = territoire.par90M;
      const par90Ecart = par90M - par90M1;
      const par90Percent = par90M1 !== 0 ? (par90Ecart / par90M1) * 100 : 0;
      
      const par180M1 = territoire.par180M1;
      const par180M = territoire.par180M;
      const par180Ecart = par180M - par180M1;
      const par180Percent = par180M1 !== 0 ? (par180Ecart / par180M1) * 100 : 0;
      
      const par360M1 = territoire.par360M1;
      const par360M = territoire.par360M;
      const par360Ecart = par360M - par360M1;
      const par360Percent = par360M1 !== 0 ? (par360Ecart / par360M1) * 100 : 0;
      
      return {
        par0M1,
        par0M,
        par0Ecart,
        par0Percent,
        par30M1,
        par30M,
        par30Ecart,
        par30Percent,
        par90M1,
        par90M,
        par90Ecart,
        par90Percent,
        par180M1,
        par180M,
        par180Ecart,
        par180Percent,
        par360M1,
        par360M,
        par360Ecart,
        par360Percent
      };
    },
    stockTotal() {
      if (this.stockData && this.stockData.TERRITOIRE) {
        let totalStockProvision = 0;
        let totalProvisionComptabilisee = 0;
        
        Object.values(this.stockData.TERRITOIRE).forEach(territory => {
          if (territory.totals) {
            totalStockProvision += parseFloat(territory.totals.stockProvision || 0);
            totalProvisionComptabilisee += parseFloat(territory.totals.provisionComptabilisee || 0);
          }
        });
        
        return {
          stockProvision: totalStockProvision,
          provisionComptabilisee: totalProvisionComptabilisee
        };
      }
      
      // Fallback: structure plate
      if (!this.stockDataFlat || this.stockDataFlat.length === 0) {
        return {
          stockProvision: 0,
          provisionComptabilisee: 0
        };
      }
      
      const total = this.stockDataFlat.reduce((acc, row) => {
        acc.stockProvision += parseFloat(row.STOCK_PROVISION || row.stock_provision || 0);
        acc.provisionComptabilisee += parseFloat(row.PROVISION_COMPTABILISEE || row.provision_comptabilisee || 0);
        return acc;
      }, { stockProvision: 0, provisionComptabilisee: 0 });
      
      return total;
    }
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        return 'Résultat de la semaine';
      }
      if (this.selectedPeriod === 'month') {
        return `Résultat Global du Mois (${this.months[this.selectedMonth - 1]} ${this.selectedYear})`;
      }
      if (this.selectedPeriod === 'year') {
        return `Résultat Global de l'Année (${this.selectedYear})`;
      }
      return 'Résultat Global';
    },
    getComparisonPeriodLabel() {
      return `${this.getDateRefLabel()} / ${this.getDateMLabel()}`;
    },
    refreshPortefeuilleData() {
      if (this.selectedView === 'par') {
        this.fetchData();
      } else if (this.selectedView === 'stock') {
        this.fetchStockData();
      }
    },
    async fetchData() {
      this.loading = true;
      this.errorMessage = null;
      
      try {
        const response = await axios.get('/api/oracle/data/portefeuille-risque', {
          params: {
            month: this.snapshotMonthYear.month,
            year: this.snapshotMonthYear.year
          }
        });
        
        if (response.data && response.data.hierarchicalData) {
          this.hierarchicalDataFromBackend = response.data.hierarchicalData;
        } else if (response.data && response.data.data) {
          this.processFlatData(response.data.data);
        } else {
          this.hierarchicalDataFromBackend = {
            TERRITOIRE: {}
          };
        }
      } catch (err) {
        console.error('Erreur lors de la récupération des données PAR:', err);
        this.errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Erreur lors de la récupération des données';
        this.hierarchicalDataFromBackend = {
          TERRITOIRE: {}
        };
      } finally {
        this.loading = false;
      }
    },
    processFlatData(data) {
      // Grouper les données par agence et créer la structure hiérarchique
      const hierarchical = {
        TERRITOIRE: {}
      };
      
      // Mapping des agences vers les territoires (à adapter selon votre structure)
      const agencyToTerritory = {
        'AGENCE CASTORS': 'territoire_dakar_ville',
        'AGENCE THIES': 'territoire_province_centre_sud',
        'AGENCE TOUBA': 'territoire_province_nord',
        'AGENCE MBOUR': 'territoire_province_centre_sud',
        'COFINA EXPRESS SAINT-LO': 'territoire_province_nord',
        'C-E RUFISQUE': 'territoire_dakar_banlieue'
      };
      
      // Grouper par agence
      const agenciesMap = {};
      
      (data || []).forEach(row => {
        const agencyName = row.AGENCE || row.agence || '-';
        const codeAgency = row.CODE_AGENCE || row.code_agence || '';
        
        if (!agenciesMap[agencyName]) {
          agenciesMap[agencyName] = {
            name: agencyName,
            code: codeAgency,
            data: [],
            totals: {
              par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
              par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
              par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0
            }
          };
        }
        
        agenciesMap[agencyName].data.push(row);
        
        // Agréger les totaux
        agenciesMap[agencyName].totals.par0M1 += parseFloat(row.PAR_0_M_1 || row.par_0_m_1 || 0);
        agenciesMap[agencyName].totals.par0M += parseFloat(row.PAR_0_M || row.par_0_m || 0);
        agenciesMap[agencyName].totals.par30M1 += parseFloat(row.PAR_30_M_1 || row.par_30_m_1 || 0);
        agenciesMap[agencyName].totals.par30M += parseFloat(row.PAR_30_M || row.par_30_m || 0);
        agenciesMap[agencyName].totals.par90M1 += parseFloat(row.PAR_90_M_1 || row.par_90_m_1 || 0);
        agenciesMap[agencyName].totals.par90M += parseFloat(row.PAR_90_M || row.par_90_m || 0);
      });
      
      // Calculer les écarts et pourcentages
      Object.values(agenciesMap).forEach(agency => {
        agency.totals.par0Ecart = agency.totals.par0M - agency.totals.par0M1;
        agency.totals.par30Ecart = agency.totals.par30M - agency.totals.par30M1;
        agency.totals.par90Ecart = agency.totals.par90M - agency.totals.par90M1;
      });
      
      // Organiser par territoire
      Object.values(agenciesMap).forEach(agency => {
        const territoryKey = agencyToTerritory[agency.name] || 'territoire_dakar_ville';
        
        if (!hierarchical.TERRITOIRE[territoryKey]) {
          hierarchical.TERRITOIRE[territoryKey] = {
            name: this.getTerritoryName(territoryKey),
            agencies: [],
            totals: {
              par0M1: 0, par0M: 0, par0Ecart: 0, par0Percent: 0,
              par30M1: 0, par30M: 0, par30Ecart: 0, par30Percent: 0,
              par90M1: 0, par90M: 0, par90Ecart: 0, par90Percent: 0
            }
          };
        }
        
        hierarchical.TERRITOIRE[territoryKey].agencies.push(agency);
        
        // Agréger les totaux du territoire
        hierarchical.TERRITOIRE[territoryKey].totals.par0M1 += agency.totals.par0M1;
        hierarchical.TERRITOIRE[territoryKey].totals.par0M += agency.totals.par0M;
        hierarchical.TERRITOIRE[territoryKey].totals.par30M1 += agency.totals.par30M1;
        hierarchical.TERRITOIRE[territoryKey].totals.par30M += agency.totals.par30M;
        hierarchical.TERRITOIRE[territoryKey].totals.par90M1 += agency.totals.par90M1;
        hierarchical.TERRITOIRE[territoryKey].totals.par90M += agency.totals.par90M;
      });
      
      // Calculer les écarts pour les territoires
      Object.values(hierarchical.TERRITOIRE).forEach(territory => {
        territory.totals.par0Ecart = territory.totals.par0M - territory.totals.par0M1;
        territory.totals.par30Ecart = territory.totals.par30M - territory.totals.par30M1;
        territory.totals.par90Ecart = territory.totals.par90M - territory.totals.par90M1;
      });
      
      this.hierarchicalDataFromBackend = hierarchical;
    },
    getTerritoryName(key) {
      const names = {
        'territoire_dakar_ville': 'TERRITOIRE DAKAR VILLE',
        'territoire_dakar_banlieue': 'TERRITOIRE DAKAR BANLIEUE',
        'territoire_province_centre_sud': 'TERRITOIRE PROVINCE CENTRE-SUD',
        'territoire_province_nord': 'TERRITOIRE PROVINCE NORD'
      };
      return names[key] || key.toUpperCase();
    },
    handleStockClick() {
      this.selectedView = 'stock';
      this.fetchStockData();
    },
    async fetchStockData() {
      this.loading = true;
      this.errorMessage = null;
      
      try {
        const response = await axios.get('/api/oracle/data/stock-provision', {
          params: {
            month: this.snapshotMonthYear.month,
            year: this.snapshotMonthYear.year
          }
        });
        
        // Gérer la nouvelle structure hiérarchique
        if (response.data && response.data.TERRITOIRE) {
          // Structure hiérarchique
          this.stockData = response.data;
          // Initialiser l'expansion des territoires
          const expanded = {};
          if (response.data.TERRITOIRE) {
            Object.keys(response.data.TERRITOIRE || {}).forEach(key => {
              expanded[key] = false;
            });
          }
          this.expandedStockTerritories = expanded;
        } else if (response.data && Array.isArray(response.data)) {
          // Structure plate (fallback)
          this.stockDataFlat = response.data;
          this.stockData = { TERRITOIRE: {} };
        } else if (response.data && response.data.data && Array.isArray(response.data.data)) {
          this.stockDataFlat = response.data.data;
          this.stockData = { TERRITOIRE: {} };
        } else {
          this.stockData = { TERRITOIRE: {} };
          this.stockDataFlat = [];
          this.errorMessage = 'Aucune donnée disponible';
        }
      } catch (error) {
        console.error('Erreur lors de la récupération des données Stock:', error);
        this.errorMessage = error.response?.data?.error || error.message || 'Erreur lors du chargement des données Stock';
        this.stockData = { TERRITOIRE: {} };
        this.stockDataFlat = [];
      } finally {
        this.loading = false;
      }
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
      // Pour les pourcentages, utiliser les totaux calculés si disponibles
      if (field.includes('%') || field.includes('Percent')) {
        // Mapper les champs de pourcentage aux totaux
        const percentMap = {
          'VARIATION_PAR_0%': 'par0Percent',
          'VARIATION_PAR_30%': 'par30Percent',
          'VARIATION_PAR_90%': 'par90Percent',
          'VARIATION_PAR_180%': 'par180Percent',
          'VARIATION_PAR_360%': 'par360Percent'
        };
        
        const totalKey = percentMap[field];
        if (totalKey && agency.totals && agency.totals[totalKey] !== undefined) {
          return agency.totals[totalKey];
        }
        
        // Sinon, calculer à partir des données brutes
        if (agency.data && agency.data.length > 0) {
          // Pour les pourcentages, on doit calculer à partir de M et M-1
          const parType = field.includes('PAR_0') ? '0' : 
                         field.includes('PAR_30') ? '30' :
                         field.includes('PAR_90') ? '90' :
                         field.includes('PAR_180') ? '180' :
                         field.includes('PAR_360') ? '360' : null;
          
          if (parType) {
            const m1Field = `PAR_${parType}_M_1`;
            const mField = `PAR_${parType}_M`;
            const m1 = this.getAgencyValue(agency, m1Field);
            const m = this.getAgencyValue(agency, mField);
            if (m1 !== 0 && m1 !== null && m1 !== undefined) {
              return ((m - m1) / m1) * 100;
            }
          }
        }
      }
      
      // Pour les autres champs, utiliser les totaux si disponibles
      if (agency.totals) {
        const totalMap = {
          'PAR_0_M_1': 'par0M1',
          'PAR_0_M': 'par0M',
          'Variation_PAR_0': 'par0Ecart',
          'PAR_30_M_1': 'par30M1',
          'PAR_30_M': 'par30M',
          'Variation_PAR_30': 'par30Ecart',
          'PAR_90_M_1': 'par90M1',
          'PAR_90_M': 'par90M',
          'Variation_PAR_90': 'par90Ecart',
          'PAR_180_M_1': 'par180M1',
          'PAR_180_M': 'par180M',
          'Variation_PAR_180': 'par180Ecart',
          'PAR_360_M_1': 'par360M1',
          'PAR_360_M': 'par360M',
          'Variation_PAR_360': 'par360Ecart'
        };
        
        const totalKey = totalMap[field];
        if (totalKey && agency.totals[totalKey] !== undefined) {
          return agency.totals[totalKey];
        }
      }
      
      // Support de différents formats de données
      // Si c'est un objet avec des données (agence avec data array)
      if (agency.data && agency.data.length > 0) {
        // Agréger les valeurs de tous les chargés d'affaire
        return agency.data.reduce((sum, row) => {
          const value = row[field] || row[field.toUpperCase()] || 0;
          return sum + (parseFloat(value) || 0);
        }, 0);
      }
      
      // Sinon, valeur directe
      const value = agency[field] || 
                   agency[field.toUpperCase()] ||
                   agency[this.camelToSnake(field)] ||
                   0;
      return value === null || value === undefined ? 0 : parseFloat(value) || 0;
    },
    camelToSnake(str) {
      return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    },
    formatValue(value) {
      if (value === null || value === undefined || value === '-') return '-';
      // Convertir en millions de FCFA
      const valueInMillions = value / 1000000;
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(valueInMillions);
    },
    formatRawValue(value) {
      if (value === null || value === undefined || value === '-') return '-';
      // Afficher les valeurs brutes en FCFA avec séparateurs de milliers
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    },
    formatEcart(value) {
      if (value === null || value === undefined || value === '-') return '-';
      if (value === 0) return '0';
      // Convertir en millions de FCFA
      const valueInMillions = value / 1000000;
      const sign = value > 0 ? '+' : '';
      return sign + new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(valueInMillions);
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '-') return '-';
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value) + '%';
    },
    calculatePercent(m1, m) {
      if (!m1 || m1 === 0 || m1 === null || m1 === undefined) return 0;
      if (m === null || m === undefined) return 0;
      const ecart = m - m1;
      return (ecart / m1) * 100;
    },
    getEcartClass(value) {
      if (value === null || value === undefined || value === '-' || value === 0) return '';
      return value > 0 ? 'ecart-red' : 'ecart-green';
    },
    formatPercentValue(value) {
      if (value === null || value === undefined || value === '-') return '0.00';
      // Les valeurs PAR sont des montants, mais pour l'affichage on les traite comme des pourcentages
      // Si la valeur est déjà un pourcentage (entre 0 et 100), l'utiliser directement
      // Sinon, on suppose que c'est un montant et on le formate comme un pourcentage
      const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
      // Si la valeur est > 100, c'est probablement un montant, on le divise par 1000 pour avoir un pourcentage approximatif
      // Sinon, on l'utilise tel quel
      const percentValue = numValue > 100 ? numValue / 1000 : numValue;
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(percentValue);
    },
    formatVariation(value) {
      if (value === null || value === undefined || value === '-') return '0.00';
      const percentValue = typeof value === 'number' ? value : parseFloat(value) || 0;
      const sign = percentValue > 0 ? '+' : '';
      return sign + new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(percentValue);
    },
    getVariationClass(value) {
      if (value === null || value === undefined || value === '-' || value === 0) return '';
      return value > 0 ? 'variation-red' : 'variation-green';
    },
    getDateM1Label() {
      return this.getDateRefLabel();
    },
    getDateRefLabel() {
      const r = this.refMonthYear;
      return `${this.months[r.month - 1]} ${r.year}`;
    },
    getDateMLabel() {
      const s = this.snapshotMonthYear;
      return `${this.months[s.month - 1]} ${s.year}`;
    }
  }
}
</script>

<style scoped>
.collection-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  width: 100%;
}

.tabs-menu {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.tab-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.3s ease;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #050505;
  background: #2d6a4f;
}

.tab-button.active {
  color: #f7f4f4;
  border-bottom-color: #26dc72;
  background: #2d6a4f;
}

.section-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
  letter-spacing: -0.5px;
  flex: 1 1 auto;
  min-width: 0;
  word-break: break-word;
}

.period-selector {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.period-select,
.date-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  color: #333;
  cursor: pointer;
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
  padding: 8px 12px;
  border: 1px solid #DDD;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  color: #333;
  cursor: pointer;
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

.zone-agencies-section {
  margin-top: 20px;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.agencies-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: white;
  min-width: 1200px;
}

.stock-table {
  min-width: 800px;
}

.agencies-table thead {
  background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
  color: white;
  position: sticky;
  top: 0;
  z-index: 10;
}

.agencies-table thead tr:first-child th {
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.agencies-table th {
  padding: 16px 12px;
  text-align: center;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.5px;
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  white-space: nowrap;
  text-transform: uppercase;
  position: relative;
}

.agencies-table th:last-child {
  border-right: none;
}

.agencies-table th:first-child {
  text-align: left;
  padding-left: 20px;
}

.agencies-table tbody tr {
  transition: all 0.2s ease;
}

.agencies-table td {
  padding: 14px 12px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #f3f4f6;
  border-right: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.agencies-table td:last-child {
  border-right: none;
}

.agencies-table td:first-child {
  text-align: left;
  padding-left: 20px;
}

.agencies-table tbody tr:last-child td {
  border-bottom: none;
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

.total-row td:first-child {
  border-bottom-left-radius: 12px;
}

.total-row td:last-child {
  border-bottom-right-radius: 12px;
}

.level-1-row {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: white;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.level-1-row:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.level-1 {
  font-size: 15px;
  padding-left: 20px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.3px;
}

.level-2-row {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.level-2-row:hover {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
}

.service-point-row {
  background: #f9fafb !important;
  color: #333 !important;
}

.service-point-row:hover {
  background: #f3f4f6 !important;
}

.service-point-cell {
  color: #333 !important;
}

.level-2 {
  font-size: 14px;
  padding-left: 40px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.level-3-row {
  background: #f8fafc;
  font-weight: 500;
  border-left: 4px solid #3b82f6;
  transition: all 0.2s ease;
}

.level-3-row:hover {
  background: #e0e7ff;
  border-left-color: #2563eb;
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.level-3 {
  padding-left: 56px !important;
  color: #1f2937;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
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
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.level-3-row .expand-btn {
  border: 2px solid #3b82f6;
  background: #3b82f6;
  color: white;
}

.level-3-row .expand-btn:hover {
  background: #2563eb;
  border-color: #2563eb;
}

.ecart-red {
  color: #ad0505 !important;
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(8, 8, 8, 0.2);
}

.ecart-green {
  color: #10b981 !important;
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(16, 185, 129, 0.2);
}

.percent-red {
  color: #ad0505 !important;
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(8, 8, 8, 0.2);
}

.variation-red {
  color: #ad0505 !important;
  font-weight: 700;
  font-size: 13px;
  position: relative;
}

.variation-red::before {
  content: '☑';
  margin-right: 4px;
  color: #ad0505;
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

.par-global-table {
  min-width: 1600px;
}

.par-global-section {
  margin-top: 20px;
}


.no-data-row {
  background: #f9fafb;
  color: #6b7280;
  font-style: italic;
}

/* Amélioration de la séparation visuelle entre les groupes PAR */
.agencies-table th[colspan="4"] {
  border-right: 2px solid rgba(255, 255, 255, 0.3);
  position: relative;
}

.agencies-table th[colspan="4"]:not(:last-of-type)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 20%;
  bottom: 20%;
  width: 1px;
  background: rgba(255, 255, 255, 0.3);
}

/* Amélioration des onglets */
.tabs-menu {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
  background: #f9fafb;
  padding: 4px;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.tab-button {
  padding: 14px 28px;
  font-size: 15px;
  font-weight: 600;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.3s ease;
  position: relative;
  letter-spacing: 0.3px;
}

.tab-button:hover {
  color: #1f2937;
  background: rgba(45, 106, 79, 0.1);
}

.tab-button.active {
  color: white;
  background: linear-gradient(135deg, #2d6a4f 0%, #1a4d3a 100%);
  box-shadow: 0 2px 8px rgba(45, 106, 79, 0.3);
}

/* Amélioration des sélecteurs */
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

.month-select:focus,
.year-select:focus {
  outline: none;
  border-color: #2d6a4f;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.1);
}

/* Media Queries pour le responsive */

/* Tablettes et écrans moyens */
@media (max-width: 1200px) {
  .agencies-table {
    min-width: 1000px;
    font-size: 12px;
  }
  
  .agencies-table th {
    padding: 12px 8px;
    font-size: 11px;
  }
  
  .agencies-table td {
    padding: 10px 8px;
    font-size: 11px;
  }
  
  .section-title {
    font-size: 22px;
  }
  
  .level-1 {
    font-size: 14px;
    padding-left: 15px !important;
  }
  
  .level-2 {
    font-size: 13px;
    padding-left: 30px !important;
  }
  
  .level-3 {
    padding-left: 45px !important;
    font-size: 12px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .collection-section {
    margin-bottom: 20px;
  }
  
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
  
  .tabs-menu {
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px;
  }
  
  .tab-button {
    flex: 1;
    min-width: 120px;
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .agencies-table {
    min-width: 900px;
    font-size: 11px;
  }
  
  .agencies-table th {
    padding: 10px 6px;
    font-size: 10px;
  }
  
  .agencies-table td {
    padding: 8px 6px;
    font-size: 10px;
  }
  
  .agencies-table th:first-child,
  .agencies-table td:first-child {
    padding-left: 10px;
  }
  
  .level-1 {
    font-size: 13px;
    padding-left: 10px !important;
  }
  
  .level-2 {
    font-size: 12px;
    padding-left: 25px !important;
  }
  
  .level-3 {
    padding-left: 35px !important;
    font-size: 11px;
  }
  
  .expand-btn {
    width: 24px;
    height: 24px;
    font-size: 16px;
    margin-right: 8px;
  }
  
  .total-row td {
    padding: 12px 8px;
    font-size: 12px;
  }
  
  .loading-message,
  .error-message {
    padding: 10px 12px;
    font-size: 13px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .section-header {
    padding: 12px;
  }
  
  .section-title {
    font-size: 18px;
    line-height: 1.3;
  }
  
  .period-selector {
    flex-direction: column;
    width: 100%;
  }
  
  .month-select,
  .year-select {
    width: 100%;
    min-width: 100%;
  }
  
  .tabs-menu {
    flex-direction: column;
    gap: 6px;
  }
  
  .tab-button {
    width: 100%;
    min-width: 100%;
    padding: 10px 14px;
    font-size: 13px;
  }
  
  .agencies-table {
    min-width: 800px;
    font-size: 10px;
  }
  
  .agencies-table th {
    padding: 8px 4px;
    font-size: 9px;
  }
  
  .agencies-table td {
    padding: 6px 4px;
    font-size: 9px;
  }
  
  .agencies-table th:first-child,
  .agencies-table td:first-child {
    padding-left: 8px;
    min-width: 100px;
  }
  
  .level-1 {
    font-size: 12px;
    padding-left: 8px !important;
  }
  
  .level-2 {
    font-size: 11px;
    padding-left: 20px !important;
  }
  
  .level-3 {
    padding-left: 30px !important;
    font-size: 10px;
  }
  
  .expand-btn {
    width: 22px;
    height: 22px;
    font-size: 14px;
    margin-right: 6px;
  }
  
  .total-row td {
    padding: 10px 6px;
    font-size: 11px;
  }
  
  .ecart-red,
  .ecart-green,
  .percent-red {
    font-size: 10px;
  }
  
  .table-container {
    border-radius: 8px;
  }
  
  .zone-agencies-section {
    margin-top: 15px;
  }
}
</style>
