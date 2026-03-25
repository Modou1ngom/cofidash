<template>
  <div class="volume-dat-section">
    <div class="section-header">
      <h2 class="section-title">ENCOURS DAT - {{ getPeriodTitle() }}</h2>
      <div class="period-selector">
        <select v-model="selectedPeriod" class="period-select" @change="handlePeriodChange">
          <option value="week">Semaine</option>
          <option value="month">Mois</option>
          <option value="year">Année</option>
        </select>
        
        <!-- Sélecteur de date pour Semaine -->
        <template v-if="selectedPeriod === 'week'">
          <input 
            type="date" 
            v-model="selectedDate" 
            class="date-select"
            @change="handleDateChange"
            @input="handleDateChange"
          />
        </template>
        
        <!-- Sélecteurs pour Mois -->
        <template v-if="selectedPeriod === 'month'">
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
        </template>
        
        <!-- Sélecteur pour Année -->
        <template v-if="selectedPeriod === 'year'">
          <select v-model="selectedYear" class="year-select" @change="handleYearChange">
            <option v-for="year in years" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </template>
      </div>
    </div>
    
    <!-- Résultat Global -->
    <div class="global-result-section">
      <div v-if="loading" class="loading-message">
        <p>🔄 Chargement des données depuis Oracle...</p>
      </div>
      <div v-if="errorMessage" class="error-message">
        <p>⚠️ {{ errorMessage }}</p>
      </div>
    </div>

    <!-- Tableau hiérarchique Volume DAT -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>DAT_M_1</th>
              <th>DAT_M</th>
              <th>VARIATION_VOLUME_DA</th>
              <th>VARIATION_DAT%</th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections['TERRITOIRE'] ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>{{ formatNumber(territoireTotalVolumeDat.datM1) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotalVolumeDat.datM) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotalVolumeDat.variationVolumeDa) }}</strong></td>
              <td><strong>{{ formatPercent(territoireTotalVolumeDat.variationDat) }}</strong></td>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections['TERRITOIRE']">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <tr v-if="territoryKey !== 'grand_compte'" class="level-2-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <td><strong>{{ formatNumber(getVolumeDatTotal(territory, 'datM1')) }}</strong></td>
                  <td><strong>{{ formatNumber(getVolumeDatTotal(territory, 'datM')) }}</strong></td>
                  <td><strong>{{ formatNumber(getVolumeDatTotal(territory, 'variationVolumeDa')) }}</strong></td>
                  <td><strong>{{ formatPercent(getVolumeDatTotal(territory, 'variationDat')) }}</strong></td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <tr 
                    v-for="agency in territory.agencies" 
                    :key="agency.name" 
                    class="level-3-row"
                    :class="{ 'selected-agency': selectedAgency && selectedAgency.name === agency.name && selectedAgency.category === 'TERRITOIRE' && selectedAgency.zone === territoryKey }"
                    @click="selectAgency({ name: agency.name, category: 'TERRITOIRE', zone: territoryKey })"
                  >
                    <td class="level-3">{{ getAgencyName(agency) }}</td>
                    <td>{{ formatNumber(getVolumeDatValue(agency, 'DAT_M_1')) }}</td>
                    <td>{{ formatNumber(getVolumeDatValue(agency, 'DAT_M')) }}</td>
                    <td>{{ formatNumber(getVolumeDatValue(agency, 'VARIATION_VOLUME_DA')) }}</td>
                    <td>{{ formatPercent(getVolumeDatValue(agency, 'VARIATION_DAT')) }}</td>
                  </tr>
                </template>
              </template>
            </template>

            <!-- POINT SERVICES -->
            <tr class="level-1-row" @click="toggleExpand('POINT SERVICES')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('POINT SERVICES')">
                  {{ expandedSections['POINT SERVICES'] ? '−' : '+' }}
                </button>
                <strong>POINT SERVICES</strong>
              </td>
              <td><strong>{{ formatNumber(pointServicesTotalVolumeDat.datM1) }}</strong></td>
              <td><strong>{{ formatNumber(pointServicesTotalVolumeDat.datM) }}</strong></td>
              <td><strong>{{ formatNumber(pointServicesTotalVolumeDat.variationVolumeDa) }}</strong></td>
              <td><strong>{{ formatPercent(pointServicesTotalVolumeDat.variationDat) }}</strong></td>
            </tr>
            
            <!-- Points de service individuels directement sous POINT SERVICES -->
            <template v-if="expandedSections['POINT SERVICES']">
              <template v-for="(servicePoint, servicePointKey) in filteredHierarchicalData['POINT SERVICES']" :key="`point-service-${servicePointKey}`">
                <template v-if="servicePoint">
                  <template v-if="servicePoint.agencies && Array.isArray(servicePoint.agencies) && servicePoint.agencies.length > 0">
                    <tr 
                      v-for="(agency, agencyIndex) in servicePoint.agencies" 
                      :key="`agency-${servicePointKey}-${agencyIndex}-${agency.name || agency.AGENCE || agencyIndex}`"
                      class="level-2-row service-point-row"
                      :class="{ 'selected-agency': selectedAgency && selectedAgency.name === agency.name && selectedAgency.category === 'POINT SERVICES' }"
                      @click="selectAgency({ name: agency.name, category: 'POINT SERVICES', zone: servicePointKey })"
                    >
                      <td class="level-2 service-point-cell">{{ getAgencyName(agency) }}</td>
                      <td>{{ formatNumber(getVolumeDatValue(agency, 'DAT_M_1')) }}</td>
                      <td>{{ formatNumber(getVolumeDatValue(agency, 'DAT_M')) }}</td>
                      <td>{{ formatNumber(getVolumeDatValue(agency, 'VARIATION_VOLUME_DA')) }}</td>
                      <td>{{ formatPercent(getVolumeDatValue(agency, 'VARIATION_DAT')) }}</td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
            
            <!-- GRAND COMPTE -->
            <tr v-if="grandCompteVolumeDat" class="level-3-row">
              <td class="level-3">GRAND COMPTE</td>
              <td>{{ formatNumber(grandCompteVolumeDat.DAT_M_1 || 0) }}</td>
              <td>{{ formatNumber(grandCompteVolumeDat.DAT_M || 0) }}</td>
              <td>{{ formatNumber(grandCompteVolumeDat.VARIATION_VOLUME_DA || 0) }}</td>
              <td>{{ formatPercent(grandCompteVolumeDat.VARIATION_DAT || 0) }}</td>
            </tr>

            <!-- Ligne TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ formatNumber(getGrandTotalVolumeDat('datM1')) }}</strong></td>
              <td><strong>{{ formatNumber(getGrandTotalVolumeDat('datM')) }}</strong></td>
              <td><strong>{{ formatNumber(getGrandTotalVolumeDat('variationVolumeDa')) }}</strong></td>
              <td><strong>{{ formatPercent(getGrandTotalVolumeDat('variationDat')) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Section Graphique d'évolution -->
    <div class="chart-evolution-section" v-if="hasChartData">
      <div class="chart-header">
        <div class="chart-title-section">
          <h3 class="chart-section-title">{{ chartTitle }}</h3>
          <div class="breadcrumb" v-if="activeLevel.type !== 'total'">
            <span class="breadcrumb-item" @click="resetToTotal()">Total</span>
            <span class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item" v-if="activeLevel.type === 'category' || activeLevel.type === 'zone' || activeLevel.type === 'agency'">
              {{ activeLevel.category }}
            </span>
            <span v-if="activeLevel.type === 'zone' || activeLevel.type === 'agency'" class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item" v-if="activeLevel.type === 'zone' || activeLevel.type === 'agency'">
              {{ getTerritoryName(activeLevel.zone) }}
            </span>
            <span v-if="activeLevel.type === 'agency'" class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item active" v-if="activeLevel.type === 'agency'">
              {{ activeLevel.name }}
            </span>
          </div>
        </div>
        <div class="chart-actions">
          <button @click="exportChart('png')" class="export-btn" title="Exporter en PNG">
            📷 PNG
          </button>
          <button @click="exportChart('pdf')" class="export-btn" title="Exporter en PDF">
            📄 PDF
          </button>
          <button @click="exportChart('csv')" class="export-btn" title="Exporter les données en CSV">
            📊 CSV
          </button>
        </div>
      </div>
      
      <!-- Menu pour basculer entre Graphique et Performance -->
      <div class="chart-view-tabs">
        <button 
          :class="['chart-view-tab', { active: chartViewMode === 'graph' }]"
          @click="chartViewMode = 'graph'"
        >
          📈 Graphique
        </button>
        <button 
          :class="['chart-view-tab', { active: chartViewMode === 'performance' }]"
          @click="chartViewMode = 'performance'"
        >
          🏆 Performance
        </button>
      </div>
      
      <!-- Vue Graphique -->
      <div v-if="chartViewMode === 'graph'">
        <div class="chart-tabs">
          <button 
            :class="['chart-tab', { active: selectedChartType === 'line' }]"
            @click="selectedChartType = 'line'"
            title="Graphique en ligne"
          >
            📈 Ligne
          </button>
          <button 
            :class="['chart-tab', { active: selectedChartType === 'bar' }]"
            @click="selectedChartType = 'bar'"
            title="Graphique en barres"
          >
            📊 Barres
          </button>
          <button 
            :class="['chart-tab', { active: selectedChartType === 'area' }]"
            @click="selectedChartType = 'area'"
            title="Graphique en aires"
          >
            📉 Aires
          </button>
          <button 
            :class="['chart-tab', { active: selectedChartType === 'pie' }]"
            @click="selectedChartType = 'pie'"
            title="Graphique circulaire"
          >
            🥧 Circulaire
          </button>
        </div>
        
        <!-- Sélecteur de données -->
        <div class="data-type-selector">
          <label>
            <input 
              type="radio" 
              value="volume_dat" 
              v-model="selectedDataType"
              @change="updateChart"
            />
            Volume DAT
          </label>
        </div>
        
        <div class="chart-wrapper-container">
          <PythonChart
            :key="`chart-${selectedChartType}-${selectedDataType}-${activeLevel.type}-${activeLevel.category || ''}-${activeLevel.zone || ''}-${activeLevel.name || ''}`"
            :chartType="selectedChartType"
            :chartData="currentChartData"
            :height="600"
            ref="chartComponent"
          />
        </div>
      </div>
      
      <!-- Vue Performance -->
      <div v-if="chartViewMode === 'performance'">
        <AgencyPerformanceSection 
          :dataType="'volume_dat'" 
          :tableData="performanceTableData"
        />
      </div>
    </div>
    <div v-else class="chart-evolution-section">
      <h3 class="chart-section-title">Évolution du Volume DAT</h3>
      <div class="chart-wrapper-container" style="display: flex; align-items: center; justify-content: center; color: #999;">
        <p>Chargement des données...</p>
      </div>
    </div>
  </div>
</template>

<script>
import PythonChart from './charts/PythonChart.vue';
import AgencyPerformanceSection from './AgencyPerformanceSection.vue';

export default {
  name: 'VolumeDatSection',
  components: {
    PythonChart,
    AgencyPerformanceSection
  },
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    }
  },
  data() {
    const now = new Date();
    return {
      loading: false,
      errorMessage: null,
      selectedZone: null,
      selectedPeriod: 'month',
      selectedDate: (() => {
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      })(),
      selectedWeek: this.getWeekNumber(now),
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      expandedSections: {
        TERRITOIRE: false,
        'POINT SERVICES': false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      },
      hierarchicalDataFromBackend: null,
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      selectedAgency: null,
      selectedChartType: 'line',
      selectedDataType: 'volume_dat',
      chartViewMode: 'graph' // 'graph' ou 'performance'
    }
  },
  mounted() {
    this.fetchDataFromOracle();
  },
  watch: {
    selectedZoneProp(newVal) {
      this.selectedZone = newVal;
      this.fetchDataFromOracle();
    },
    selectedPeriod() {
      this.loadDataForPeriod();
    },
    selectedDate() {
      this.updateWeekFromDate();
      this.loadDataForPeriod();
    },
    selectedWeek() {
      this.loadDataForPeriod();
    },
    selectedMonth(newVal, oldVal) {
      if (newVal !== oldVal && oldVal !== undefined) {
        this.loadDataForPeriod();
      }
    },
    selectedYear(newVal, oldVal) {
      if (newVal !== oldVal && oldVal !== undefined) {
        this.loadDataForPeriod();
      }
    }
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
    hierarchicalData() {
      if (this.hierarchicalDataFromBackend && typeof this.hierarchicalDataFromBackend === 'object') {
        return this.hierarchicalDataFromBackend;
      }
      return {
        TERRITOIRE: {},
        'POINT SERVICES': {}
      };
    },
    filteredHierarchicalData() {
      if (!this.selectedZone) {
        return this.hierarchicalData;
      }
      
      const filtered = {
        TERRITOIRE: {},
        'POINT SERVICES': this.hierarchicalData['POINT SERVICES'] || {}
      };
      
      if (this.hierarchicalData.TERRITOIRE && 
          typeof this.hierarchicalData.TERRITOIRE === 'object' && 
          this.hierarchicalData.TERRITOIRE !== null &&
          !Array.isArray(this.hierarchicalData.TERRITOIRE) &&
          this.hierarchicalData.TERRITOIRE[this.selectedZone]) {
        filtered.TERRITOIRE[this.selectedZone] = this.hierarchicalData.TERRITOIRE[this.selectedZone];
      }
      
      return filtered;
    },
    territoireTotalVolumeDat() {
      const hierarchicalData = this.filteredHierarchicalData || {};
      let total = {
        datM1: 0,
        datM: 0,
        variationVolumeDa: 0,
        variationDat: 0
      };
      
      if (hierarchicalData.TERRITOIRE) {
        Object.entries(hierarchicalData.TERRITOIRE).forEach(([territoryKey, territory]) => {
          if (territoryKey !== 'grand_compte' && territory && territory.agencies) {
            territory.agencies.forEach(agency => {
              total.datM1 += parseFloat(this.getVolumeDatValue(agency, 'DAT_M_1') || 0);
              total.datM += parseFloat(this.getVolumeDatValue(agency, 'DAT_M') || 0);
              total.variationVolumeDa += parseFloat(this.getVolumeDatValue(agency, 'VARIATION_VOLUME_DA') || 0);
              total.variationDat += parseFloat(this.getVolumeDatValue(agency, 'VARIATION_DAT') || 0);
            });
          }
        });
      }
      
      return total;
    },
    pointServicesTotalVolumeDat() {
      const hierarchicalData = this.filteredHierarchicalData || {};
      let total = {
        datM1: 0,
        datM: 0,
        variationVolumeDa: 0,
        variationDat: 0
      };
      
      if (hierarchicalData['POINT SERVICES']) {
        Object.values(hierarchicalData['POINT SERVICES']).forEach(servicePoint => {
          if (servicePoint && servicePoint.agencies) {
            servicePoint.agencies.forEach(agency => {
              total.datM1 += parseFloat(this.getVolumeDatValue(agency, 'DAT_M_1') || 0);
              total.datM += parseFloat(this.getVolumeDatValue(agency, 'DAT_M') || 0);
              total.variationVolumeDa += parseFloat(this.getVolumeDatValue(agency, 'VARIATION_VOLUME_DA') || 0);
              total.variationDat += parseFloat(this.getVolumeDatValue(agency, 'VARIATION_DAT') || 0);
            });
          }
        });
      }
      
      return total;
    },
    grandCompteVolumeDat() {
      const hierarchicalData = this.filteredHierarchicalData || {};
      if (hierarchicalData.TERRITOIRE && hierarchicalData.TERRITOIRE.grand_compte) {
        const grandCompte = hierarchicalData.TERRITOIRE.grand_compte;
        if (grandCompte.agencies && grandCompte.agencies.length > 0) {
          return {
            DAT_M_1: this.getVolumeDatTotal(grandCompte, 'datM1'),
            DAT_M: this.getVolumeDatTotal(grandCompte, 'datM'),
            VARIATION_VOLUME_DA: this.getVolumeDatTotal(grandCompte, 'variationVolumeDa'),
            VARIATION_DAT: this.getVolumeDatTotal(grandCompte, 'variationDat')
          };
        }
      }
      return null;
    },
    performanceTableData() {
      if (this.hierarchicalDataFromBackend) {
        return {
          hierarchicalData: this.hierarchicalDataFromBackend
        };
      }
      return null;
    },
    hasChartData() {
      // Pour Volume DAT, on affiche M-1 et M (2 valeurs)
      return this.chartLabels.length > 0 && 
             this.chartCurrentData.length > 0 && 
             this.chartCurrentData.length === this.chartLabels.length &&
             this.chartCurrentData.length === 2;
    },
    activeLevel() {
      if (this.selectedAgency) {
        return {
          type: 'agency',
          category: this.selectedAgency.category,
          zone: this.selectedAgency.zone,
          name: this.selectedAgency.name
        };
      }
      
      for (const key in this.expandedSections) {
        if (key.startsWith('TERRITOIRE_') && this.expandedSections[key]) {
          const zoneKey = key.replace('TERRITOIRE_', '');
          return {
            type: 'zone',
            category: 'TERRITOIRE',
            zone: zoneKey,
            name: this.hierarchicalData.TERRITOIRE[zoneKey]?.name || `Zone ${zoneKey}`
          };
        }
      }
      
      if (this.expandedSections.TERRITOIRE) {
        return {
          type: 'category',
          category: 'TERRITOIRE',
          name: 'TERRITOIRE'
        };
      }
      if (this.expandedSections['POINT SERVICES']) {
        return {
          type: 'category',
          category: 'POINT SERVICES',
          name: 'POINT SERVICES'
        };
      }
      
      return {
        type: 'total',
        name: 'Total'
      };
    },
    chartTitle() {
      const level = this.activeLevel;
      return `Évolution - ${level.name}`;
    },
    chartLabels() {
      // Pour Volume DAT, on affiche M-1 et M
      return ['M-1', 'M'];
    },
    chartCurrentData() {
      const level = this.activeLevel;
      let data = [];
      
      const normalizeValue = (value) => {
        const num = parseFloat(value);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      };
      
      if (level.type === 'agency') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        if (agency) {
          data = [
            normalizeValue(this.getVolumeDatValue(agency, 'DAT_M_1')),
            normalizeValue(this.getVolumeDatValue(agency, 'DAT_M'))
          ];
        }
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        if (zoneData?.totals) {
          data = [
            normalizeValue(zoneData.totals.datM1 || 0),
            normalizeValue(zoneData.totals.datM || 0)
          ];
        }
      } else if (level.type === 'category') {
        if (level.category === 'TERRITOIRE') {
          data = [
            normalizeValue(this.territoireTotalVolumeDat.datM1),
            normalizeValue(this.territoireTotalVolumeDat.datM)
          ];
        } else {
          data = [
            normalizeValue(this.pointServicesTotalVolumeDat.datM1),
            normalizeValue(this.pointServicesTotalVolumeDat.datM)
          ];
        }
      } else {
        // Total général
        data = [
          normalizeValue(this.getGrandTotalVolumeDat('datM1')),
          normalizeValue(this.getGrandTotalVolumeDat('datM'))
        ];
      }
      
      return data.map(v => normalizeValue(v));
    },
    currentChartData() {
      const labels = this.chartLabels;
      const current = this.chartCurrentData;
      const title = `${this.chartTitle} - Volume DAT`;
      const ylabel = 'Volume DAT (FCFA)';
      
      const normalizedCurrent = current.map(v => {
        const num = parseFloat(v);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      });
      
      if (this.selectedChartType === 'bar') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title,
          xlabel: 'Période',
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'area') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title,
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'pie') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title
        };
      } else {
        // Pour les graphiques en ligne
        return {
          labels: labels,
          current: normalizedCurrent,
          previous: normalizedCurrent,
          title: title,
          ylabel: ylabel
        };
      }
    }
  },
  methods: {
    getWeekNumber(date) {
      const d = date instanceof Date ? date : new Date(date);
      const dateObj = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
      const dayNum = dateObj.getUTCDay() || 7;
      dateObj.setUTCDate(dateObj.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(dateObj.getUTCFullYear(), 0, 1));
      return Math.ceil((((dateObj - yearStart) / 86400000) + 1) / 7);
    },
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        return 'Résultat de la semaine';
      } else if (this.selectedPeriod === 'month') {
        return `Résultat Global du Mois (${this.months[this.selectedMonth - 1]} ${this.selectedYear})`;
      } else if (this.selectedPeriod === 'year') {
        return `Résultat Global de l'Année (${this.selectedYear})`;
      }
      return 'Résultat Global';
    },
    updateWeekFromDate() {
      if (this.selectedDate) {
        const date = new Date(this.selectedDate);
        this.selectedYear = date.getFullYear();
        this.selectedWeek = this.getWeekNumber(date);
      }
    },
    formatNumber(num) {
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    formatPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return `${num.toFixed(0)}%`;
    },
    getAgencyName(agency) {
      if (!agency) return 'Agence non identifiée';
      const name = agency.name || agency.AGENCE || agency.NOM_AGENCE || agency.agence || agency.BRANCH_NAME || agency.branch_name || '';
      if (name && name.trim() !== '') {
        return name.trim();
      }
      return 'Agence non identifiée';
    },
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    selectAgency(agency) {
      if (this.selectedAgency && 
          this.selectedAgency.name === agency.name && 
          this.selectedAgency.category === agency.category && 
          this.selectedAgency.zone === agency.zone) {
        this.selectedAgency = null;
      } else {
        this.selectedAgency = agency;
      }
    },
    resetToTotal() {
      this.selectedAgency = null;
      this.expandedSections.TERRITOIRE = false;
      this.expandedSections['POINT SERVICES'] = false;
      Object.keys(this.expandedSections).forEach(key => {
        if (key.startsWith('TERRITOIRE_')) {
          this.expandedSections[key] = false;
        }
      });
    },
    getTerritoryName(zoneKey) {
      const territoryNames = {
        'territoire_dakar_ville': 'DAKAR CENTRE VILLE',
        'territoire_dakar_banlieue': 'DAKAR BANLIEUE',
        'province_centre_sud': 'PROVINCE CENTRE SUD',
        'province_nord': 'PROVINCE NORD'
      };
      return territoryNames[zoneKey] || zoneKey;
    },
    updateChart() {
      this.$nextTick(() => {});
    },
    async exportChart(format) {
      try {
        await this.$nextTick();
        
        if (format === 'csv') {
          const labels = this.chartLabels;
          const current = this.chartCurrentData;
          let csv = 'Période,Volume DAT\n';
          
          for (let i = 0; i < labels.length; i++) {
            const value = current[i] || 0;
            csv += `"${labels[i]}",${value}\n`;
          }
          
          const BOM = '\uFEFF';
          const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          const fileName = `donnees-volume-dat-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.csv`;
          link.download = fileName;
          link.href = URL.createObjectURL(blob);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          setTimeout(() => URL.revokeObjectURL(link.href), 100);
          return;
        }
        
        const chartRef = this.$refs.chartComponent;
        if (!chartRef || !chartRef.chartContainer) {
          alert('Le graphique n\'est pas encore chargé. Veuillez attendre quelques instants.');
          return;
        }

        if (format === 'png' || format === 'pdf') {
          const Plotly = (await import('plotly.js-dist')).default;
          const container = chartRef.chartContainer;
          
          if (!container) {
            alert('Le graphique n\'est pas encore chargé. Veuillez attendre quelques instants.');
            return;
          }
          
          const img = await Plotly.toImage(container, {
            format: 'png',
            width: 1200,
            height: 600
          });
          
          const link = document.createElement('a');
          const extension = format === 'pdf' ? 'png' : 'png';
          const fileName = `graphique-volume-dat-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedChartType}-${new Date().toISOString().split('T')[0]}.${extension}`;
          link.download = fileName;
          link.href = img;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          if (format === 'pdf') {
            alert('Graphique exporté en PNG. Pour PDF, ouvrez l\'image et utilisez "Imprimer en PDF" de votre navigateur.');
          }
        }
      } catch (error) {
        alert('Erreur lors de l\'export du graphique : ' + error.message);
      }
    },
    getVolumeDatValue(data, field) {
      if (!data) return 0;
      
      const fieldMap = {
        'DAT_M_1': ['DAT_M_1', 'dat_m_1', 'datM1', 'DATM1'],
        'DAT_M': ['DAT_M', 'dat_m', 'datM', 'DATM'],
        'VARIATION_VOLUME_DA': ['VARIATION_VOLUME_DA', 'variation_volume_da', 'variationVolumeDa', 'VARIATIONVOLUMEDA'],
        'VARIATION_DAT': ['VARIATION_DAT', 'variation_dat', 'variationDat', 'VARIATIONDAT', 'VARIATION_DAT%']
      };
      
      const possibleFields = fieldMap[field] || [field];
      
      for (const possibleField of possibleFields) {
        if (data[possibleField] !== undefined && data[possibleField] !== null) {
          return parseFloat(data[possibleField]) || 0;
        }
      }
      
      return 0;
    },
    getVolumeDatTotal(territory, field) {
      if (!territory || !territory.agencies) return 0;
      
      let total = 0;
      territory.agencies.forEach(agency => {
        const fieldMap = {
          'datM1': 'DAT_M_1',
          'datM': 'DAT_M',
          'variationVolumeDa': 'VARIATION_VOLUME_DA',
          'variationDat': 'VARIATION_DAT'
        };
        
        const mappedField = fieldMap[field] || field;
        total += parseFloat(this.getVolumeDatValue(agency, mappedField) || 0);
      });
      
      return total;
    },
    getGrandTotalVolumeDat(field) {
      let total = this.territoireTotalVolumeDat[field] + this.pointServicesTotalVolumeDat[field];
      if (this.grandCompteVolumeDat) {
        const fieldMap = {
          'datM1': 'DAT_M_1',
          'datM': 'DAT_M',
          'variationVolumeDa': 'VARIATION_VOLUME_DA',
          'variationDat': 'VARIATION_DAT'
        };
        const mappedField = fieldMap[field] || field;
        total += parseFloat(this.grandCompteVolumeDat[mappedField] || 0);
      }
      return total;
    },
    async fetchDataFromOracle() {
      this.loading = true;
      try {
        const params = {
          period: this.selectedPeriod,
          zone: this.selectedZone || null
        };
        
        if (this.selectedPeriod === 'week') {
          if (this.selectedDate) {
            let dateToSend = this.selectedDate;
            if (dateToSend.includes('/')) {
              const parts = dateToSend.split('/');
              dateToSend = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            params.date = dateToSend;
          }
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        this.errorMessage = null;

        const response = await window.axios.get('/api/oracle/data/volume-dat', { params });
        
        let data = null;
        
        if (response.data && response.data.data) {
          data = response.data.data;
        } else if (response.data) {
          data = response.data;
        }
        
        if (data && data.hierarchicalData) {
          this.hierarchicalDataFromBackend = data.hierarchicalData;
          console.log('📊 Volume DAT - Données reçues:', {
            hasTerritoire: !!data.hierarchicalData.TERRITOIRE,
            hasPointServices: !!data.hierarchicalData['POINT SERVICES'],
            pointServicesKeys: Object.keys(data.hierarchicalData['POINT SERVICES'] || {}),
            pointServicesStructure: data.hierarchicalData['POINT SERVICES']
          });
        } else {
          this.hierarchicalDataFromBackend = {
            TERRITOIRE: {},
            'POINT SERVICES': {}
          };
        }
      } catch (error) {
        this.hierarchicalDataFromBackend = {
          TERRITOIRE: {},
          'POINT SERVICES': {}
        };
        
        if (error.response && error.response.data) {
          const errorData = error.response.data;
          if (errorData.error) {
            this.errorMessage = `Erreur: ${errorData.error}. ${errorData.message || ''}`;
          } else if (errorData.message) {
            this.errorMessage = errorData.message;
          } else {
            this.errorMessage = 'Erreur lors du chargement des données depuis Oracle. Veuillez réessayer.';
          }
        } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          this.errorMessage = 'La requête a pris trop de temps. Veuillez réessayer ou vérifier la connexion au serveur Oracle.';
        } else {
          this.errorMessage = 'Erreur de connexion. Veuillez vérifier que le service Oracle est accessible.';
        }
      } finally {
        this.loading = false;
      }
    },
    loadDataForPeriod() {
      this.hierarchicalDataFromBackend = null;
      this.expandedSections = {
        TERRITOIRE: false,
        'POINT SERVICES': false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      };
      this.fetchDataFromOracle();
    },
    handlePeriodChange() {
      this.loadDataForPeriod();
    },
    handleMonthChange() {
      this.loadDataForPeriod();
    },
    handleYearChange() {
      this.loadDataForPeriod();
    },
    handleDateChange() {
      this.updateWeekFromDate();
      this.$nextTick(() => {
        this.loadDataForPeriod();
      });
    }
  }
}
</script>

