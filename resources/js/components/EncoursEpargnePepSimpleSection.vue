<template>
  <div class="encours-epargne-pep-simple-section">
    <div class="section-header">
      <h2 class="section-title">{{ getSectionTitle }} - {{ getPeriodTitle() }}</h2>
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

    <!-- Tableau hiérarchique Encours Épargne (PEP et SIMPLE) -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Objectif</th>
              <th v-if="isCombinedView">EPARGNE M</th>
              <th v-if="isCombinedView">EPARGNE M1</th>
              <th v-if="!isCombinedView && showColumn('mEnoursProjet')">EPARGNE PROJET M</th>
              <th v-if="!isCombinedView && showColumn('mEnours')">EPARGNE M</th>
              <th v-if="!isCombinedView && showColumn('m1Enours')">EPARGNE M1</th>
              <th v-if="!isCombinedView && showColumn('m1EnoursProjet')">EPARGNE PROJET M1</th>
              <th>TRO</th>
              <th>Variation</th>
              <th>Dette rattachée</th>
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
              <td><strong>{{ formatNumber(getObjectiveForLevel('territoire')) }}</strong></td>
              <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneM('territoire')) }}</strong></td>
              <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneM1('territoire')) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('mEnoursProjet')"><strong>{{ formatNumber((territoireTotal.mEnoursProjet || 0)) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('mEnours')"><strong>{{ formatNumber(territoireTotal.mEnours) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('m1Enours')"><strong>{{ formatNumber(territoireTotal.m1Enours) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('m1EnoursProjet')"><strong>{{ formatNumber((territoireTotal.m1EnoursProjet || 0)) }}</strong></td>
              <td><strong>{{ formatPercent(getTROForLevel('territoire')) }}</strong></td>
              <td :class="getVariationClass(getVariationForLevel('territoire'))"><strong>{{ formatVariation(getVariationForLevel('territoire')) }}</strong></td>
              <td><strong>{{ formatNumber(isCombinedView ? getCombinedTotal('territoire', 'detteRattachee') : getTerritoireTotal('detteRattachee')) }}</strong></td>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections['TERRITOIRE']">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <tr v-if="territoryKey !== 'grand_compte' && hasTerritoryData(territory)" class="level-2-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <td><strong>{{ formatNumber(getObjectiveForTerritory(territory)) }}</strong></td>
                  <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneMForTerritory(territory)) }}</strong></td>
                  <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneM1ForTerritory(territory)) }}</strong></td>
                  <td v-if="!isCombinedView && showColumn('mEnoursProjet')"><strong>{{ formatNumber(getTerritoryTotal(territory, 'mEnoursProjet')) }}</strong></td>
                  <td v-if="!isCombinedView && showColumn('mEnours')"><strong>{{ formatNumber(getTerritoryTotal(territory, 'mEnours')) }}</strong></td>
                  <td v-if="!isCombinedView && showColumn('m1Enours')"><strong>{{ formatNumber(getTerritoryTotal(territory, 'm1Enours')) }}</strong></td>
                  <td v-if="!isCombinedView && showColumn('m1EnoursProjet')"><strong>{{ formatNumber(getTerritoryTotal(territory, 'm1EnoursProjet')) }}</strong></td>
                  <td><strong>{{ formatPercent(getTROForTerritory(territory)) }}</strong></td>
                  <td :class="getVariationClass(getVariationForTerritory(territory))"><strong>{{ formatVariation(getVariationForTerritory(territory)) }}</strong></td>
                  <td><strong>{{ formatNumber(isCombinedView ? getCombinedTotalForTerritory(territory, 'detteRattachee') : getTerritoryTotal(territory, 'detteRattachee')) }}</strong></td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <tr 
                    v-for="agency in territory.agencies.filter(a => hasAgencyData(a))" 
                    :key="agency.name" 
                    class="level-3-row"
                    :class="{ 'selected-agency': selectedAgency && selectedAgency.name === agency.name && selectedAgency.category === 'TERRITOIRE' && selectedAgency.zone === territoryKey }"
                    @click="selectAgency({ name: agency.name, category: 'TERRITOIRE', zone: territoryKey })"
                  >
                    <td class="level-3">{{ getAgencyName(agency) }}</td>
                    <td>{{ formatNumber(getObjectiveForAgency(agency)) }}</td>
                    <td v-if="isCombinedView">{{ formatNumber(getCombinedEpargneMForAgency(agency)) }}</td>
                    <td v-if="isCombinedView">{{ formatNumber(getCombinedEpargneM1ForAgency(agency)) }}</td>
                    <td v-if="!isCombinedView && showColumn('mEnoursProjet')">{{ formatNumber(getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET')) }}</td>
                    <td v-if="!isCombinedView && showColumn('mEnours')">{{ formatNumber(getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE')) }}</td>
                    <td v-if="!isCombinedView && showColumn('m1Enours')">{{ formatNumber(getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE')) }}</td>
                    <td v-if="!isCombinedView && showColumn('m1EnoursProjet')">{{ formatNumber(getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET')) }}</td>
                    <td>{{ formatPercent(getTROForAgency(agency)) }}</td>
                    <td :class="getVariationClass(getVariationForAgency(agency))">{{ formatVariation(getVariationForAgency(agency)) }}</td>
                    <td>{{ formatNumber(isCombinedView ? getCombinedDetteRattacheeForAgency(agency) : (getEncoursValue(agency, 'DETTE_RATTACHEE') || agency.detteRattachee || 0)) }}</td>
                  </tr>
                </template>
              </template>
            </template>

            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte" class="level-3-row">
              <td class="level-3">GRAND COMPTE</td>
              <td>{{ formatNumber(getObjectiveForGrandCompte()) }}</td>
              <td v-if="isCombinedView">{{ formatNumber((grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0)) }}</td>
              <td v-if="isCombinedView">{{ formatNumber((grandCompte.M1_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (grandCompte.M1_ENCOURS_COMPTE_EPARGNE || 0)) }}</td>
              <td v-if="!isCombinedView && showColumn('mEnoursProjet')">{{ formatNumber(grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0) }}</td>
              <td v-if="!isCombinedView && showColumn('mEnours')">{{ formatNumber(grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0) }}</td>
              <td v-if="!isCombinedView && showColumn('m1Enours')">{{ formatNumber(grandCompte.M1_ENCOURS_COMPTE_EPARGNE || 0) }}</td>
              <td v-if="!isCombinedView && showColumn('m1EnoursProjet')">{{ formatNumber(grandCompte.M1_ENCOURS_COMPTE_EPARGNE_PROJET || 0) }}</td>
              <td>{{ formatPercent(getTROForGrandCompte()) }}</td>
              <td :class="getVariationClass(getVariationForGrandCompte())">{{ formatVariation(getVariationForGrandCompte()) }}</td>
              <td>{{ formatNumber(isCombinedView ? getCombinedDetteRattacheeForGrandCompte() : (grandCompte.DETTE_RATTACHEE || grandCompte.detteRattachee || 0)) }}</td>
            </tr>

            <!-- Ligne TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ formatNumber(getObjectiveForLevel('total')) }}</strong></td>
              <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneM('total')) }}</strong></td>
              <td v-if="isCombinedView"><strong>{{ formatNumber(getCombinedEpargneM1('total')) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('mEnoursProjet')"><strong>{{ formatNumber(getGrandTotal('mEnoursProjet')) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('mEnours')"><strong>{{ formatNumber(getGrandTotal('mEnours')) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('m1Enours')"><strong>{{ formatNumber(getGrandTotal('m1Enours')) }}</strong></td>
              <td v-if="!isCombinedView && showColumn('m1EnoursProjet')"><strong>{{ formatNumber(getGrandTotal('m1EnoursProjet')) }}</strong></td>
              <td><strong>{{ formatPercent(getTROForLevel('total')) }}</strong></td>
              <td :class="getVariationClass(getVariationForLevel('total'))"><strong>{{ formatVariation(getVariationForLevel('total')) }}</strong></td>
              <td><strong>{{ formatNumber(isCombinedView ? getCombinedTotal('total', 'detteRattachee') : getGrandTotal('detteRattachee')) }}</strong></td>
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
          :dataType="'encours_epargne_pep_simple'" 
          :tableData="performanceTableData"
        />
      </div>
    </div>
    <div v-else class="chart-evolution-section">
      <h3 class="chart-section-title">Évolution des {{ getSectionTitle }}</h3>
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
  name: 'EncoursEpargnePepSimpleSection',
  components: {
    PythonChart,
    AgencyPerformanceSection
  },
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    },
    filterType: {
      type: String,
      default: 'epargne-pep-simple' // 'epargne-simple', 'epargne-pep-simple', 'epargne-projet'
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
      selectedDataType: 'epargne_pep_simple',
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
    filterType() {
      // Réinitialiser les sélections quand on change de filtre
      this.selectedAgency = null;
      this.expandedSections = {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      };
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
        TERRITOIRE: {}
      };
    },
    filteredHierarchicalData() {
      if (!this.selectedZone) {
        return this.hierarchicalData;
      }
      
      const filtered = {
        TERRITOIRE: {}
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
    isCombinedView() {
      // Vue combinée : additionner PEP + SIMPLE
      return !this.filterType || this.filterType === 'epargne-pep-simple';
    },
    territoireTotal() {
      const hierarchicalData = this.filteredHierarchicalData || {};
      let total = {
        mEnoursProjet: 0,
        mEnours: 0,
        m1Enours: 0,
        m1EnoursProjet: 0,
        encoursTotalM: 0,
        encoursTotalM1: 0
      };
      
      if (hierarchicalData.TERRITOIRE) {
        Object.entries(hierarchicalData.TERRITOIRE).forEach(([territoryKey, territory]) => {
          if (territoryKey !== 'grand_compte' && territory && territory.agencies) {
            territory.agencies.forEach(agency => {
              total.mEnoursProjet += parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
              total.mEnours += parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
              total.m1Enours += parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE') || 0);
              total.m1EnoursProjet += parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
              total.encoursTotalM += parseFloat(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M') || 0);
              total.encoursTotalM1 += parseFloat(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M_1') || 0);
            });
          }
        });
      }
      
      return total;
    },
    grandCompte() {
      const hierarchicalData = this.filteredHierarchicalData || {};
      if (hierarchicalData.TERRITOIRE && hierarchicalData.TERRITOIRE.grand_compte) {
        const grandCompte = hierarchicalData.TERRITOIRE.grand_compte;
        if (grandCompte.agencies && grandCompte.agencies.length > 0) {
          return {
            M_ENCOURS_COMPTE_EPARGNE_PROJET: this.getTerritoryTotal(grandCompte, 'mEnoursProjet'),
            M_ENCOURS_COMPTE_EPARGNE: this.getTerritoryTotal(grandCompte, 'mEnours'),
            M1_ENCOURS_COMPTE_EPARGNE: this.getTerritoryTotal(grandCompte, 'm1Enours'),
            M1_ENCOURS_COMPTE_EPARGNE_PROJET: this.getTerritoryTotal(grandCompte, 'm1EnoursProjet'),
            ENCOURS_TOTAL_M: this.getTerritoryTotal(grandCompte, 'encoursTotalM')
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
      // Vérifier que les données correspondent aux labels selon le filtre
      const expectedLength = (!this.filterType || this.filterType === 'epargne-pep-simple') ? 5 : 3;
      return this.chartLabels.length > 0 && 
             this.chartCurrentData.length > 0 && 
             this.chartCurrentData.length === this.chartLabels.length &&
             this.chartCurrentData.length === expectedLength;
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
      
      return {
        type: 'total',
        name: 'Total'
      };
    },
    chartTitle() {
      const level = this.activeLevel;
      return `Évolution - ${level.name}`;
    },
    getSectionTitle() {
      if (!this.filterType) {
        return 'Encours Épargne (PEP et SIMPLE)';
      }
      if (this.filterType === 'epargne-simple') {
        return 'Encours Épargne Simple';
      } else if (this.filterType === 'epargne-projet') {
        return 'Encours Épargne Projet';
      } else {
        return 'Encours Épargne (PEP et SIMPLE)';
      }
    },
    chartLabels() {
      // Ajuster les labels selon le filtre
      if (!this.filterType || this.filterType === 'epargne-pep-simple') {
        // 'epargne-pep-simple' : afficher les 5 variables
        return ['M ENCOURS COMPTE EPARGNE PROJET', 'M ENCOURS COMPTE EPARGNE', 'M1 ENCOURS COMPTE EPARGNE', 'M1 ENCOURS COMPTE EPARGNE PROJET', 'ENCOURS_TOTAL_M'];
      } else if (this.filterType === 'epargne-simple') {
        return ['M1 ENCOURS COMPTE EPARGNE', 'M ENCOURS COMPTE EPARGNE', 'ENCOURS_TOTAL_M'];
      } else if (this.filterType === 'epargne-projet') {
        return ['M ENCOURS COMPTE EPARGNE PROJET', 'M1 ENCOURS COMPTE EPARGNE PROJET', 'ENCOURS_TOTAL_M'];
      }
      // Par défaut, retourner toutes les colonnes
      return ['M ENCOURS COMPTE EPARGNE PROJET', 'M ENCOURS COMPTE EPARGNE', 'M1 ENCOURS COMPTE EPARGNE', 'M1 ENCOURS COMPTE EPARGNE PROJET', 'ENCOURS_TOTAL_M'];
    },
    chartCurrentData() {
      const level = this.activeLevel;
      let data = [];
      
      const normalizeValue = (value) => {
        const num = parseFloat(value);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      };
      
      // Fonction pour obtenir les valeurs selon le filtre
      const getValuesFromAgency = (agency) => {
        if (!this.filterType || this.filterType === 'epargne-pep-simple') {
          // 'epargne-pep-simple' : toutes les valeurs
          return [
            normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET')),
            normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE')),
            normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE')),
            normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET')),
            normalizeValue(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M'))
          ];
        } else if (this.filterType === 'epargne-simple') {
          return [
            normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE')),
            normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE')),
            normalizeValue(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M'))
          ];
        } else if (this.filterType === 'epargne-projet') {
          return [
            normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET')),
            normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET')),
            normalizeValue(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M'))
          ];
        }
        // Par défaut, retourner toutes les valeurs
        return [
          normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET')),
          normalizeValue(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE')),
          normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE')),
          normalizeValue(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET')),
          normalizeValue(this.getEncoursValue(agency, 'ENCOURS_TOTAL_M'))
        ];
      };
      
      if (level.type === 'agency') {
        // Niveau Agence : données de l'agence sélectionnée
        const zoneData = this.hierarchicalData[level.category]?.[level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        if (agency) {
          data = getValuesFromAgency(agency);
        } else {
          const terr = this.hierarchicalData.TERRITOIRE;
          if (terr) {
            for (const tk of Object.keys(terr)) {
              if (tk === 'grand_compte') continue;
              const z = terr[tk];
              const foundAgency = z?.agencies?.find(a => this.getAgencyName(a) === level.name);
              if (foundAgency) {
                data = getValuesFromAgency(foundAgency);
                break;
              }
            }
          }
        }
        // Si toujours pas de données, retourner des zéros selon le filtre
        if (data.length === 0) {
          const expectedLength = (!this.filterType || this.filterType === 'epargne-pep-simple') ? 5 : 3;
          data = new Array(expectedLength).fill(0);
        }
      } else if (level.type === 'zone') {
        // Niveau Zone : total du territoire
        const zoneData = this.hierarchicalData[level.category]?.[level.zone];
        if (zoneData) {
          if (this.filterType === 'epargne-simple') {
            data = [
              normalizeValue(this.getTerritoryTotal(zoneData, 'm1Enours')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'mEnours')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'encoursTotalM'))
            ];
          } else if (this.filterType === 'epargne-projet') {
            data = [
              normalizeValue(this.getTerritoryTotal(zoneData, 'mEnoursProjet')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'm1EnoursProjet')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'encoursTotalM'))
            ];
          } else {
            // Par défaut (epargne-pep-simple) : toutes les colonnes
            data = [
              normalizeValue(this.getTerritoryTotal(zoneData, 'mEnoursProjet')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'mEnours')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'm1Enours')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'm1EnoursProjet')),
              normalizeValue(this.getTerritoryTotal(zoneData, 'encoursTotalM'))
            ];
          }
        } else {
          const expectedLength = (!this.filterType || this.filterType === 'epargne-pep-simple') ? 5 : 3;
          data = new Array(expectedLength).fill(0);
        }
      } else if (level.type === 'category') {
        if (level.category === 'TERRITOIRE') {
          if (this.filterType === 'epargne-simple') {
            data = [
              normalizeValue(this.territoireTotal.m1Enours),
              normalizeValue(this.territoireTotal.mEnours),
              normalizeValue(this.territoireTotal.encoursTotalM)
            ];
          } else if (this.filterType === 'epargne-projet') {
            data = [
              normalizeValue(this.territoireTotal.mEnoursProjet || 0),
              normalizeValue(this.territoireTotal.m1EnoursProjet || 0),
              normalizeValue(this.territoireTotal.encoursTotalM)
            ];
          } else {
            data = [
              normalizeValue(this.territoireTotal.mEnoursProjet || 0),
              normalizeValue(this.territoireTotal.mEnours),
              normalizeValue(this.territoireTotal.m1Enours),
              normalizeValue(this.territoireTotal.m1EnoursProjet || 0),
              normalizeValue(this.territoireTotal.encoursTotalM)
            ];
          }
        } else {
          const expectedLength = (!this.filterType || this.filterType === 'epargne-pep-simple') ? 5 : 3;
          data = new Array(expectedLength).fill(0);
        }
      } else {
        // Niveau Total : total général
        if (this.filterType === 'epargne-simple') {
          data = [
            normalizeValue(this.getGrandTotal('m1Enours')),
            normalizeValue(this.getGrandTotal('mEnours')),
            normalizeValue(this.getGrandTotal('encoursTotalM'))
          ];
        } else if (this.filterType === 'epargne-projet') {
          data = [
            normalizeValue(this.getGrandTotal('mEnoursProjet')),
            normalizeValue(this.getGrandTotal('m1EnoursProjet')),
            normalizeValue(this.getGrandTotal('encoursTotalM'))
          ];
        } else {
          data = [
            normalizeValue(this.getGrandTotal('mEnoursProjet')),
            normalizeValue(this.getGrandTotal('mEnours')),
            normalizeValue(this.getGrandTotal('m1Enours')),
            normalizeValue(this.getGrandTotal('m1EnoursProjet')),
            normalizeValue(this.getGrandTotal('encoursTotalM'))
          ];
        }
      }
      
      return data.map(v => normalizeValue(v));
    },
    currentChartData() {
      const labels = this.chartLabels;
      const current = this.chartCurrentData;
      
      let title = `${this.chartTitle} - Évolution des Encours`;
      let ylabel = 'Encours (FCFA)';
      
      const normalizedCurrent = current.map(v => {
        const num = parseFloat(v);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      });
      
      if (this.selectedChartType === 'bar') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title,
          xlabel: 'Variables',
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
    showColumn(column) {
      // Détermine quelles colonnes afficher selon le filtre
      if (!this.filterType || this.filterType === 'epargne-pep-simple') {
        // 'epargne-pep-simple' : afficher toutes les colonnes (mais on utilise isCombinedView pour les combiner)
        return true;
      } else if (this.filterType === 'epargne-simple') {
        // Afficher seulement M et M1 ENCOURS COMPTE EPARGNE (sans PROJET)
        return column === 'mEnours' || column === 'm1Enours';
      } else if (this.filterType === 'epargne-projet') {
        // Afficher seulement M et M1 ENCOURS COMPTE EPARGNE PROJET
        return column === 'mEnoursProjet' || column === 'm1EnoursProjet';
      }
      return true;
    },
    // Méthodes pour calculer les sommes PEP + SIMPLE
    getCombinedEpargneMForAgency(agency) {
      if (!agency) return 0;
      const projetM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
      const simpleM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
      return projetM + simpleM;
    },
    getCombinedEpargneM1ForAgency(agency) {
      if (!agency) return 0;
      const projetM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
      const simpleM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE') || 0);
      return projetM1 + simpleM1;
    },
    getCombinedEpargneMForTerritory(territory) {
      if (!territory || !territory.agencies) return 0;
      let total = 0;
      territory.agencies.forEach(agency => {
        total += this.getCombinedEpargneMForAgency(agency);
      });
      return total;
    },
    getCombinedEpargneM1ForTerritory(territory) {
      if (!territory || !territory.agencies) return 0;
      let total = 0;
      territory.agencies.forEach(agency => {
        total += this.getCombinedEpargneM1ForAgency(agency);
      });
      return total;
    },
    getCombinedEpargneM(level) {
      if (level === 'territoire') {
        return (this.territoireTotal.mEnoursProjet || 0) + (this.territoireTotal.mEnours || 0);
      } else if (level === 'total') {
        const territoireM = (this.territoireTotal.mEnoursProjet || 0) + (this.territoireTotal.mEnours || 0);
        const grandCompteM = this.grandCompte ?
          ((this.grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (this.grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0)) : 0;
        return territoireM + grandCompteM;
      }
      return 0;
    },
    getCombinedEpargneM1(level) {
      if (level === 'territoire') {
        return (this.territoireTotal.m1EnoursProjet || 0) + (this.territoireTotal.m1Enours || 0);
      } else if (level === 'total') {
        const territoireM1 = (this.territoireTotal.m1EnoursProjet || 0) + (this.territoireTotal.m1Enours || 0);
        const grandCompteM1 = this.grandCompte ?
          ((this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE || 0)) : 0;
        return territoireM1 + grandCompteM1;
      }
      return 0;
    },
    // Méthodes pour obtenir l'objectif selon le filtre (SIMPLE, PROJET ou combiné)
    getObjectiveForAgency(agency) {
      if (!agency) return 0;
      if (this.isCombinedView) {
        return this.getCombinedObjectiveForAgency(agency);
      } else if (this.filterType === 'epargne-simple') {
        return parseFloat(agency.objectif_epargne_simple || agency.OBJECTIF_EPARGNE_SIMPLE || 0);
      } else if (this.filterType === 'epargne-projet') {
        return parseFloat(agency.objectif_epargne_projet || agency.OBJECTIF_EPARGNE_PROJET || 0);
      }
      return parseFloat(agency.objectif || agency.OBJECTIF || 0);
    },
    getObjectiveForTerritory(territory) {
      if (!territory || !territory.agencies) return 0;
      let total = 0;
      territory.agencies.forEach(agency => {
        total += this.getObjectiveForAgency(agency);
      });
      return total;
    },
    getObjectiveForLevel(level) {
      if (level === 'territoire') {
        let total = 0;
        Object.values(this.filteredHierarchicalData.TERRITOIRE || {}).forEach(territory => {
          if (territory && territory.agencies) {
            total += this.getObjectiveForTerritory(territory);
          }
        });
        return total;
      } else if (level === 'total') {
        const territoire = this.getObjectiveForLevel('territoire');
        const grandCompte = this.getObjectiveForGrandCompte();
        return territoire + grandCompte;
      }
      return 0;
    },
    getObjectiveForGrandCompte() {
      if (!this.grandCompte) return 0;
      if (this.isCombinedView) {
        return this.getCombinedObjectiveForGrandCompte();
      } else if (this.filterType === 'epargne-simple') {
        return parseFloat(this.grandCompte.OBJECTIF_EPARGNE_SIMPLE || this.grandCompte.objectif_epargne_simple || 0);
      } else if (this.filterType === 'epargne-projet') {
        return parseFloat(this.grandCompte.OBJECTIF_EPARGNE_PROJET || this.grandCompte.objectif_epargne_projet || 0);
      }
      return parseFloat(this.grandCompte.OBJECTIF || this.grandCompte.objectif || 0);
    },
    // Méthodes pour calculer le TRO selon le filtre
    getTROForAgency(agency) {
      if (!agency) return 0;
      if (this.isCombinedView) {
        return this.getCombinedTROForAgency(agency);
      }
      
      const objectif = this.getObjectiveForAgency(agency);
      let epargneM = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
      } else if (this.filterType === 'epargne-projet') {
        epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
      }
      
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getTROForTerritory(territory) {
      if (!territory) return 0;
      if (this.isCombinedView) {
        return this.getCombinedTROForTerritory(territory);
      }
      
      const objectif = this.getObjectiveForTerritory(territory);
      let epargneM = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = this.getTerritoryTotal(territory, 'mEnours');
      } else if (this.filterType === 'epargne-projet') {
        epargneM = this.getTerritoryTotal(territory, 'mEnoursProjet');
      }
      
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getTROForLevel(level) {
      if (this.isCombinedView) {
        return this.getCombinedTRO(level);
      }
      
      const objectif = this.getObjectiveForLevel(level);
      let epargneM = 0;
      
      if (level === 'territoire') {
        if (this.filterType === 'epargne-simple') {
          epargneM = this.territoireTotal.mEnours || 0;
        } else if (this.filterType === 'epargne-projet') {
          epargneM = this.territoireTotal.mEnoursProjet || 0;
        }
      } else if (level === 'total') {
        if (this.filterType === 'epargne-simple') {
          epargneM = this.getGrandTotal('mEnours');
        } else if (this.filterType === 'epargne-projet') {
          epargneM = this.getGrandTotal('mEnoursProjet');
        }
      }
      
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getTROForGrandCompte() {
      if (!this.grandCompte) return 0;
      if (this.isCombinedView) {
        return this.getCombinedTROForGrandCompte();
      }
      
      const objectif = this.getObjectiveForGrandCompte();
      let epargneM = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = parseFloat(this.grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0);
      } else if (this.filterType === 'epargne-projet') {
        epargneM = parseFloat(this.grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0);
      }
      
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    // Méthodes pour calculer la variation selon le filtre
    getVariationForAgency(agency) {
      if (!agency) return 0;
      if (this.isCombinedView) {
        return this.getCombinedVariationForAgency(agency);
      }
      
      let epargneM = 0;
      let epargneM1 = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
        epargneM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE') || 0);
      } else if (this.filterType === 'epargne-projet') {
        epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
        epargneM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
      }
      
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getVariationForTerritory(territory) {
      if (!territory) return 0;
      if (this.isCombinedView) {
        return this.getCombinedVariationForTerritory(territory);
      }
      
      let epargneM = 0;
      let epargneM1 = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = this.getTerritoryTotal(territory, 'mEnours');
        epargneM1 = this.getTerritoryTotal(territory, 'm1Enours');
      } else if (this.filterType === 'epargne-projet') {
        epargneM = this.getTerritoryTotal(territory, 'mEnoursProjet');
        epargneM1 = this.getTerritoryTotal(territory, 'm1EnoursProjet');
      }
      
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getVariationForLevel(level) {
      if (this.isCombinedView) {
        return this.getCombinedVariation(level);
      }
      
      let epargneM = 0;
      let epargneM1 = 0;
      
      if (level === 'territoire') {
        if (this.filterType === 'epargne-simple') {
          epargneM = this.territoireTotal.mEnours || 0;
          epargneM1 = this.territoireTotal.m1Enours || 0;
        } else if (this.filterType === 'epargne-projet') {
          epargneM = this.territoireTotal.mEnoursProjet || 0;
          epargneM1 = this.territoireTotal.m1EnoursProjet || 0;
        }
      } else if (level === 'total') {
        if (this.filterType === 'epargne-simple') {
          epargneM = this.getGrandTotal('mEnours');
          epargneM1 = this.getGrandTotal('m1Enours');
        } else if (this.filterType === 'epargne-projet') {
          epargneM = this.getGrandTotal('mEnoursProjet');
          epargneM1 = this.getGrandTotal('m1EnoursProjet');
        }
      }
      
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getVariationForGrandCompte() {
      if (!this.grandCompte) return 0;
      if (this.isCombinedView) {
        return this.getCombinedVariationForGrandCompte();
      }
      
      let epargneM = 0;
      let epargneM1 = 0;
      
      if (this.filterType === 'epargne-simple') {
        epargneM = parseFloat(this.grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0);
        epargneM1 = parseFloat(this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE || 0);
      } else if (this.filterType === 'epargne-projet') {
        epargneM = parseFloat(this.grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0);
        epargneM1 = parseFloat(this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE_PROJET || 0);
      }
      
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    // Méthodes pour calculer les valeurs combinées (PEP + SIMPLE) pour objectif, TRO, variation, dette
    getCombinedObjectiveForAgency(agency) {
      if (!agency) return 0;
      // L'objectif combiné est déjà calculé dans mergeObjectivesWithOracleData
      // Utiliser d'abord l'objectif combiné, sinon additionner les objectifs individuels
      const objectifCombined = parseFloat(agency.objectif || agency.OBJECTIF || 0);
      if (objectifCombined > 0) {
        return objectifCombined;
      }
      // Sinon, additionner les objectifs individuels
      const objectifSimple = parseFloat(agency.objectif_epargne_simple || agency.OBJECTIF_EPARGNE_SIMPLE || 0);
      const objectifProjet = parseFloat(agency.objectif_epargne_projet || agency.OBJECTIF_EPARGNE_PROJET || 0);
      return objectifSimple + objectifProjet;
    },
    getCombinedTROForAgency(agency) {
      if (!agency) return 0;
      const objectif = this.getCombinedObjectiveForAgency(agency);
      const epargneM = this.getCombinedEpargneMForAgency(agency);
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getCombinedVariationForAgency(agency) {
      if (!agency) return 0;
      const epargneM = this.getCombinedEpargneMForAgency(agency);
      const epargneM1 = this.getCombinedEpargneM1ForAgency(agency);
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getCombinedDetteRattacheeForAgency(agency) {
      if (!agency) return 0;
      const detteSimple = parseFloat(this.getEncoursValue(agency, 'DETTE_RATTACHEE') || agency.detteRattachee || 0);
      const detteProjet = parseFloat(agency.detteRattacheeProjet || agency.DETTE_RATTACHEE_PROJET || 0);
      return detteSimple + detteProjet;
    },
    getCombinedTotalForTerritory(territory, field) {
      if (!territory || !territory.agencies) return 0;
      let total = 0;
      territory.agencies.forEach(agency => {
        if (field === 'objectif') {
          total += this.getCombinedObjectiveForAgency(agency);
        } else if (field === 'detteRattachee') {
          total += this.getCombinedDetteRattacheeForAgency(agency);
        }
      });
      return total;
    },
    getCombinedTROForTerritory(territory) {
      if (!territory) return 0;
      const objectif = this.getCombinedTotalForTerritory(territory, 'objectif');
      const epargneM = this.getCombinedEpargneMForTerritory(territory);
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getCombinedVariationForTerritory(territory) {
      if (!territory) return 0;
      const epargneM = this.getCombinedEpargneMForTerritory(territory);
      const epargneM1 = this.getCombinedEpargneM1ForTerritory(territory);
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getCombinedTotal(level, field) {
      if (level === 'territoire') {
        return this.getTerritoireTotal(field);
      } else if (level === 'total') {
        const territoire = this.getTerritoireTotal(field);
        const grandCompte = field === 'objectif' ? this.getCombinedObjectiveForGrandCompte() :
                           field === 'detteRattachee' ? this.getCombinedDetteRattacheeForGrandCompte() : 0;
        return territoire + grandCompte;
      }
      return 0;
    },
    getCombinedTRO(level) {
      if (level === 'territoire') {
        const objectif = this.getCombinedTotal('territoire', 'objectif');
        const epargneM = this.getCombinedEpargneM('territoire');
        if (objectif > 0) {
          // L'objectif est en millions de FCFA, convertir en FCFA
          const objectifEnFCFA = objectif * 1000000;
          return (epargneM / objectifEnFCFA) * 100;
        }
        return 0;
      } else if (level === 'total') {
        const objectif = this.getCombinedTotal('total', 'objectif');
        const epargneM = this.getCombinedEpargneM('total');
        if (objectif > 0) {
          // L'objectif est en millions de FCFA, convertir en FCFA
          const objectifEnFCFA = objectif * 1000000;
          return (epargneM / objectifEnFCFA) * 100;
        }
        return 0;
      }
      return 0;
    },
    getCombinedVariation(level) {
      if (level === 'territoire') {
        const epargneM = this.getCombinedEpargneM('territoire');
        const epargneM1 = this.getCombinedEpargneM1('territoire');
        if (epargneM1 > 0) {
          return ((epargneM - epargneM1) / epargneM1) * 100;
        }
        return 0;
      } else if (level === 'total') {
        const epargneM = this.getCombinedEpargneM('total');
        const epargneM1 = this.getCombinedEpargneM1('total');
        if (epargneM1 > 0) {
          return ((epargneM - epargneM1) / epargneM1) * 100;
        }
        return 0;
      }
      return 0;
    },
    getCombinedObjectiveForGrandCompte() {
      if (!this.grandCompte) return 0;
      const objectifSimple = parseFloat(this.grandCompte.OBJECTIF_EPARGNE_SIMPLE || this.grandCompte.objectif_epargne_simple || this.grandCompte.objectif || 0);
      const objectifProjet = parseFloat(this.grandCompte.OBJECTIF_EPARGNE_PROJET || this.grandCompte.objectif_epargne_projet || 0);
      const objectifCombined = parseFloat(this.grandCompte.OBJECTIF || this.grandCompte.objectif || 0);
      return objectifCombined > 0 ? objectifCombined : (objectifSimple + objectifProjet);
    },
    getCombinedTROForGrandCompte() {
      if (!this.grandCompte) return 0;
      const objectif = this.getCombinedObjectiveForGrandCompte();
      const epargneM = (this.grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (this.grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0);
      if (objectif > 0) {
        // L'objectif est en millions de FCFA, convertir en FCFA
        const objectifEnFCFA = objectif * 1000000;
        return (epargneM / objectifEnFCFA) * 100;
      }
      return 0;
    },
    getCombinedVariationForGrandCompte() {
      if (!this.grandCompte) return 0;
      const epargneM = (this.grandCompte.M_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (this.grandCompte.M_ENCOURS_COMPTE_EPARGNE || 0);
      const epargneM1 = (this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE_PROJET || 0) + (this.grandCompte.M1_ENCOURS_COMPTE_EPARGNE || 0);
      if (epargneM1 > 0) {
        return ((epargneM - epargneM1) / epargneM1) * 100;
      }
      return 0;
    },
    getCombinedDetteRattacheeForGrandCompte() {
      if (!this.grandCompte) return 0;
      const detteSimple = parseFloat(this.grandCompte.DETTE_RATTACHEE || this.grandCompte.detteRattachee || 0);
      const detteProjet = parseFloat(this.grandCompte.DETTE_RATTACHEE_PROJET || this.grandCompte.detteRattacheeProjet || 0);
      return detteSimple + detteProjet;
    },
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
    getAgencyName(agency) {
      if (!agency) return 'Agence non identifiée';
      const name = agency.name || agency.BRANCH_NAME || agency.AGENCE || agency.NOM_AGENCE || agency.agence || agency.branch_name || '';
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
          let csv = 'Période,Encours\n';
          
          for (let i = 0; i < labels.length; i++) {
            const value = current[i] || 0;
            csv += `"${labels[i]}",${value}\n`;
          }
          
          const BOM = '\uFEFF';
          const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          const fileName = `donnees-encours-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.csv`;
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
          const fileName = `graphique-encours-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedChartType}-${new Date().toISOString().split('T')[0]}.${extension}`;
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
    getEncoursValue(data, field) {
      if (!data) return 0;
      
      const fieldMap = {
        'M_ENCOURS_COMPTE_EPARGNE_PROJET': ['M_ENCOURS_COMPTE_EPARGNE_PROJET', 'm_enours_compte_epargne_projet', 'mEnoursCompteEpargneProjet'],
        'M_ENCOURS_COMPTE_EPARGNE': ['M_ENCOURS_COMPTE_EPARGNE', 'm_enours_compte_epargne', 'mEnoursCompteEpargne'],
        'M1_ENCOURS_COMPTE_EPARGNE': ['M1_ENCOURS_COMPTE_EPARGNE', 'm1_enours_compte_epargne', 'm1EnoursCompteEpargne'],
        'M1_ENCOURS_COMPTE_EPARGNE_PROJET': ['M1_ENCOURS_COMPTE_EPARGNE_PROJET', 'm1_enours_compte_epargne_projet', 'm1EnoursCompteEpargneProjet'],
        'ENCOURS_TOTAL_M': ['ENCOURS_TOTAL_M', 'encours_total_m', 'encoursTotalM', 'ENCOURSTOTALM'],
        'ENCOURS_TOTAL_M_1': ['ENCOURS_TOTAL_M_1', 'encours_total_m_1', 'encoursTotalM1', 'ENCOURSTOTALM1']
      };
      
      const possibleFields = fieldMap[field] || [field];
      
      for (const possibleField of possibleFields) {
        if (data[possibleField] !== undefined && data[possibleField] !== null) {
          return parseFloat(data[possibleField]) || 0;
        }
      }
      
      return 0;
    },
    getTerritoryTotal(territory, field) {
      if (!territory || !territory.agencies) return 0;
      
      let total = 0;
      territory.agencies.forEach(agency => {
        const fieldMap = {
          'mEnoursProjet': 'M_ENCOURS_COMPTE_EPARGNE_PROJET',
          'mEnours': 'M_ENCOURS_COMPTE_EPARGNE',
          'm1Enours': 'M1_ENCOURS_COMPTE_EPARGNE',
          'm1EnoursProjet': 'M1_ENCOURS_COMPTE_EPARGNE_PROJET',
          'encoursTotalM': 'ENCOURS_TOTAL_M',
          'encoursTotalM1': 'ENCOURS_TOTAL_M_1',
          'objectif': 'OBJECTIF',
          'tro': 'TRO',
          'variation': 'VARIATION',
          'detteRattachee': 'DETTE_RATTACHEE'
        };
        
        const mappedField = fieldMap[field] || field;
        if (field === 'objectif' || field === 'detteRattachee') {
          total += parseFloat(this.getEncoursValue(agency, mappedField) || agency[mappedField.toLowerCase()] || 0);
        } else if (field === 'tro' || field === 'variation') {
          // Pour TRO et Variation, on prend la valeur directement de l'agence
          total += parseFloat(agency[mappedField] || agency[mappedField.toLowerCase()] || 0);
        } else {
          total += parseFloat(this.getEncoursValue(agency, mappedField) || 0);
        }
      });
      
      return total;
    },
    getTerritoireTotal(field) {
      let total = 0;
      Object.values(this.filteredHierarchicalData.TERRITOIRE || {}).forEach(territory => {
        if (territory && territory.agencies) {
          total += this.getTerritoryTotal(territory, field);
        }
      });
      return total;
    },
    getGrandTotal(field) {
      let total = this.getTerritoireTotal(field);
      if (this.grandCompte) {
        const fieldMap = {
          'mEnoursProjet': 'M_ENCOURS_COMPTE_EPARGNE_PROJET',
          'mEnours': 'M_ENCOURS_COMPTE_EPARGNE',
          'm1Enours': 'M1_ENCOURS_COMPTE_EPARGNE',
          'm1EnoursProjet': 'M1_ENCOURS_COMPTE_EPARGNE_PROJET',
          'encoursTotalM': 'ENCOURS_TOTAL_M',
          'encoursTotalM1': 'ENCOURS_TOTAL_M_1',
          'objectif': 'OBJECTIF',
          'tro': 'TRO',
          'variation': 'VARIATION',
          'detteRattachee': 'DETTE_RATTACHEE'
        };
        const mappedField = fieldMap[field] || field;
        if (field === 'objectif' || field === 'detteRattachee') {
          total += parseFloat(this.grandCompte[mappedField] || this.grandCompte[mappedField.toLowerCase()] || 0);
        } else if (field === 'tro' || field === 'variation') {
          total += parseFloat(this.grandCompte[mappedField] || this.grandCompte[mappedField.toLowerCase()] || 0);
        } else {
          total += parseFloat(this.grandCompte[mappedField] || 0);
        }
      }
      return total;
    },
    formatPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return `${num.toFixed(0)}%`;
    },
    formatVariation(value) {
      if (value === null || value === undefined) return '-';
      return value >= 0 ? `+${this.formatNumber(value)}` : this.formatNumber(value);
    },
    getVariationClass(value) {
      if (value === null || value === undefined) return '';
      return value >= 0 ? 'positive' : 'negative';
    },
    hasAgencyData(agency) {
      if (!agency) return false;
      
      // Vérifier si l'agence a au moins une donnée non nulle
      if (this.isCombinedView) {
        const epargneM = this.getCombinedEpargneMForAgency(agency);
        const epargneM1 = this.getCombinedEpargneM1ForAgency(agency);
        const detteRattachee = this.getCombinedDetteRattacheeForAgency(agency);
        return epargneM > 0 || epargneM1 > 0 || detteRattachee > 0;
      } else {
        // Pour les vues non combinées, vérifier selon le type de filtre
        if (this.filterType === 'epargne-simple') {
          const epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
          const epargneM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE') || 0);
          const detteRattachee = parseFloat(this.getEncoursValue(agency, 'DETTE_RATTACHEE') || agency.detteRattachee || 0);
          return epargneM > 0 || epargneM1 > 0 || detteRattachee > 0;
        } else if (this.filterType === 'epargne-projet') {
          const epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
          const epargneM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
          const detteRattachee = parseFloat(this.getEncoursValue(agency, 'DETTE_RATTACHEE') || agency.detteRattachee || 0);
          return epargneM > 0 || epargneM1 > 0 || detteRattachee > 0;
        } else {
          // Pour epargne-pep-simple, vérifier toutes les valeurs
          const epargneM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE') || 0);
          const epargneM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE') || 0);
          const epargneProjetM = parseFloat(this.getEncoursValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
          const epargneProjetM1 = parseFloat(this.getEncoursValue(agency, 'M1_ENCOURS_COMPTE_EPARGNE_PROJET') || 0);
          const detteRattachee = parseFloat(this.getEncoursValue(agency, 'DETTE_RATTACHEE') || agency.detteRattachee || 0);
          return epargneM > 0 || epargneM1 > 0 || epargneProjetM > 0 || epargneProjetM1 > 0 || detteRattachee > 0;
        }
      }
    },
    hasTerritoryData(territory) {
      if (!territory || !territory.agencies || !Array.isArray(territory.agencies)) return false;
      // Un territoire a des données s'il a au moins une agence avec des données
      return territory.agencies.some(agency => this.hasAgencyData(agency));
    },
    hasServicePointData(servicePoint) {
      if (!servicePoint || !servicePoint.agencies || !Array.isArray(servicePoint.agencies)) return false;
      // Un point de service a des données s'il a au moins une agence avec des données
      return servicePoint.agencies.some(agency => this.hasAgencyData(agency));
    },
    async fetchDataFromOracle() {
      this.loading = true;
      try {
        const params = {
          period: this.selectedPeriod,
          zone: this.selectedZone || null,
          type: 'epargne-pep-simple' // Toujours utiliser 'epargne-pep-simple' pour récupérer toutes les données
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

        const response = await window.axios.get('/api/oracle/data/encours', { params });
        
        let data = null;
        
        console.log('Réponse API complète:', response);
        console.log('response.data:', response.data);
        
        if (response.data && response.data.data) {
          data = response.data.data;
        } else if (response.data) {
          data = response.data;
        }
        
        console.log('Données extraites:', data);
        console.log('data.hierarchicalData:', data?.hierarchicalData);
        
        if (data && data.hierarchicalData) {
          this.hierarchicalDataFromBackend = data.hierarchicalData;
          console.log('Données hiérarchiques assignées:', this.hierarchicalDataFromBackend);
        } else if (data && data.TERRITOIRE) {
          this.hierarchicalDataFromBackend = {
            TERRITOIRE: data.TERRITOIRE || {}
          };
          console.log('Données hiérarchiques assignées (format direct):', this.hierarchicalDataFromBackend);
        } else {
          console.warn('Aucune donnée hiérarchique trouvée dans la réponse');
          this.hierarchicalDataFromBackend = {
            TERRITOIRE: {}
          };
        }
        
        // Charger les objectifs depuis Laravel et les fusionner avec les données Oracle
        await this.loadObjectives();
      } catch (error) {
        this.hierarchicalDataFromBackend = {
          TERRITOIRE: {}
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
        // Charger les objectifs même en cas d'erreur partielle
        try {
          await this.loadObjectives();
        } catch (error) {
          console.warn('⚠️ Erreur lors du chargement des objectifs:', error);
        }
        this.loading = false;
      }
    },
    async loadObjectives() {
      // Charger les objectifs EPARGNE_SIMPLE et EPARGNE_PROJET depuis l'API Laravel
      try {
        const token = localStorage.getItem('token');
        const objectiveTypes = ['EPARGNE_SIMPLE', 'EPARGNE_PROJET'];
        const allObjectives = {};
        
        for (const type of objectiveTypes) {
          const params = {
            type: type,
            period: this.selectedPeriod === 'week' ? 'month' : this.selectedPeriod,
            year: this.selectedYear
          };
          
          // Ajouter les paramètres selon la période
          if (this.selectedPeriod === 'month') {
            params.month = this.selectedMonth;
          } else if (this.selectedPeriod === 'quarter') {
            params.quarter = Math.ceil(this.selectedMonth / 3);
          } else if (this.selectedPeriod === 'week') {
            if (this.selectedDate) {
              const date = new Date(this.selectedDate);
              params.month = date.getMonth() + 1;
            }
          }
          
          console.log(`📊 Chargement des objectifs ${type} avec params:`, params);
          
          const response = await window.axios.get('/api/objectives', {
            params: params,
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.data && response.data.success && response.data.data) {
            const objectives = Array.isArray(response.data.data) ? response.data.data : [response.data.data];
            console.log(`✅ Objectifs ${type} chargés:`, objectives.length);
            
            // Créer un map des objectifs par agency_code et agency_name
            objectives.forEach(obj => {
              const agencyCode = (obj.agency_code || '').toString().trim();
              const agencyName = (obj.agency_name || '').toString().trim();
              const value = obj.value || 0;
              
              if (agencyCode) {
                if (!allObjectives[agencyCode]) {
                  allObjectives[agencyCode] = {};
                }
                allObjectives[agencyCode][type] = value;
              }
              if (agencyName) {
                const normalizedName = agencyName.toUpperCase().trim();
                if (!allObjectives[normalizedName]) {
                  allObjectives[normalizedName] = {};
                }
                allObjectives[normalizedName][type] = value;
              }
            });
          }
        }
        
        console.log('📊 Tous les objectifs épargne chargés:', allObjectives);
        
        // Fusionner les objectifs avec les données Oracle
        this.mergeObjectivesWithOracleData(allObjectives);
      } catch (error) {
        console.warn('⚠️ Erreur lors du chargement des objectifs:', error);
      }
    },
    mergeObjectivesWithOracleData(allObjectives) {
      // Fusionner les objectifs avec les agences dans les territoires
      if (this.hierarchicalDataFromBackend && this.hierarchicalDataFromBackend.TERRITOIRE) {
        Object.keys(this.hierarchicalDataFromBackend.TERRITOIRE).forEach(territoryKey => {
          const territory = this.hierarchicalDataFromBackend.TERRITOIRE[territoryKey];
          if (territory.agencies && Array.isArray(territory.agencies)) {
            territory.agencies.forEach(agency => {
              const agencyCode = (agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '').toString().trim();
              const agencyName = (agency.name || agency.AGENCE || agency.NOM_AGENCE || '').toString().trim();
              
              // Chercher les objectifs par code d'agence d'abord
              let objectives = null;
              if (agencyCode && allObjectives[agencyCode]) {
                objectives = allObjectives[agencyCode];
                console.log(`✅ Objectifs trouvés par code pour ${agencyName} (${agencyCode}):`, objectives);
              } else if (agencyName) {
                const normalizedName = agencyName.toUpperCase().trim();
                if (allObjectives[normalizedName]) {
                  objectives = allObjectives[normalizedName];
                  console.log(`✅ Objectifs trouvés par nom pour ${agencyName}:`, objectives);
                }
              }
              
              if (objectives) {
                // Stocker les objectifs individuels
                agency.objectif_epargne_simple = objectives.EPARGNE_SIMPLE || 0;
                agency.objectif_epargne_projet = objectives.EPARGNE_PROJET || 0;
                agency.OBJECTIF_EPARGNE_SIMPLE = objectives.EPARGNE_SIMPLE || 0;
                agency.OBJECTIF_EPARGNE_PROJET = objectives.EPARGNE_PROJET || 0;
                // Somme des objectifs EPARGNE_SIMPLE et EPARGNE_PROJET
                const totalObjective = (objectives.EPARGNE_SIMPLE || 0) + (objectives.EPARGNE_PROJET || 0);
                agency.objectif = totalObjective;
                agency.OBJECTIF = totalObjective;
              }
            });
          }
        });
      }
      
      // Fusionner avec le grand compte (dans la structure hiérarchique)
      if (this.hierarchicalDataFromBackend && this.hierarchicalDataFromBackend.TERRITOIRE && this.hierarchicalDataFromBackend.TERRITOIRE.grand_compte) {
        const grandCompte = this.hierarchicalDataFromBackend.TERRITOIRE.grand_compte;
        if (grandCompte.agencies && Array.isArray(grandCompte.agencies) && grandCompte.agencies.length > 0) {
          grandCompte.agencies.forEach(agency => {
            const agencyCode = (agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '').toString().trim();
            const agencyName = (agency.name || agency.AGENCE || agency.NOM_AGENCE || '').toString().trim();
            
            let objectives = null;
            if (agencyCode && allObjectives[agencyCode]) {
              objectives = allObjectives[agencyCode];
            } else if (agencyName) {
              const normalizedName = agencyName.toUpperCase().trim();
              if (allObjectives[normalizedName]) {
                objectives = allObjectives[normalizedName];
              }
            }
            
            if (objectives) {
              // Stocker les objectifs individuels
              agency.objectif_epargne_simple = objectives.EPARGNE_SIMPLE || 0;
              agency.objectif_epargne_projet = objectives.EPARGNE_PROJET || 0;
              agency.OBJECTIF_EPARGNE_SIMPLE = objectives.EPARGNE_SIMPLE || 0;
              agency.OBJECTIF_EPARGNE_PROJET = objectives.EPARGNE_PROJET || 0;
              // Somme des objectifs EPARGNE_SIMPLE et EPARGNE_PROJET
              const totalObjective = (objectives.EPARGNE_SIMPLE || 0) + (objectives.EPARGNE_PROJET || 0);
              agency.objectif = totalObjective;
              agency.OBJECTIF = totalObjective;
            }
          });
        }
      }
      
      // Stocker aussi les objectifs pour grandCompte au niveau racine (si disponible)
      if (this.grandCompte) {
        // Chercher les objectifs pour GRAND COMPTE
        const grandCompteName = 'GRAND COMPTE';
        const normalizedName = grandCompteName.toUpperCase().trim();
        if (allObjectives[normalizedName]) {
          const objectives = allObjectives[normalizedName];
          this.grandCompte.objectif_epargne_simple = objectives.EPARGNE_SIMPLE || 0;
          this.grandCompte.objectif_epargne_projet = objectives.EPARGNE_PROJET || 0;
          this.grandCompte.OBJECTIF_EPARGNE_SIMPLE = objectives.EPARGNE_SIMPLE || 0;
          this.grandCompte.OBJECTIF_EPARGNE_PROJET = objectives.EPARGNE_PROJET || 0;
          const totalObjective = (objectives.EPARGNE_SIMPLE || 0) + (objectives.EPARGNE_PROJET || 0);
          this.grandCompte.objectif = totalObjective;
          this.grandCompte.OBJECTIF = totalObjective;
        }
      }
    },
    loadDataForPeriod() {
      this.hierarchicalDataFromBackend = null;
      this.expandedSections = {
        TERRITOIRE: false,
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
.encours-epargne-pep-simple-section {
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
  min-width: 800px;
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

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
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
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.data-type-selector label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.data-type-select {
  flex: 1;
  max-width: 400px;
  padding: 8px 12px;
  border: 1px solid #DDD;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.data-type-select:hover {
  border-color: #1A4D3A;
}

.data-type-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.1);
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
.positive {
  color: #10B981;
  font-weight: 600;
}

.negative {
  color: #EF4444;
  font-weight: 600;
}
</style>
