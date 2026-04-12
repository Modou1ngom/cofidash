<template>
  <div class="client-section">
    <div class="section-header">
      <h2 class="section-title">Client - {{ getPeriodTitle() }}</h2>
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
        <p>🔄 Chargement des données ...</p>
      </div>
      <div v-if="errorMessage" class="error-message">
        <p>⚠️ {{ errorMessage }}</p>
      </div>
      <div class="kpi-row">
        <KPICard :label="kpiLabels.current" :value="globalResult.mois" />
        <KPICard :label="kpiLabels.previous" :value="globalResult.mois1" />
        <KPICard label="Evolution" :value="globalResult.evolution" percentage />
        <KPICard :label="kpiLabels.difference" :value="computedDifference" />
      </div>
    </div>

    <!-- Tableau hiérarchique par niveaux -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Objectif</th>
              <th>Nouveaux Clients <br>{{ tablePeriodLabels.previous }}</th>
              <th>Nouveaux Clients <br>{{ tablePeriodLabels.current }}</th>
              <th>Variation <br>(Nouveaux Clients)</th>
              <th>TRO</th>
              <th>Taux de croissance <br>(Nouveaux Clients)</th>
              <th>Frais d'ouverture de compte <br>{{ tablePeriodLabels.previous }}</th>
              <th>Frais d'ouverture de compte <br>{{ tablePeriodLabels.current }}</th>
              <th>Variation <br>(Frais d'ouverture de compte)</th>
              <th>Taux de croissance <br>(Frais d'ouverture de compte)</th>
              
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr v-if="Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length > 0" class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>{{ formatNumber(territoireTotal.objectif) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.nouveauxClientsM1) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.nouveauxClientsM) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.variationClients)">
                <strong>{{ formatVariation(territoireTotal.variationClients) }}</strong>
              </td>
              <td :class="getAchievementClass(territoireTotal.atteinte)">
                <strong>{{ formatPercent(territoireTotal.atteinte) }}</strong>
              </td>
              <td :class="getGrowthClass(territoireTotal.tauxCroissanceClients)">
                <strong>{{ formatGrowthRate(territoireTotal.tauxCroissanceClients) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(territoireTotal.fraisM1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.fraisM) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.variationFrais)">
                <strong>{{ formatVariation(territoireTotal.variationFrais) }}</strong>
              </td>
              <td :class="getGrowthClass(territoireTotal.tauxCroissanceFrais)">
                <strong>{{ formatGrowthRate(territoireTotal.tauxCroissanceFrais) }}</strong>
              </td>
              
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
                  <td><strong>{{ formatNumber(territory.totals.objectif) }}</strong></td>
                  <td><strong>{{ formatNumber(territory.totals.nouveauxClientsM1) }}</strong></td>
                  <td><strong>{{ formatNumber(territory.totals.nouveauxClientsM) }}</strong></td>
                  <td :class="getVariationClass(territory.totals.variationClients)">
                    <strong>{{ formatVariation(territory.totals.variationClients) }}</strong>
                  </td>
                  <td :class="getAchievementClass(territory.totals.atteinte)">
                    <strong>{{ formatPercent(territory.totals.atteinte) }}</strong>
                  </td>
                  <td :class="getGrowthClass(territory.totals.tauxCroissanceClients)">
                    <strong>{{ formatGrowthRate(territory.totals.tauxCroissanceClients) }}</strong>
                  </td>
                  <td><strong>{{ formatCurrency(territory.totals.fraisM1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.fraisM) }}</strong></td>
                  <td :class="getVariationClass(territory.totals.variationFrais)">
                    <strong>{{ formatVariation(territory.totals.variationFrais) }}</strong>
                  </td>
                  <td :class="getGrowthClass(territory.totals.tauxCroissanceFrais)">
                    <strong>{{ formatGrowthRate(territory.totals.tauxCroissanceFrais) }}</strong>
                  </td>
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
                    <td>{{ formatNumber(agency.objectif || agency.OBJECTIF_CLIENT || 0) }}</td>
                    <td>{{ formatNumber(agency.nouveauxClientsM1) }}</td>
                    <td>{{ formatNumber(agency.nouveauxClientsM) }}</td>
                    <td :class="getVariationClass(agency.variationClients)">
                      {{ formatVariation(agency.variationClients) }}
                    </td>
                    <td :class="getAchievementClass(agency.atteinte || agency.TAUX_REALISATION || 0)">
                      {{ formatPercent(agency.atteinte || agency.TAUX_REALISATION || 0) }}
                    </td>
                    <td :class="getGrowthClass(agency.tauxCroissanceClients)">
                      {{ formatGrowthRate(agency.tauxCroissanceClients) }}
                    </td>
                    <td>{{ formatCurrency(agency.fraisM1) }}</td>
                    <td>{{ formatCurrency(agency.fraisM) }}</td>
                    <td :class="getVariationClass(agency.variationFrais)">
                      {{ formatVariation(agency.variationFrais) }}
                    </td>
                    <td :class="getGrowthClass(agency.tauxCroissanceFrais)">
                      {{ formatGrowthRate(agency.tauxCroissanceFrais) }}
                    </td>
                  </tr>
                </template>
              </template>

            </template>

            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte" class="level-3-row">
              <td class="level-3">GRAND COMPTE</td>
              <td>{{ formatNumber(grandCompte.objectif || 0) }}</td>
              <td>{{ formatNumber(grandCompte.nouveauxClientsM1) }}</td>
              <td>{{ formatNumber(grandCompte.nouveauxClientsM) }}</td>
              <td :class="getVariationClass(grandCompte.variationClients)">
                {{ formatVariation(grandCompte.variationClients) }}
              </td>
              <td :class="getAchievementClass(grandCompte.atteinte || 0)">
                {{ formatPercent(grandCompte.atteinte || 0) }}
              </td>
              <td :class="getGrowthClass(grandCompte.tauxCroissanceClients)">
                {{ formatGrowthRate(grandCompte.tauxCroissanceClients) }}
              </td>
              <td>{{ formatCurrency(grandCompte.fraisM1) }}</td>
              <td>{{ formatCurrency(grandCompte.fraisM) }}</td>
              <td :class="getVariationClass(grandCompte.variationFrais)">
                {{ formatVariation(grandCompte.variationFrais) }}
              </td>
              <td :class="getGrowthClass(grandCompte.tauxCroissanceFrais)">
                {{ formatGrowthRate(grandCompte.tauxCroissanceFrais) }}
              </td>
            </tr>

            <!-- Ligne TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ formatNumber(getGrandTotal('objectif')) }}</strong></td>
              <td><strong>{{ formatNumber(getGrandTotal('nouveauxClientsM1')) }}</strong></td>
              <td><strong>{{ formatNumber(getGrandTotal('nouveauxClientsM')) }}</strong></td>
              <td :class="getVariationClass(getGrandTotal('variationClients'))">
                <strong>{{ formatVariation(getGrandTotal('variationClients')) }}</strong>
              </td>
              <td :class="getAchievementClass(getGrandTotalAtteinte())">
                <strong>{{ formatPercent(getGrandTotalAtteinte()) }}</strong>
              </td>
              <td :class="getGrowthClass(getGrandTotalTauxCroissance('clients'))">
                <strong>{{ formatGrowthRate(getGrandTotalTauxCroissance('clients')) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(getGrandTotal('fraisM1')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('fraisM')) }}</strong></td>
              <td :class="getVariationClass(getGrandTotal('variationFrais'))">
                <strong>{{ formatVariation(getGrandTotal('variationFrais')) }}</strong>
              </td>
              <td :class="getGrowthClass(getGrandTotalTauxCroissance('frais'))">
                <strong>{{ formatGrowthRate(getGrandTotalTauxCroissance('frais')) }}</strong>
              </td>
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
      
      <!-- Sélecteur de données (Nouveaux Clients ou Frais) -->
      <div class="data-type-selector">
        <label>
          <input 
            type="radio" 
            value="clients" 
            v-model="selectedDataType"
            @change="updateChart"
          />
          Nouveaux Clients
        </label>
        <label>
          <input 
            type="radio" 
            value="frais" 
            v-model="selectedDataType"
            @change="updateChart"
          />
          Frais d'Ouverture
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
    <div v-else class="chart-evolution-section">
      <h3 class="chart-section-title">Évolution des Nouveaux Clients et Frais d'Ouverture</h3>
      <div class="chart-wrapper-container" style="display: flex; align-items: center; justify-content: center; color: #999;">
        <p>Chargement des données...</p>
      </div>
    </div>
  </div>
</template>