<style scoped>
.volume-dat-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
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

.period-select,
.month-select,
.week-select,
.year-select,
.date-select {
  padding: 8px 12px;
  border: 1px solid #DDD;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  color: #333;
  cursor: pointer;
}

.period-select:hover,
.month-select:hover,
.week-select:hover,
.year-select:hover,
.date-select:hover {
  border-color: #1A4D3A;
}

.period-select:focus,
.month-select:focus,
.week-select:focus,
.year-select:focus,
.date-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.1);
}

.global-result-section {
  margin-bottom: 40px;
}

.loading-message {
  background: #E3F2FD;
  border: 1px solid #2196F3;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: center;
  color: #1976D2;
  font-weight: 500;
}

.error-message {
  background: #FFEBEE;
  border: 1px solid #F44336;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: center;
  color: #C62828;
  font-weight: 500;
}

.zone-agencies-section {
  margin-top: 30px;
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
  min-width: 1200px;
}

.agencies-table thead {
  background: #DC2626;
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
  border-bottom: 1px solid #EEE;
  border-right: 1px solid #F0F0F0;
}

.agencies-table td:first-child {
  text-align: left;
  padding-left: 16px;
}

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
}

.level-1-row {
  background: #2A2A2A;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.level-1 {
  font-size: 16px;
  padding-left: 16px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-2-row {
  background: #4A4A4A;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.service-point-row {
  background: white !important;
  color: #333 !important;
}

.service-point-cell {
  color: #333 !important;
}

.level-2 {
  font-size: 14px;
  padding-left: 32px !important;
  cursor: pointer;
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
  cursor: pointer;
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
  transition: background 0.2s;
}

.level-2 .expand-btn {
  border-color: rgba(255, 255, 255, 0.3);
}

.no-data-row {
  text-align: center;
  padding: 40px;
  color: #666;
}

.agency-name {
  font-weight: 500;
  color: #333;
  min-width: 150px;
}

@media (max-width: 768px) {
  .table-container {
    overflow-x: scroll;
  }
}

.selected-agency {
  background: #e3f2fd !important;
  border-left: 4px solid #1A4D3A;
}

.chart-evolution-section {
  margin-top: 30px;
  background: white;
  border: 1px solid #DDD;
  border-radius: 4px;
  padding: 20px;
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.chart-title-section {
  flex: 1;
}

.chart-section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #666;
  flex-wrap: wrap;
}

.breadcrumb-item {
  cursor: pointer;
  color: #1A4D3A;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #0d3320;
  text-decoration: underline;
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 600;
  cursor: default;
}

.breadcrumb-item.active:hover {
  text-decoration: none;
}

.breadcrumb-separator {
  color: #999;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.export-btn {
  padding: 6px 12px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.export-btn:hover {
  background: #153d2a;
}

.chart-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #DDD;
  margin-bottom: 20px;
}

.chart-tab {
  padding: 10px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.chart-tab:hover {
  color: #1A4D3A;
  background: #f5f5f5;
}

.chart-tab.active {
  color: #1A4D3A;
  font-weight: 600;
  border-bottom-color: #1A4D3A;
  background: transparent;
}

.chart-view-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding: 0;
  border-bottom: 2px solid #DDD;
}

.chart-view-tab {
  padding: 12px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  position: relative;
}

.chart-view-tab:hover {
  color: #1A4D3A;
  background: #f5f5f5;
}

.chart-view-tab.active {
  color: #1A4D3A;
  font-weight: 600;
  border-bottom-color: #1A4D3A;
  background: transparent;
}

.data-type-selector {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.data-type-selector label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.data-type-selector input[type="radio"] {
  cursor: pointer;
  accent-color: #1A4D3A;
}

.chart-wrapper-container {
  width: 100% !important;
  min-height: 500px;
  height: 600px;
  max-height: 800px;
  position: relative;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
}

@media (max-width: 768px) {
  .chart-wrapper-container {
    min-height: 400px;
    max-height: 500px;
  }
}
</style>