<script>
import KPICard from './KPICard.vue';
import PythonChart from './charts/PythonChart.vue';
import { ProfileManager, PERMISSIONS } from '../utils/profiles.js';

export default {
  name: 'ClientSection',
  components: {
    KPICard,
    PythonChart
  },
  computed: {
    canEditObjectives() {
      return ProfileManager.canEditObjectives();
    },
    canManageFinancial() {
      return ProfileManager.canManageFinancial();
    },
    isAdmin() {
      return ProfileManager.isAdmin();
    },
    canViewOnly() {
      return ProfileManager.getCurrentProfile() === 'EXPLOITATIONS';
    },
    kpiLabels() {
      if (this.selectedPeriod === 'week') {
        return {
          current: 'Résultat Global (Semaine)',
          previous: 'Résultat Global (Semaine-1)',
          difference: 'Différence'
        };
      } else if (this.selectedPeriod === 'month') {
        return {
          current: 'Résultat Global (Mois)',
          previous: 'Résultat Global (Mois-1)',
          difference: 'Différence'
        };
      } else if (this.selectedPeriod === 'year') {
        return {
          current: 'Résultat Global (Année)',
          previous: 'Résultat Global (Année-1)',
          difference: 'Différence'
        };
      }
      return {
        current: 'Résultat Global (Mois)',
        previous: 'Résultat Global (Mois-1)',
        difference: 'Différence'
      };
    },
    computedDifference() {
      // Calculer la différence dynamiquement
      return this.globalResult.mois - this.globalResult.mois1;
    },
    tablePeriodLabels() {
      if (this.selectedPeriod === 'week') {
        return {
          current: 'S',
          previous: 'S-1'
        };
      } else if (this.selectedPeriod === 'month') {
        return {
          current: 'M',
          previous: 'M-1'
        };
      } else if (this.selectedPeriod === 'year') {
        return {
          current: 'A',
          previous: 'A-1'
        };
      }
      return {
        current: 'M',
        previous: 'M-1'
      };
    },
    years() {
      const currentYear = new Date().getFullYear();
      const years = [];
      // Générer les 5 dernières années et les 2 prochaines
      for (let i = currentYear - 5; i <= currentYear + 2; i++) {
        years.push(i);
      }
      return years;
    },
    weeks() {
      const weeks = [];
      for (let i = 1; i <= 52; i++) {
        weeks.push({
          value: i,
          label: `Semaine ${i}`
        });
      }
      return weeks;
    },
    hierarchicalData() {
      // Utiliser les données hiérarchiques du backend si disponibles, sinon construire depuis territories
      if (this.hierarchicalDataFromBackend && typeof this.hierarchicalDataFromBackend === 'object') {
        try {
          // Calculer les totaux pour chaque territoire si pas déjà calculés
          const data = JSON.parse(JSON.stringify(this.hierarchicalDataFromBackend));
          if (data.TERRITOIRE && typeof data.TERRITOIRE === 'object' && data.TERRITOIRE !== null) {
            Object.keys(data.TERRITOIRE).forEach(key => {
              if (data.TERRITOIRE[key]) {
                // Filtrer les agences pour exclure "Inconnu"
                const agencies = data.TERRITOIRE[key].agencies || data.TERRITOIRE[key].data || [];
                data.TERRITOIRE[key].agencies = this.filterAgencies(agencies);
                if (!data.TERRITOIRE[key].totals) {
                  data.TERRITOIRE[key].totals = this.calculateZoneTotals(data.TERRITOIRE[key].agencies);
                }
              }
            });
          }
          return data;
        } catch (e) {
          console.warn('Erreur lors du traitement des données hiérarchiques:', e);
        }
      }
      
      // Construire depuis les territories pour compatibilité
      // S'assurer que territories existe
      if (!this.territories || typeof this.territories !== 'object') {
        return {
          TERRITOIRE: {}
        };
      }
      
      // Filtrer les agences pour chaque territoire
      const filteredDakarVille = this.filterAgencies((this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.agencies) || []);
      const filteredDakarBanlieue = this.filterAgencies((this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.agencies) || []);
      const filteredProvinceCentreSud = this.filterAgencies((this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.agencies) || []);
      const filteredProvinceNord = this.filterAgencies((this.territories.territoire_province_nord && this.territories.territoire_province_nord.agencies) || []);
      
      const data = {
        TERRITOIRE: {
          territoire_dakar_ville: {
            name: (this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.name) || 'TERRITOIRE DAKAR VILLE',
            agencies: filteredDakarVille,
            totals: this.calculateZoneTotals(filteredDakarVille)
          },
          territoire_dakar_banlieue: {
            name: (this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.name) || 'TERRITOIRE DAKAR BANLIEUE',
            agencies: filteredDakarBanlieue,
            totals: this.calculateZoneTotals(filteredDakarBanlieue)
          },
          territoire_province_centre_sud: {
            name: (this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.name) || 'TERRITOIRE PROVINCE CENTRE-SUD',
            agencies: filteredProvinceCentreSud,
            totals: this.calculateZoneTotals(filteredProvinceCentreSud)
          },
          territoire_province_nord: {
            name: (this.territories.territoire_province_nord && this.territories.territoire_province_nord.name) || 'TERRITOIRE PROVINCE NORD',
            agencies: filteredProvinceNord,
            totals: this.calculateZoneTotals(filteredProvinceNord)
          }
        }
      };
      
      return data;
    },
    filteredHierarchicalData() {
      // S'assurer que hierarchicalData existe et est un objet
      if (!this.hierarchicalData || typeof this.hierarchicalData !== 'object' || this.hierarchicalData === null) {
        return {
          TERRITOIRE: {}
        };
      }
      
      if (!this.selectedZone) {
        // Si aucune zone n'est sélectionnée, afficher tout
        return this.hierarchicalData;
      }
      
      // Filtrer selon la zone sélectionnée
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
    territoireTotal() {
      // Calculer le total de tous les territoires
      const t1 = this.calculateZoneTotals(this.territories.territoire_dakar_ville.agencies || []);
      const t2 = this.calculateZoneTotals(this.territories.territoire_dakar_banlieue.agencies || []);
      const t3 = this.calculateZoneTotals(this.territories.territoire_province_centre_sud.agencies || []);
      const t4 = this.calculateZoneTotals(this.territories.territoire_province_nord.agencies || []);
      
      const totalObjectif = t1.objectif + t2.objectif + t3.objectif + t4.objectif;
      const totalNouveauxClientsM = t1.nouveauxClientsM + t2.nouveauxClientsM + t3.nouveauxClientsM + t4.nouveauxClientsM;
      
      return {
        objectif: totalObjectif,
        nouveauxClientsM1: t1.nouveauxClientsM1 + t2.nouveauxClientsM1 + t3.nouveauxClientsM1 + t4.nouveauxClientsM1,
        nouveauxClientsM: totalNouveauxClientsM,
        variationClients: totalNouveauxClientsM - (t1.nouveauxClientsM1 + t2.nouveauxClientsM1 + t3.nouveauxClientsM1 + t4.nouveauxClientsM1),
        tauxCroissanceClients: this.calculateTotalGrowthRate(
          t1.nouveauxClientsM1 + t2.nouveauxClientsM1 + t3.nouveauxClientsM1 + t4.nouveauxClientsM1,
          totalNouveauxClientsM
        ),
        fraisM1: t1.fraisM1 + t2.fraisM1 + t3.fraisM1 + t4.fraisM1,
        fraisM: t1.fraisM + t2.fraisM + t3.fraisM + t4.fraisM,
        variationFrais: (t1.fraisM + t2.fraisM + t3.fraisM + t4.fraisM) - (t1.fraisM1 + t2.fraisM1 + t3.fraisM1 + t4.fraisM1),
        tauxCroissanceFrais: this.calculateTotalGrowthRate(
          t1.fraisM1 + t2.fraisM1 + t3.fraisM1 + t4.fraisM1,
          t1.fraisM + t2.fraisM + t3.fraisM + t4.fraisM
        ),
        atteinte: totalObjectif > 0 ? (totalNouveauxClientsM / totalObjectif) * 100 : null
      };
    },
    // Compatibilité avec l'ancien code
    corporateTotal() {
      return this.territoireTotal;
    },
    retailTotal() {
      return { nouveauxClientsM1: 0, nouveauxClientsM: 0, variationClients: 0, fraisM1: 0, fraisM: 0, variationFrais: 0, tauxCroissanceClients: 0, tauxCroissanceFrais: 0 };
    },
    grandCompte() {
      // Récupérer les données du grand compte depuis l'API ou retourner des valeurs vides
      // Chercher dans les données Oracle si elles existent
      // Vérifier avec includes() car le nom peut être "AGENCE GRAND COMPTE" ou "GRAND COMPTE"
      if (this.grandCompteData && this.grandCompteData.name && 
          this.grandCompteData.name.toUpperCase().includes('GRAND COMPTE')) {
        const data = this.grandCompteData;
        const variationClients = (data.nouveauxClientsM || 0) - (data.nouveauxClientsM1 || 0);
        const variationFrais = (data.fraisM || 0) - (data.fraisM1 || 0);
        const objectif = data.objectif || data.OBJECTIF_CLIENT || 0;
        const nouveauxClientsM = data.nouveauxClientsM || 0;
        return {
          objectif: objectif,
          nouveauxClientsM1: data.nouveauxClientsM1 || 0,
          nouveauxClientsM: nouveauxClientsM,
          variationClients: variationClients,
          tauxCroissanceClients: (data.nouveauxClientsM1 || 0) > 0 
            ? this.calculateTotalGrowthRate(data.nouveauxClientsM1, nouveauxClientsM) 
            : null,
          fraisM1: data.fraisM1 || 0,
          fraisM: data.fraisM || 0,
          variationFrais: variationFrais,
          tauxCroissanceFrais: (data.fraisM1 || 0) > 0 
            ? this.calculateTotalGrowthRate(data.fraisM1, data.fraisM) 
            : null,
          atteinte: objectif > 0 ? (nouveauxClientsM / objectif) * 100 : null
        };
      }
      
      // Retourner des valeurs vides par défaut
      return {
        objectif: 0,
        nouveauxClientsM1: 0,
        nouveauxClientsM: 0,
        variationClients: 0,
        tauxCroissanceClients: null,
        fraisM1: 0,
        fraisM: 0,
        variationFrais: 0,
        tauxCroissanceFrais: null,
        atteinte: null
      };
    },
    chartLabels() {
      // Générer les labels pour les 12 derniers mois
      const labels = [];
      const monthNames = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];
      const currentDate = new Date();
      for (let i = 11; i >= 0; i--) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
        labels.push(`${monthNames[date.getMonth()]} ${date.getFullYear()}`);
      }
      return labels;
    },
    hasChartData() {
      // Vérifier que les données sont disponibles
      return this.chartLabels.length > 0 && 
             this.chartCurrentData.length > 0 && 
             this.chartCurrentData.length === this.chartLabels.length;
    },
    activeLevel() {
      // Déterminer le niveau actif basé sur les sections expansées
      // Priorité : Agence sélectionnée > Zone expansée > Catégorie (CORPORATE/RETAIL) > Total
      
      // Vérifier si une agence est sélectionnée (priorité la plus haute)
      if (this.selectedAgency) {
        return {
          type: 'agency',
          category: this.selectedAgency.category,
          zone: this.selectedAgency.zone,
          name: this.selectedAgency.name
        };
      }
      
      // Vérifier si une zone est expansée
      for (const key in this.expandedSections) {
        if (key.startsWith('CORPORATE_') && this.expandedSections[key]) {
          const zoneKey = key.replace('CORPORATE_', '');
          return {
            type: 'zone',
            category: 'CORPORATE',
            zone: zoneKey,
            name: this.hierarchicalData.CORPORATE[zoneKey]?.name || `Zone ${zoneKey}`
          };
        }
        if (key.startsWith('RETAIL_') && this.expandedSections[key]) {
          const zoneKey = key.replace('RETAIL_', '');
          return {
            type: 'zone',
            category: 'RETAIL',
            zone: zoneKey,
            name: this.hierarchicalData.RETAIL[zoneKey]?.name || `Zone ${zoneKey}`
          };
        }
      }
      
      // Vérifier si une catégorie est expansée
      if (this.expandedSections.CORPORATE) {
        return {
          type: 'category',
          category: 'CORPORATE',
          name: 'CORPORATE'
        };
      }
      if (this.expandedSections.RETAIL) {
        return {
          type: 'category',
          category: 'RETAIL',
          name: 'RETAIL'
        };
      }
      
      // Par défaut, afficher le total
      return {
        type: 'total',
        name: 'Total'
      };
    },
    chartTitle() {
      const level = this.activeLevel;
      return `Évolution - ${level.name}`;
    },
    chartCurrentData() {
      const level = this.activeLevel;
      let baseValue;
      
      // Calculer la valeur de base selon le niveau
      if (level.type === 'agency') {
        // Données pour une agence spécifique
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        baseValue = agency?.nouveauxClientsM || 0;
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        baseValue = zoneData?.totals?.nouveauxClientsM || 0;
      } else if (level.type === 'category') {
        if (level.category === 'CORPORATE') {
          baseValue = this.corporateTotal.nouveauxClientsM;
        } else {
          baseValue = this.retailTotal.nouveauxClientsM;
        }
      } else {
        // Total
        baseValue = this.getGrandTotal('nouveauxClientsM') || 719;
      }
      
      // Générer des données d'exemple avec une progression réaliste
      const variations = [0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.08, 1.02, 0.98, 1.03, 1.07, 1.12];
      
      const data = [];
      for (let i = 0; i < 12; i++) {
        data.push(Math.round(baseValue * variations[i]));
      }
      
      return data;
    },
    chartPreviousData() {
      const level = this.activeLevel;
      let baseValue;
      
      // Calculer la valeur de base selon le niveau
      if (level.type === 'agency') {
        // Données pour une agence spécifique
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        baseValue = agency?.nouveauxClientsM1 || 0;
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        baseValue = zoneData?.totals?.nouveauxClientsM1 || 0;
      } else if (level.type === 'category') {
        if (level.category === 'CORPORATE') {
          baseValue = this.corporateTotal.nouveauxClientsM1;
        } else {
          baseValue = this.retailTotal.nouveauxClientsM1;
        }
      } else {
        // Total
        baseValue = this.getGrandTotal('nouveauxClientsM1') || 598;
      }
      
      // Même pattern de variation mais décalé
      const variations = [0.82, 0.88, 0.93, 0.97, 1.02, 1.07, 1.05, 0.99, 0.96, 1.01, 1.05, 1.09];
      
      const data = [];
      for (let i = 0; i < 12; i++) {
        data.push(Math.round(baseValue * variations[i]));
      }
      
      return data;
    },
    chartFraisCurrentData() {
      const level = this.activeLevel;
      let baseValue;
      
      // Calculer la valeur de base selon le niveau pour les frais
      if (level.type === 'agency') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        baseValue = agency?.fraisM || 0;
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        baseValue = zoneData?.totals?.fraisM || 0;
      } else if (level.type === 'category') {
        if (level.category === 'CORPORATE') {
          baseValue = this.corporateTotal.fraisM;
        } else {
          baseValue = this.retailTotal.fraisM;
        }
      } else {
        // Total
        baseValue = this.getGrandTotal('fraisM') || 10387;
      }
      
      // Générer des données d'exemple avec une progression réaliste
      const variations = [0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.08, 1.02, 0.98, 1.03, 1.07, 1.12];
      
      const data = [];
      for (let i = 0; i < 12; i++) {
        data.push(Math.round(baseValue * variations[i]));
      }
      
      return data;
    },
    currentChartData() {
      // Préparer les données selon le type de données sélectionné (clients ou frais)
      const labels = this.chartLabels;
      const current = this.selectedDataType === 'clients' ? this.chartCurrentData : this.chartFraisCurrentData;
      const previous = this.selectedDataType === 'clients' ? this.chartPreviousData : this.chartFraisPreviousData;
      const ylabel = this.selectedDataType === 'clients' ? 'Nombre de clients' : 'Montant (FCFA)';
      const title = `${this.chartTitle} - ${this.selectedDataType === 'clients' ? 'Nouveaux Clients' : 'Frais d\'Ouverture'}`;
      
      // Formater les données selon le type de graphique
      if (this.selectedChartType === 'bar') {
        // Pour les barres, utiliser seulement les données actuelles
        return {
          labels: labels,
          values: current, // Le controller attend 'values' pour les barres
          title: title,
          xlabel: 'Période',
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'area') {
        // Pour les aires (timeseries), utiliser la période actuelle
        // Le controller attend 'values' pour timeseries
        return {
          labels: labels,
          values: current,
          title: title,
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'pie') {
        // Pour le graphique circulaire, utiliser les données actuelles
        // Les labels représentent les catégories (mois) et values les montants
        return {
          labels: labels,
          values: current,
          title: title
        };
      } else {
        // Pour les lignes (evolution), utiliser current et previous
        return {
          labels: labels,
          current: current,
          previous: previous,
          title: title,
          ylabel: ylabel
        };
      }
    },
    chartFraisPreviousData() {
      const level = this.activeLevel;
      let baseValue;
      
      // Calculer la valeur de base selon le niveau pour les frais
      if (level.type === 'agency') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        baseValue = agency?.fraisM1 || 0;
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        baseValue = zoneData?.totals?.fraisM1 || 0;
      } else if (level.type === 'category') {
        if (level.category === 'CORPORATE') {
          baseValue = this.corporateTotal.fraisM1;
        } else {
          baseValue = this.retailTotal.fraisM1;
        }
      } else {
        // Total
        baseValue = this.getGrandTotal('fraisM1') || 8300;
      }
      
      // Même pattern de variation mais décalé
      const variations = [0.82, 0.88, 0.93, 0.97, 1.02, 1.07, 1.05, 0.99, 0.96, 1.01, 1.05, 1.09];
      
      const data = [];
      for (let i = 0; i < 12; i++) {
        data.push(Math.round(baseValue * variations[i]));
      }
      
      return data;
    },
    updateChart() {
      // Force la mise à jour du graphique quand on change le type de données
      this.$nextTick(() => {
        // Le graphique se mettra à jour automatiquement grâce au watch sur chartData
      });
    }
  },
  data() {
    const now = new Date();
    // Calculer le numéro de semaine actuel
    const getWeekNumber = (date) => {
      const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
      const dayNum = d.getUTCDay() || 7;
      d.setUTCDate(d.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    };
    return {
      loading: false, // Indicateur de chargement des données Oracle
      errorMessage: null, // Message d'erreur à afficher
      selectedZone: null,
      selectedPeriod: 'month', // 'week', 'month', 'year'
      selectedDate: (() => {
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      })(),
      selectedWeek: getWeekNumber(now),
      selectedMonth: now.getMonth() + 1, // Mois en cours (1-12)
      selectedYear: now.getFullYear(), // Année en cours
      expandedSections: {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      },
      hierarchicalDataFromBackend: null,
      selectedAgency: null, // { name: 'POINT E', category: 'CORPORATE', zone: 'zone1' }
      selectedChartType: 'line', // 'line', 'bar', 'area', 'pie'
      selectedDataType: 'clients', // 'clients' ou 'frais'
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      globalResult: {
        mois: 0,
        mois1: 0,
        evolution: 0
      },
      grandCompteData: null, // Données du grand compte depuis l'API Oracle
      territories: {
        territoire_dakar_ville: {
          name: 'TERRITOIRE DAKAR VILLE',
          agencies: []
        },
        territoire_dakar_banlieue: {
          name: 'TERRITOIRE DAKAR BANLIEUE',
          agencies: []
        },
        territoire_province_centre_sud: {
          name: 'TERRITOIRE PROVINCE CENTRE-SUD',
          agencies: []
        },
        territoire_province_nord: {
          name: 'TERRITOIRE PROVINCE NORD',
          agencies: []
        }
      },
      // Compatibilité avec l'ancien format
      corporateZones: {
        zone1: {
          name: 'TERRITOIRE DAKAR VILLE',
          agencies: []
        },
        zone2: {
          name: 'TERRITOIRE PROVINCE CENTRE-SUD',
          agencies: []
        }
      },
      retailZones: {
        zone1: {
          name: 'TERRITOIRE DAKAR BANLIEUE',
          agencies: []
        },
        zone2: {
          name: 'TERRITOIRE PROVINCE NORD',
          agencies: []
        }
      }
    }
  },
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    }
  },
  mounted() {
    // Charger les données depuis Oracle au montage du composant
    this.fetchDataFromOracle();
  },
  watch: {
    selectedZoneProp(newVal) {
      this.selectedZone = newVal;
      // Recharger les données si la zone change
      this.fetchDataFromOracle();
      // Ouvrir automatiquement les sections qui contiennent des données pour la zone sélectionnée
      this.$nextTick(() => {
        if (newVal) {
          // Ouvrir CORPORATE si la zone contient des données CORPORATE
          if (this.hierarchicalData.CORPORATE[newVal]) {
            this.expandedSections.CORPORATE = true;
            this.expandedSections[`CORPORATE_${newVal}`] = true;
          }
          // Ouvrir RETAIL si la zone contient des données RETAIL
          if (this.hierarchicalData.RETAIL[newVal]) {
            this.expandedSections.RETAIL = true;
            this.expandedSections[`RETAIL_${newVal}`] = true;
          }
        } else {
          // Si aucune zone n'est sélectionnée, fermer toutes les sections
          this.expandedSections.CORPORATE = false;
          this.expandedSections.RETAIL = false;
          Object.keys(this.expandedSections).forEach(key => {
            if (key.startsWith('CORPORATE_') || key.startsWith('RETAIL_')) {
              this.expandedSections[key] = false;
            }
          });
        }
      });
    },
    selectedPeriod(newVal) {
      // Si on passe à la période "week", initialiser la date si nécessaire
      if (newVal === 'week' && !this.selectedDate) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        this.selectedDate = `${year}-${month}-${day}`;
        this.updateWeekFromDate();
      }
      this.loadDataForPeriod();
    },
    selectedDate(newVal, oldVal) {
      console.log('📅 selectedDate a changé:', { oldVal, newVal, period: this.selectedPeriod });
      this.updateWeekFromDate();
      this.loadDataForPeriod();
    },
    selectedWeek() {
      this.loadDataForPeriod();
    },
    selectedMonth() {
      this.loadDataForPeriod();
    },
    selectedYear() {
      this.loadDataForPeriod();
    },
    expandedSections: {
      handler() {
        // Forcer la mise à jour du graphique quand les sections changent
        this.$nextTick(() => {
          // Le graphique se mettra à jour automatiquement grâce à la computed property activeLevel
        });
      },
      deep: true
    }
  },
  methods: {
    getZoneName(zone) {
      // Support des anciennes clés pour compatibilité
      if (zone === 'zone1') return 'TERRITOIRE DAKAR VILLE';
      if (zone === 'zone2') return 'TERRITOIRE PROVINCE CENTRE-SUD';
      // Support des nouvelles clés
      if (this.territories[zone]) {
        return this.territories[zone].name;
      }
      return zone || '';
    },
    getTerritoryName(zone) {
      // Mapping des territoires
      const territoryMap = {
        'zone1': 'TERRITOIRE DAKAR VILLE',
        'zone2': 'TERRITOIRE PROVINCE CENTRE-SUD',
        'territoire_dakar_ville': 'TERRITOIRE DAKAR VILLE',
        'territoire_dakar_banlieue': 'TERRITOIRE DAKAR BANLIEUE',
        'territoire_province_centre_sud': 'TERRITOIRE PROVINCE CENTRE-SUD',
        'territoire_province_nord': 'TERRITOIRE PROVINCE NORD'
      };
      return territoryMap[zone] || zone || '';
    },
    getAgenciesForZone(zone) {
      // Récupérer les agences depuis les territoires
      const agencies = [];
      
      // Support des anciennes clés pour compatibilité
      if (zone === 'zone1') {
        if (this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.agencies) {
          agencies.push(...this.territories.territoire_dakar_ville.agencies);
        }
        if (this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.agencies) {
          agencies.push(...this.territories.territoire_dakar_banlieue.agencies);
        }
      } else if (zone === 'zone2') {
        if (this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.agencies) {
          agencies.push(...this.territories.territoire_province_centre_sud.agencies);
        }
        if (this.territories.territoire_province_nord && this.territories.territoire_province_nord.agencies) {
          agencies.push(...this.territories.territoire_province_nord.agencies);
        }
      } else if (this.territories[zone] && this.territories[zone].agencies) {
        agencies.push(...this.territories[zone].agencies);
      }
      
      // Compatibilité avec l'ancien format
      if (this.corporateZones[zone] && this.corporateZones[zone].agencies) {
        agencies.push(...this.corporateZones[zone].agencies);
      }
      if (this.retailZones[zone] && this.retailZones[zone].agencies) {
        agencies.push(...this.retailZones[zone].agencies);
      }
      
      return agencies;
    },
    formatNumber(num) {
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    formatCurrency(num) {
      return new Intl.NumberFormat('fr-FR', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      }).format(num);
    },
    formatVariation(value) {
      if (value === null || value === undefined) return '-';
      return value >= 0 ? `+${this.formatNumber(value)}` : this.formatNumber(value);
    },
    formatGrowthRate(value) {
      if (value === null || value === undefined) return '-';
      const formatted = value.toFixed(2);
      return value >= 0 ? `▲${formatted}%` : `▼${Math.abs(value).toFixed(2)}%`;
    },
    getVariationClass(value) {
      if (value === null || value === undefined) return '';
      return value >= 0 ? 'positive' : 'negative';
    },
    getGrowthClass(value) {
      if (value === null || value === undefined) return '';
      return value >= 0 ? 'positive' : 'negative';
    },
    formatPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return `${num.toFixed(0)}%`;
    },
    getAchievementClass(value) {
      if (value === null || value === undefined || isNaN(value)) return '';
      if (value >= 100) return 'achievement-high';
      if (value >= 70) return 'achievement-medium';
      return 'achievement-low';
    },
    getAgencyName(agency) {
      // Essayer plusieurs champs possibles pour le nom d'agence
      const name = agency.name || agency.AGENCE || agency.NOM_AGENCE || agency.agence || '';
      
      // Si le nom est vide ou "Inconnu", essayer d'utiliser le code d'agence
      if (!name || name.trim() === '' || name.toUpperCase() === 'INCONNU' || name.toUpperCase() === 'UNKNOWN') {
        const code = agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '';
        if (code && code.trim() !== '') {
          return `Agence ${code}`;
        }
        // Si même le code n'est pas disponible, retourner un message par défaut
        return 'Agence non identifiée';
      }
      
      return name.trim();
    },
    filterAgencies(agencies) {
      // Filtrer les agences pour exclure celles avec "Inconnu" ou non identifiées
      if (!agencies || !Array.isArray(agencies)) {
        return [];
      }
      
      return agencies.filter(agency => {
        const name = agency.name || agency.AGENCE || agency.NOM_AGENCE || agency.agence || '';
        const nameUpper = name.toUpperCase().trim();
        
        // Exclure les agences "Inconnu", "Unknown", ou vides
        if (!name || nameUpper === '' || nameUpper === 'INCONNU' || nameUpper === 'UNKNOWN') {
          return false;
        }
        
        return true;
      });
    },
    getTotal(field) {
      const agencies = this.getAgenciesForZone(this.selectedZone);
      return agencies.reduce((sum, agency) => sum + (agency[field] || 0), 0);
    },
    getTotalTauxCroissance(type) {
      const agencies = this.getAgenciesForZone(this.selectedZone);
      const totalM1 = type === 'clients' 
        ? this.getTotal('nouveauxClientsM1')
        : this.getTotal('fraisM1');
      const totalM = type === 'clients'
        ? this.getTotal('nouveauxClientsM')
        : this.getTotal('fraisM');
      
      if (totalM1 === 0) return null;
      return ((totalM - totalM1) / totalM1) * 100;
    },
    calculateZoneTotals(agencies) {
      const totals = {
        objectif: 0,
        nouveauxClientsM1: 0,
        nouveauxClientsM: 0,
        variationClients: 0,
        tauxCroissanceClients: null,
        fraisM1: 0,
        fraisM: 0,
        variationFrais: 0,
        tauxCroissanceFrais: null,
        atteinte: null
      };

      agencies.forEach(agency => {
        totals.objectif += agency.objectif || agency.OBJECTIF_CLIENT || 0;
        totals.nouveauxClientsM1 += agency.nouveauxClientsM1 || 0;
        totals.nouveauxClientsM += agency.nouveauxClientsM || 0;
        totals.variationClients += agency.variationClients || 0;
        totals.fraisM1 += agency.fraisM1 || 0;
        totals.fraisM += agency.fraisM || 0;
        totals.variationFrais += agency.variationFrais || 0;
      });

      if (totals.nouveauxClientsM1 > 0) {
        totals.tauxCroissanceClients = ((totals.nouveauxClientsM - totals.nouveauxClientsM1) / totals.nouveauxClientsM1) * 100;
      }
      if (totals.fraisM1 > 0) {
        totals.tauxCroissanceFrais = ((totals.fraisM - totals.fraisM1) / totals.fraisM1) * 100;
      }
      if (totals.objectif > 0) {
        totals.atteinte = (totals.nouveauxClientsM / totals.objectif) * 100;
      }

      return totals;
    },
    getGrandTotal(field) {
      let total = 0;
      
      // Utiliser la nouvelle structure hiérarchique
      const hierarchicalData = this.filteredHierarchicalData || {};
      
      // Calculer le total des territoires
      if (hierarchicalData.TERRITOIRE && 
          typeof hierarchicalData.TERRITOIRE === 'object' && 
          hierarchicalData.TERRITOIRE !== null &&
          !Array.isArray(hierarchicalData.TERRITOIRE)) {
        try {
          Object.values(hierarchicalData.TERRITOIRE).forEach(territory => {
            if (territory && territory.totals && territory.totals[field] !== undefined) {
              total += territory.totals[field] || 0;
            }
          });
        } catch (e) {
          console.warn('Erreur lors du calcul du total des territoires:', e);
        }
      }
      
      // Compatibilité avec l'ancienne structure
      if (hierarchicalData.CORPORATE && 
          typeof hierarchicalData.CORPORATE === 'object' && 
          hierarchicalData.CORPORATE !== null &&
          !Array.isArray(hierarchicalData.CORPORATE)) {
        try {
          Object.values(hierarchicalData.CORPORATE).forEach(zone => {
            if (zone && zone.totals && zone.totals[field] !== undefined) {
              total += zone.totals[field] || 0;
            }
          });
        } catch (e) {
          console.warn('Erreur lors du calcul du total CORPORATE:', e);
        }
      }
      if (hierarchicalData.RETAIL && 
          typeof hierarchicalData.RETAIL === 'object' && 
          hierarchicalData.RETAIL !== null &&
          !Array.isArray(hierarchicalData.RETAIL)) {
        try {
          Object.values(hierarchicalData.RETAIL).forEach(zone => {
            if (zone && zone.totals && zone.totals[field] !== undefined) {
              total += zone.totals[field] || 0;
            }
          });
        } catch (e) {
          console.warn('Erreur lors du calcul du total RETAIL:', e);
        }
      }
      
      // Inclure le grand compte dans le total si disponible
      if (this.grandCompte && this.grandCompte[field] !== undefined) {
        total += this.grandCompte[field] || 0;
      }
      
      return total;
    },
    getGrandTotalAtteinte() {
      const totalObjectif = this.getGrandTotal('objectif');
      const totalNouveauxClientsM = this.getGrandTotal('nouveauxClientsM');
      if (totalObjectif > 0) {
        return (totalNouveauxClientsM / totalObjectif) * 100;
      }
      return null;
    },
    getGrandTotalTauxCroissance(type) {
      const totalM1 = type === 'clients' 
        ? this.getGrandTotal('nouveauxClientsM1')
        : this.getGrandTotal('fraisM1');
      const totalM = type === 'clients'
        ? this.getGrandTotal('nouveauxClientsM')
        : this.getGrandTotal('fraisM');
      
      if (totalM1 === 0) return null;
      return ((totalM - totalM1) / totalM1) * 100;
    },
    calculateTotalGrowthRate(m1, m) {
      if (m1 === 0) return null;
      return ((m - m1) / m1) * 100;
    },
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
      // Réinitialiser la sélection d'agence si on ferme la zone qui la contient
      if (this.selectedAgency) {
        const agencyZone = `${this.selectedAgency.category}_${this.selectedAgency.zone}`;
        if (section === agencyZone && !this.expandedSections[section]) {
          this.selectedAgency = null;
        }
      }
      // Réinitialiser la sélection d'agence si on ferme la catégorie qui la contient
      if (this.selectedAgency && (section === this.selectedAgency.category)) {
        if (!this.expandedSections[section]) {
          this.selectedAgency = null;
        }
      }
    },
    selectAgency(agency) {
      // Si on clique sur la même agence, la désélectionner
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
      // Réinitialiser à la vue totale
      this.selectedAgency = null;
      this.expandedSections.CORPORATE = false;
      this.expandedSections.RETAIL = false;
      Object.keys(this.expandedSections).forEach(key => {
        if (key.startsWith('CORPORATE_') || key.startsWith('RETAIL_')) {
          this.expandedSections[key] = false;
        }
      });
    },
    async exportChart(format) {
      try {
        await this.$nextTick();
        
        if (format === 'csv') {
          // Export CSV des données
          const labels = this.chartLabels;
          const current = this.selectedDataType === 'clients' ? this.chartCurrentData : this.chartFraisCurrentData;
          const previous = this.selectedDataType === 'clients' ? this.chartPreviousData : this.chartFraisPreviousData;
          
          const typeLabel = this.selectedDataType === 'clients' ? 'Nouveaux Clients' : 'Frais d\'Ouverture';
          let csv = 'Période,' + typeLabel + ' (Actuel),' + typeLabel + ' (Précédent)\n';
          
          for (let i = 0; i < labels.length; i++) {
            const value = current[i] || 0;
            const prevValue = previous[i] || 0;
            csv += `"${labels[i]}",${value},${prevValue}\n`;
          }
          
          // Télécharger le CSV avec BOM UTF-8 pour Excel
          const BOM = '\uFEFF';
          const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          const fileName = `donnees-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedDataType}-${new Date().toISOString().split('T')[0]}.csv`;
          link.download = fileName;
          link.href = URL.createObjectURL(blob);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          setTimeout(() => URL.revokeObjectURL(link.href), 100);
          return;
        }
        
        // Pour PNG et PDF, utiliser la méthode d'export du composant
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
          const fileName = `graphique-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedChartType}-${this.selectedDataType}-${new Date().toISOString().split('T')[0]}.${extension}`;
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
        console.error('Erreur lors de l\'export:', error);
        alert('Erreur lors de l\'export du graphique : ' + error.message);
      }
    },
    getSelectedMonthName() {
      return this.months[this.selectedMonth - 1];
    },
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        return 'Résultat de la semaine';
      } else if (this.selectedPeriod === 'month') {
        return `Résultat Global du Mois (${this.getSelectedMonthName()} ${this.selectedYear})`;
      } else if (this.selectedPeriod === 'year') {
        return `Résultat Global de l'Année (${this.selectedYear})`;
      }
      return 'Résultat Global';
    },
    getPeriodLabel() {
      if (this.selectedPeriod === 'week') {
        return `(Semaine ${this.selectedWeek} ${this.selectedYear})`;
      } else if (this.selectedPeriod === 'month') {
        return `(${this.getSelectedMonthName()} ${this.selectedYear})`;
      } else if (this.selectedPeriod === 'year') {
        return `(${this.selectedYear})`;
      }
      return '';
    },
    updateWeekFromDate() {
      if (this.selectedDate) {
        const date = new Date(this.selectedDate);
        this.selectedYear = date.getFullYear();
        this.selectedWeek = this.getWeekNumber(date);
      }
    },
    getWeekNumber(date) {
      // Si date est une string, la convertir en Date
      const d = date instanceof Date ? date : new Date(date);
      const dateObj = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
      const dayNum = dateObj.getUTCDay() || 7;
      dateObj.setUTCDate(dateObj.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(dateObj.getUTCFullYear(), 0, 1));
      return Math.ceil((((dateObj - yearStart) / 86400000) + 1) / 7);
    },
    getWeekDateRange() {
      if (!this.selectedDate) return '';
      
      const date = new Date(this.selectedDate);
      // Trouver le lundi de la semaine
      const day = date.getDay();
      const diff = date.getDate() - day + (day === 0 ? -6 : 1); // Ajuster pour lundi = 1
      const monday = new Date(date);
      monday.setDate(date.getDate() - day + (day === 0 ? -6 : 1));
      
      // Trouver le dimanche de la semaine
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      
      // Formater les dates
      const formatDate = (d) => {
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        return `${day}/${month}/${d.getFullYear()}`;
      };
      
      return `${formatDate(monday)} - ${formatDate(sunday)}`;
    },
    async fetchDataFromOracle() {
      // Charger les données depuis Oracle
      this.loading = true;
      try {
        const params = {
          period: this.selectedPeriod,
          zone: this.selectedZone || null
        };
        
        // Ajouter les paramètres selon la période
        if (this.selectedPeriod === 'week') {
          // Pour la semaine, envoyer la date sélectionnée
          if (this.selectedDate) {
            // S'assurer que la date est au format YYYY-MM-DD
            let dateToSend = this.selectedDate;
            // Si la date est au format DD/MM/YYYY, la convertir
            if (dateToSend.includes('/')) {
              const parts = dateToSend.split('/');
              dateToSend = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            params.date = dateToSend;
            console.log('📅 Période WEEK - Date sélectionnée (formatée):', dateToSend, 'Originale:', this.selectedDate);
          } else {
            console.warn('⚠️ Période WEEK mais aucune date sélectionnée');
          }
          // Envoyer aussi l'année pour référence
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        this.errorMessage = null; // Réinitialiser le message d'erreur
        console.log('🔍 Chargement des données Oracle avec les paramètres:', params);
        console.log('📅 Période sélectionnée:', this.selectedPeriod, 'Date:', this.selectedDate);
        console.log('📅 Timestamp de la requête:', new Date().toISOString());
        const response = await window.axios.get('/api/oracle/data/clients', { params });
        console.log('✅ Réponse reçue de l\'API Oracle:', response.data);
        
        // La réponse peut être directement les données ou dans response.data.data
        let data = null;
        if (response.data && response.data.data) {
          data = response.data.data;
        } else if (response.data) {
          data = response.data;
        }
        
        console.log('📊 Données formatées:', data);
        
        if (data) {
          
          // Priorité au nouveau format hiérarchique
          if (data.hierarchicalData) {
            console.log('📊 Données hiérarchiques reçues:', data.hierarchicalData);
            this.hierarchicalDataFromBackend = data.hierarchicalData;
            
            // Extraire les territoires et points de service
            if (data.hierarchicalData.TERRITOIRE) {
              // Filtrer les agences pour chaque territoire
              const territoire_dakar_ville = data.hierarchicalData.TERRITOIRE.territoire_dakar_ville || { name: 'TERRITOIRE DAKAR VILLE', agencies: [] };
              const territoire_dakar_banlieue = data.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue || { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] };
              const territoire_province_centre_sud = data.hierarchicalData.TERRITOIRE.territoire_province_centre_sud || { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] };
              const territoire_province_nord = data.hierarchicalData.TERRITOIRE.territoire_province_nord || { name: 'TERRITOIRE PROVINCE NORD', agencies: [] };
              
              // Vérifier si LAMINE GUEYE a un objectif
              const agenciesDakarVille = territoire_dakar_ville.agencies || territoire_dakar_ville.data || [];
              const lamineGueye = agenciesDakarVille.find(ag => 
                (ag.name || ag.AGENCE || '').toUpperCase().includes('LAMINE') || 
                (ag.name || ag.AGENCE || '').toUpperCase().includes('GUEYE')
              );
              if (lamineGueye) {
                console.log('🔍 AGENCE LAMINE GUEYE trouvée dans territoire_dakar_ville:', {
                  name: lamineGueye.name || lamineGueye.AGENCE,
                  objectif: lamineGueye.objectif,
                  OBJECTIF_CLIENT: lamineGueye.OBJECTIF_CLIENT,
                  all_keys: Object.keys(lamineGueye)
                });
              }
              
              this.territories = {
                territoire_dakar_ville: {
                  ...territoire_dakar_ville,
                  agencies: this.filterAgencies(agenciesDakarVille)
                },
                territoire_dakar_banlieue: {
                  ...territoire_dakar_banlieue,
                  agencies: this.filterAgencies(territoire_dakar_banlieue.agencies || territoire_dakar_banlieue.data || [])
                },
                territoire_province_centre_sud: {
                  ...territoire_province_centre_sud,
                  agencies: this.filterAgencies(territoire_province_centre_sud.agencies || territoire_province_centre_sud.data || [])
                },
                territoire_province_nord: {
                  ...territoire_province_nord,
                  agencies: this.filterAgencies(territoire_province_nord.agencies || territoire_province_nord.data || [])
                }
              };
            }
            
            // Logger le nombre d'agences
            console.log('📊 Agences par territoire:');
            console.log('   DAKAR VILLE:', this.territories.territoire_dakar_ville.agencies?.length || 0);
            console.log('   DAKAR BANLIEUE:', this.territories.territoire_dakar_banlieue.agencies?.length || 0);
            console.log('   PROVINCE CENTRE-SUD:', this.territories.territoire_province_centre_sud.agencies?.length || 0);
            console.log('   PROVINCE NORD:', this.territories.territoire_province_nord.agencies?.length || 0);
            console.log('📊 hierarchicalDataFromBackend:', this.hierarchicalDataFromBackend);
            
            // Mettre à jour aussi corporateZones et retailZones pour compatibilité
            this.corporateZones = {
              zone1: this.territories.territoire_dakar_ville,
              zone2: this.territories.territoire_province_centre_sud
            };
            this.retailZones = {
              zone1: this.territories.territoire_dakar_banlieue,
              zone2: this.territories.territoire_province_nord
            };            
            // Mettre à jour globalResult si disponible
            if (data.globalResult) {
              this.globalResult = {
                mois: data.globalResult.mois || 0,
                mois1: data.globalResult.mois1 || 0,
                evolution: data.globalResult.evolution || 0
              };
            }
            
            // Récupérer les données du grand compte si disponibles
            if (data.grandCompte) {
              this.grandCompteData = data.grandCompte;
            }
            
            // Charger les objectifs depuis Laravel et les fusionner avec les données Oracle
            await this.loadObjectives();
          } else if (data.territories) {
            // Format territories (sans hierarchicalData)
            console.log('📊 Données territories reçues:', data.territories);
            const territoire_dakar_ville = data.territories.territoire_dakar_ville || { name: 'TERRITOIRE DAKAR VILLE', agencies: [] };
            const territoire_dakar_banlieue = data.territories.territoire_dakar_banlieue || { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] };
            const territoire_province_centre_sud = data.territories.territoire_province_centre_sud || { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] };
            const territoire_province_nord = data.territories.territoire_province_nord || { name: 'TERRITOIRE PROVINCE NORD', agencies: [] };
            
            this.territories = {
              territoire_dakar_ville: {
                ...territoire_dakar_ville,
                agencies: this.filterAgencies(territoire_dakar_ville.agencies || territoire_dakar_ville.data || [])
              },
              territoire_dakar_banlieue: {
                ...territoire_dakar_banlieue,
                agencies: this.filterAgencies(territoire_dakar_banlieue.agencies || territoire_dakar_banlieue.data || [])
              },
              territoire_province_centre_sud: {
                ...territoire_province_centre_sud,
                agencies: this.filterAgencies(territoire_province_centre_sud.agencies || territoire_province_centre_sud.data || [])
              },
              territoire_province_nord: {
                ...territoire_province_nord,
                agencies: this.filterAgencies(territoire_province_nord.agencies || territoire_province_nord.data || [])
              }
            };
            
            // Logger le nombre d'agences par territoire
            console.log('📊 Agences par territoire:');
            console.log('   DAKAR VILLE:', this.territories.territoire_dakar_ville.agencies?.length || 0);
            console.log('   DAKAR BANLIEUE:', this.territories.territoire_dakar_banlieue.agencies?.length || 0);
            console.log('   PROVINCE CENTRE-SUD:', this.territories.territoire_province_centre_sud.agencies?.length || 0);
            console.log('   PROVINCE NORD:', this.territories.territoire_province_nord.agencies?.length || 0);
            
            // Mettre à jour aussi corporateZones et retailZones pour compatibilité
            this.corporateZones = {
              zone1: this.territories.territoire_dakar_ville,
              zone2: this.territories.territoire_province_centre_sud
            };
            this.retailZones = {
              zone1: this.territories.territoire_dakar_banlieue,
              zone2: this.territories.territoire_province_nord
            };
            
            // Mettre à jour globalResult si disponible
            if (data.globalResult) {
              this.globalResult = {
                mois: data.globalResult.mois || 0,
                mois1: data.globalResult.mois1 || 0,
                evolution: data.globalResult.evolution || 0
              };
            }
            
            // Récupérer les données du grand compte si disponibles
            if (data.grandCompte) {
              this.grandCompteData = data.grandCompte;
            }
            
            // Charger les objectifs depuis Laravel et les fusionner avec les données Oracle
            await this.loadObjectives();
          } else if (data.corporateZones && data.retailZones) {
            // Format ancien pour compatibilité
            this.corporateZones = {
              zone1: data.corporateZones.zone1 || { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
              zone2: data.corporateZones.zone2 || { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] }
            };
            this.retailZones = {
              zone1: data.retailZones.zone1 || { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
              zone2: data.retailZones.zone2 || { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
            };
            
            // Construire les territoires depuis l'ancien format et filtrer les agences
            this.territories = {
              territoire_dakar_ville: {
                ...this.corporateZones.zone1,
                agencies: this.filterAgencies(this.corporateZones.zone1.agencies || [])
              },
              territoire_dakar_banlieue: {
                ...this.retailZones.zone1,
                agencies: this.filterAgencies(this.retailZones.zone1.agencies || [])
              },
              territoire_province_centre_sud: {
                ...this.corporateZones.zone2,
                agencies: this.filterAgencies(this.corporateZones.zone2.agencies || [])
              },
              territoire_province_nord: {
                ...this.retailZones.zone2,
                agencies: this.filterAgencies(this.retailZones.zone2.agencies || [])
              }
            };
            
            if (data.globalResult) {
              this.globalResult = {
                mois: data.globalResult.mois || 0,
                mois1: data.globalResult.mois1 || 0,
                evolution: data.globalResult.evolution || 0
              };
            }
            
            // Récupérer les données du grand compte si disponibles
            if (data.grandCompte) {
              this.grandCompteData = data.grandCompte;
            } else {
              // Chercher dans toutes les zones corporate pour trouver "GRAND COMPTE"
              let grandCompteFound = null;
              if (data.corporateZones) {
                for (const zoneKey in data.corporateZones) {
                  const zone = data.corporateZones[zoneKey];
                  if (zone && zone.agencies && Array.isArray(zone.agencies)) {
                    grandCompteFound = zone.agencies.find(agency => 
                      agency && agency.name && agency.name.toUpperCase().includes('GRAND COMPTE')
                    );
                    if (grandCompteFound) break;
                  }
                }
              }
              this.grandCompteData = grandCompteFound || null;
            }
            console.log('✅ Données mises à jour dans le composant');
          } else {
            console.error('❌ Format de données Oracle non reconnu:', data);
            // Initialiser avec des structures vides en cas de format non reconnu
            this.territories = {
              territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
              territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
              territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
              territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
            };
            this.corporateZones = {
              zone1: this.territories.territoire_dakar_ville,
              zone2: this.territories.territoire_province_centre_sud
            };
            this.retailZones = {
              zone1: this.territories.territoire_dakar_banlieue,
              zone2: this.territories.territoire_province_nord
            };
            this.globalResult = { mois: 0, mois1: 0, evolution: 0 };
          }
        } else {
          console.error('❌ Réponse API invalide - response.data ou response.data.data manquant:', response.data);
          // Initialiser avec des structures vides
          this.territories = {
            territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
            territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
            territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
            territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
          };
          this.corporateZones = {
            zone1: this.territories.territoire_dakar_ville,
            zone2: this.territories.territoire_province_centre_sud
          };
          this.retailZones = {
            zone1: this.territories.territoire_dakar_banlieue,
            zone2: this.territories.territoire_province_nord
          };
          this.globalResult = { mois: 0, mois1: 0, evolution: 0 };
        }
      } catch (error) {
        console.error('❌ Erreur lors du chargement des données Oracle:', error);
        if (error.response) {
          console.error('   Status:', error.response.status);
          console.error('   Data:', error.response.data);
        } else if (error.request) {
          console.error('   Aucune réponse reçue. Vérifiez que le serveur Laravel est démarré.');
        }
        // En cas d'erreur, réinitialiser avec des structures vides
        this.territories = {
          territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
          territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
          territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
          territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
        };
        this.corporateZones = {
          zone1: this.territories.territoire_dakar_ville,
          zone2: this.territories.territoire_province_centre_sud
        };
        this.retailZones = {
          zone1: this.territories.territoire_dakar_banlieue,
          zone2: this.territories.territoire_province_nord
        };
        this.globalResult = { mois: 0, mois1: 0, evolution: 0, difference: 0 };
        this.grandCompteData = null;
        
        // Afficher un message d'erreur à l'utilisateur
        if (error.response && error.response.data) {
          const errorData = error.response.data;
          if (errorData.error) {
            this.errorMessage = `Erreur: ${errorData.error}. ${errorData.message || ''}`;
          } else if (errorData.message) {
            this.errorMessage = errorData.message;
          } else {
            this.errorMessage = 'Erreur lors du chargement des données depuis Oracle. Veuillez réessayer.';
          }
          console.error('Détails de l\'erreur API:', error.response.data);
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
    loadDataForPeriod() {
      // Charger les données depuis Oracle quand la période change
      console.log('🔄 loadDataForPeriod appelé - period:', this.selectedPeriod, 'date:', this.selectedDate, 'timestamp:', Date.now());
      // Forcer le rechargement en ajoutant un timestamp pour éviter le cache
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
      console.log('📅 handleDateChange appelé - Date:', this.selectedDate);
      this.updateWeekFromDate();
      // Forcer le rechargement immédiatement
      this.$nextTick(() => {
        this.loadDataForPeriod();
      });
    },
    async loadObjectives() {
      // Charger les objectifs CLIENT depuis l'API Laravel
      try {
        const token = localStorage.getItem('token');
        const params = {
          type: 'CLIENT',
          period: this.selectedPeriod === 'week' ? 'month' : this.selectedPeriod, // Pour la semaine, utiliser month
          year: this.selectedYear
        };
        
        // Ajouter les paramètres selon la période
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
        } else if (this.selectedPeriod === 'quarter') {
          params.quarter = Math.ceil(this.selectedMonth / 3); // Convertir le mois en trimestre
        } else if (this.selectedPeriod === 'week') {
          // Pour la semaine, utiliser le mois de la date sélectionnée
          if (this.selectedDate) {
            const date = new Date(this.selectedDate);
            params.month = date.getMonth() + 1;
          }
        }
        
        console.log('📊 Chargement des objectifs CLIENT avec params:', params);
        
        const response = await window.axios.get('/api/objectives', {
          params: params,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.data && response.data.success && response.data.data) {
          const objectives = Array.isArray(response.data.data) ? response.data.data : [response.data.data];
          console.log('✅ Objectifs CLIENT chargés:', objectives.length);
          
          // Créer un map des objectifs par agency_code et agency_name
          const objectivesMapByCode = {};
          const objectivesMapByName = {};
          objectives.forEach(obj => {
            const agencyCode = obj.agency_code || '';
            const agencyName = obj.agency_name || '';
            const value = obj.value || 0;
            
            if (agencyCode) {
              // Stocker l'objectif avec le code d'agence comme clé
              objectivesMapByCode[agencyCode] = value;
            }
            if (agencyName) {
              // Stocker aussi par nom d'agence (normalisé en majuscules)
              const normalizedName = agencyName.toUpperCase().trim();
              objectivesMapByName[normalizedName] = value;
            }
          });
          
          console.log('📊 Objectifs par code:', Object.keys(objectivesMapByCode).length);
          console.log('📊 Objectifs par nom:', Object.keys(objectivesMapByName).length);
          
          // Fusionner les objectifs avec les données Oracle
          this.mergeObjectivesWithOracleData(objectivesMapByCode, objectivesMapByName);
        }
      } catch (error) {
        console.warn('⚠️ Erreur lors du chargement des objectifs:', error);
        // Ne pas bloquer l'affichage si les objectifs ne peuvent pas être chargés
      }
    },
    mergeObjectivesWithOracleData(objectivesMapByCode, objectivesMapByName) {
      // Fusionner les objectifs avec les agences dans les territoires
      Object.keys(this.territories).forEach(territoryKey => {
        const territory = this.territories[territoryKey];
        if (territory.agencies && Array.isArray(territory.agencies)) {
          territory.agencies.forEach(agency => {
            const agencyCode = (agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '').toString().trim();
            const agencyName = (agency.name || agency.AGENCE || agency.NOM_AGENCE || '').toString().trim();
            
            // Chercher l'objectif par code d'agence d'abord
            let objectiveValue = null;
            if (agencyCode && objectivesMapByCode[agencyCode]) {
              objectiveValue = objectivesMapByCode[agencyCode];
              console.log(`✅ Objectif trouvé par code pour ${agencyName} (${agencyCode}):`, objectiveValue);
            } else if (agencyName) {
              // Essayer de trouver par nom d'agence (normalisé)
              const normalizedName = agencyName.toUpperCase().trim();
              if (objectivesMapByName[normalizedName]) {
                objectiveValue = objectivesMapByName[normalizedName];
                console.log(`✅ Objectif trouvé par nom pour ${agencyName}:`, objectiveValue);
              }
            }
            
            if (objectiveValue !== null) {
              agency.objectif = objectiveValue;
              agency.OBJECTIF_CLIENT = objectiveValue;
            }
          });
        }
      });
      
      // Fusionner avec le grand compte
      if (this.grandCompteData) {
        const agencyCode = (this.grandCompteData.CODE_AGENCE || this.grandCompteData.code_agence || this.grandCompteData.code || this.grandCompteData.CODE || '').toString().trim();
        const agencyName = (this.grandCompteData.name || this.grandCompteData.AGENCE || this.grandCompteData.NOM_AGENCE || '').toString().trim();
        
        let objectiveValue = null;
        if (agencyCode && objectivesMapByCode[agencyCode]) {
          objectiveValue = objectivesMapByCode[agencyCode];
        } else if (agencyName) {
          const normalizedName = agencyName.toUpperCase().trim();
          if (objectivesMapByName[normalizedName]) {
            objectiveValue = objectivesMapByName[normalizedName];
          }
        }
        
        if (objectiveValue !== null) {
          this.grandCompteData.objectif = objectiveValue;
          this.grandCompteData.OBJECTIF_CLIENT = objectiveValue;
        }
      }
      
      // Mettre à jour aussi hierarchicalDataFromBackend si disponible
      if (this.hierarchicalDataFromBackend) {
        this.updateHierarchicalDataWithObjectives(objectivesMapByCode, objectivesMapByName);
      }
    },
    updateHierarchicalDataWithObjectives(objectivesMapByCode, objectivesMapByName) {
      // Mettre à jour les objectifs dans la structure hiérarchique
      if (this.hierarchicalDataFromBackend.TERRITOIRE) {
        Object.keys(this.hierarchicalDataFromBackend.TERRITOIRE).forEach(territoryKey => {
          const territory = this.hierarchicalDataFromBackend.TERRITOIRE[territoryKey];
          if (territory.agencies && Array.isArray(territory.agencies)) {
            territory.agencies.forEach(agency => {
              const agencyCode = (agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '').toString().trim();
              const agencyName = (agency.name || agency.AGENCE || agency.NOM_AGENCE || '').toString().trim();
              
              let objectiveValue = null;
              if (agencyCode && objectivesMapByCode[agencyCode]) {
                objectiveValue = objectivesMapByCode[agencyCode];
              } else if (agencyName) {
                const normalizedName = agencyName.toUpperCase().trim();
                if (objectivesMapByName[normalizedName]) {
                  objectiveValue = objectivesMapByName[normalizedName];
                }
              }
              
              if (objectiveValue !== null) {
                agency.objectif = objectiveValue;
                agency.OBJECTIF_CLIENT = objectiveValue;
              }
            });
          }
        });
      }
    }
  }
}
</script>

<style scoped>
.client-section {
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

.week-info {
  margin-left: 10px;
  font-size: 14px;
  color: #666;
  font-style: italic;
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

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.zone-selection {
  padding: 40px;
  text-align: center;
  background: #F9F9F9;
  border: 2px dashed #DDD;
  border-radius: 8px;
  margin-bottom: 30px;
}

.zone-message {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.zone-agencies-section {
  margin-top: 30px;
}

.zone-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 25px;
  color: #1A4D3A;
  padding-bottom: 10px;
  border-bottom: 2px solid #1A4D3A;
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


.agency-name {
  font-weight: 500;
  color: #333;
  min-width: 150px;
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

.selected-agency {
  background: #e3f2fd !important;
  border-left: 4px solid #1A4D3A;
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

.positive {
  color: #10B981;
  font-weight: 600;
}

.negative {
  color: #EF4444;
  font-weight: 600;
}

.achievement-high {
  color: #10B981;
  font-weight: 500;
}

.achievement-medium {
  color: #F59E0B;
  font-weight: 500;
}

.achievement-low {
  color: #EF4444;
  font-weight: 500;
}

.chart-evolution-section {
  margin-top: 30px;
  background: white;
  border: 1px solid #DDD;
  border-radius: 4px;
  padding: 20px 20px 20px 20px; /* padding: top right bottom left */
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

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
  }
  
  .section-header {
    flex-wrap: wrap;
    gap: 15px;
  }
  
  .chart-wrapper-container {
    min-height: 450px;
    height: 550px;
    max-height: 700px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .section-header {
    flex-direction: column;
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
  .year-select,
  .period-select,
  .date-select {
    flex: 1;
    min-width: 120px;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .table-container {
    overflow-x: scroll;
  }
  
  .chart-wrapper-container {
    min-height: 400px;
    max-height: 500px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .chart-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .chart-tabs {
    flex-wrap: wrap;
  }
  
  .chart-tab {
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .data-type-selector {
    flex-direction: column;
    gap: 10px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .kpi-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .section-header {
    padding: 12px;
  }
  
  .section-title {
    font-size: 18px;
  }
  
  .period-selector {
    flex-direction: column;
    width: 100%;
  }
  
  .month-select,
  .year-select,
  .period-select,
  .date-select {
    width: 100%;
    min-width: 100%;
  }
  
  .chart-tabs {
    flex-direction: column;
  }
  
  .chart-tab {
    width: 100%;
    text-align: left;
  }
  
  .chart-wrapper-container {
    min-height: 350px;
    max-height: 450px;
  }
}
</style>
