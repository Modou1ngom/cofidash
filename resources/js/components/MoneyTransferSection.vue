<template>
  <div class="money-transfer-section">
    <div class="section-header">
      <h2 class="section-title">Activités de Transferts d'Argent - {{ getPeriodTitle() }}</h2>
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
    
    <!-- Boutons de sélection de service -->
    <div class="service-selector">
      <button 
        v-for="service in availableServices" 
        :key="service.value"
        :class="['service-btn', { active: selectedService === service.value }]"
        @click="selectService(service.value)"
      >
        {{ service.label }}
      </button>
    </div>
    
    <!-- Message de chargement ou d'erreur -->
    <div v-if="loading" class="loading-message">
      <p>🔄 Chargement des données depuis Oracle...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>⚠️ {{ errorMessage }}</p>
    </div>
    
    <!-- Contenu principal - toujours affiché -->
    <div class="transfer-content">
      <!-- Tableau détaillé à gauche -->
      <div class="zone-agencies-section">
        <div class="table-container">
          <table class="agencies-table">
            <thead>
              <tr>
                <th>AGENCE</th>
                <th>Objectif</th>
                <th>Volume transfert M-1</th>
                <th>Volume transfert M</th>
                <th>Variation <br>(Volume)</th>
                <th>Variation <br>(%)</th>
                <th>TRO</th>
                <th>Contribution agence <br>sur la zone</th>
                <th>Commission générée</th>
              </tr>
            </thead>
            <tbody>
              <!-- TERRITOIRE - toujours affiché -->
              <tr class="level-1-row" 
                  @click="toggleExpand('TERRITOIRE')">
                <td class="level-1">
                  <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                    {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                  </button>
                  <strong>TERRITOIRE</strong>
                </td>
                <td><strong>{{ formatNumber(territoireTotal.objectif) }}</strong></td>
                <td><strong>{{ formatNumber(territoireTotal.volume_m1) }}</strong></td>
                <td><strong>{{ formatNumber(territoireTotal.volume_m) }}</strong></td>
                <td :class="getVariationClass(territoireTotal.variation_volume)">
                  <strong>{{ formatVariation(territoireTotal.variation_volume) }}</strong>
                </td>
                <td :class="getVariationClass(territoireTotal.variation_pct)">
                  <strong>{{ formatVariationPercent(territoireTotal.variation_pct) }}</strong>
                </td>
                <td :class="getTROClass(territoireTotal.tro)">
                  <strong>{{ formatTRO(territoireTotal.tro) }}</strong>
                </td>
                <td :class="getContributionClass(territoireTotal.contribution)">
                  <strong>{{ formatPercent(territoireTotal.contribution) }}</strong>
                </td>
                <td><strong>{{ formatNumber(territoireTotal.commission || 0, 2) }}</strong></td>
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
                    <td><strong>{{ formatNumber(territory.total.objectif) }}</strong></td>
                    <td><strong>{{ formatNumber(territory.total.volume_m1) }}</strong></td>
                    <td><strong>{{ formatNumber(territory.total.volume_m) }}</strong></td>
                    <td :class="getVariationClass(territory.total.variation_volume)">
                      <strong>{{ formatVariation(territory.total.variation_volume) }}</strong>
                    </td>
                    <td :class="getVariationClass(territory.total.variation_pct)">
                      <strong>{{ formatVariationPercent(territory.total.variation_pct) }}</strong>
                    </td>
                    <td :class="getTROClass(territory.total.tro)">
                      <strong>{{ formatTRO(territory.total.tro) }}</strong>
                    </td>
                    <td :class="getContributionClass(territory.total.contribution || 0)">
                      <strong>{{ formatPercent(territory.total.contribution || 0) }}</strong>
                    </td>
                    <td><strong>{{ formatNumber(territory.total.commission || 0, 2) }}</strong></td>
                  </tr>
                  <!-- Entités dans chaque territoire (agences, zones, corporate, retail, etc.) -->
                  <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                    <tr 
                      v-for="entity in territory.data" 
                      :key="entity.agence || entity.name" 
                      class="level-3-row"
                    >
                      <td class="level-3">{{ entity.agence || entity.name }}</td>
                      <td>{{ formatNumber(entity.objectif || 0) }}</td>
                      <td>{{ formatNumber(entity.volume_m1 || 0) }}</td>
                      <td>{{ formatNumber(entity.volume_m || 0) }}</td>
                      <td :class="getVariationClass(entity.variation_volume || 0)">
                        {{ formatVariation(entity.variation_volume || 0) }}
                      </td>
                      <td :class="getVariationClass(entity.variation_pct || 0)">
                        {{ formatVariationPercent(entity.variation_pct || 0) }}
                      </td>
                      <td :class="getTROClass(entity.tro || 0)">
                        {{ formatTRO(entity.tro || 0) }}
                      </td>
                      <td :class="getContributionClass(entity.contribution || 0)">
                        {{ formatPercent(entity.contribution || 0) }}
                      </td>
                      <td>{{ formatNumber(entity.commission || 0, 2) }}</td>
                    </tr>
                  </template>
                </template>
              </template>

              <!-- GRAND COMPTE -->
              <tr v-if="grandCompte" class="level-3-row">
                <td class="level-3">GRAND COMPTE</td>
                <td>{{ formatNumber(grandCompte.objectif || 0) }}</td>
                <td>{{ formatNumber(grandCompte.volume_m1 || 0) }}</td>
                <td>{{ formatNumber(grandCompte.volume_m || 0) }}</td>
                <td :class="getVariationClass(grandCompte.variation_volume || 0)">
                  {{ formatVariation(grandCompte.variation_volume || 0) }}
                </td>
                <td :class="getVariationClass(grandCompte.variation_pct || 0)">
                  {{ formatVariationPercent(grandCompte.variation_pct || 0) }}
                </td>
                <td :class="getTROClass(grandCompte.tro || 0)">
                  {{ formatTRO(grandCompte.tro || 0) }}
                </td>
                <td :class="getContributionClass(grandCompte.contribution || 0)">
                  {{ formatPercent(grandCompte.contribution || 0) }}
                </td>
                <td>{{ formatNumber(grandCompte.commission || 0, 2) }}</td>
              </tr>

              <!-- Ligne TOTAL -->
              <tr class="total-row">
                <td><strong>TOTAL</strong></td>
                <td><strong>{{ formatNumber(getGrandTotal('objectif')) }}</strong></td>
                <td><strong>{{ formatNumber(getGrandTotal('volume_m1')) }}</strong></td>
                <td><strong>{{ formatNumber(getGrandTotal('volume_m')) }}</strong></td>
                <td :class="getVariationClass(getGrandTotal('variation_volume'))">
                  <strong>{{ formatVariation(getGrandTotal('variation_volume')) }}</strong>
                </td>
                <td :class="getVariationClass(getGrandTotal('variation_pct'))">
                  <strong>{{ formatVariationPercent(getGrandTotal('variation_pct')) }}</strong>
                </td>
                <td :class="getTROClass(getGrandTotal('tro'))">
                  <strong>{{ formatTRO(getGrandTotal('tro')) }}</strong>
                </td>
                <td :class="getContributionClass(getGrandTotal('contribution'))">
                  <strong>{{ formatPercent(getGrandTotal('contribution')) }}</strong>
                </td>
                <td><strong>{{ formatNumber(getGrandTotal('commission'), 2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MoneyTransferSection',
  data() {
    const now = new Date();
    return {
      loading: false,
      errorMessage: null,
      agencies: [],
      services: [],
      hierarchicalData: {
        TERRITOIRE: {
          territoire_dakar_ville: {
            name: 'TERRITOIRE DAKAR VILLE',
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_dakar_banlieue: {
            name: 'TERRITOIRE DAKAR BANLIEUE',
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_province_centre_sud: {
            name: 'TERRITOIRE PROVINCE CENTRE-SUD',
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_province_nord: {
            name: 'TERRITOIRE PROVINCE NORD',
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          }
        }
      },
      expandedSections: {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      },
      grandCompte: null,
      selectedPeriod: 'month',
      selectedDate: now.toISOString().split('T')[0],
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      selectedService: 'om', // Service par défaut: Orange Money
      availableServices: [
        { value: 'om', label: 'Orange Money' },
        { value: 'wave', label: 'Wave' },
        { value: 'ria', label: 'Ria' },
        { value: 'wu', label: 'Western Union' },
        { value: 'moneygram', label: 'MoneyGram' },
        { value: 'wizzal', label: 'Wizzal' },
        { value: 'free_money', label: 'FREE Money' }
      ],
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      years: Array.from({ length: 5 }, (_, i) => now.getFullYear() - i)
    }
  },
  computed: {
    filteredHierarchicalData() {
      return this.hierarchicalData;
    },
    territoireTotal() {
      const territories = this.hierarchicalData.TERRITOIRE || {};
      let total = {
        objectif: 0,
        volume_m1: 0,
        volume_m: 0,
        variation_volume: 0,
        variation_pct: 0,
        tro: 0,
        contribution: 100, // TERRITOIRE représente 100% de la contribution totale
        commission: 0
      };
      
      Object.values(territories).forEach(territory => {
        if (territory.total) {
          total.objectif += territory.total.objectif || 0;
          total.volume_m1 += territory.total.volume_m1 || 0;
          total.volume_m += territory.total.volume_m || 0;
          total.commission += territory.total.commission || 0;
        }
      });
      
      total.variation_volume = total.volume_m - total.volume_m1;
      total.variation_pct = total.volume_m1 > 0 
        ? ((total.variation_volume / total.volume_m1) * 100) 
        : 0;
      total.tro = total.objectif > 0 ? (total.volume_m / total.objectif) * 100 : 0;
      
      return total;
    }
  },
  mounted() {
    this.fetchTransferData();
  },
  methods: {
    async fetchTransferData() {
      this.loading = true;
      this.errorMessage = null;
      
      try {
        const params = {
          period: this.selectedPeriod,
          service: this.selectedService,
          _t: Date.now()
        };
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'week') {
          params.date = this.selectedDate;
        }

        const axios = window.axios;
        if (!axios) {
          throw new Error('axios non disponible');
        }

        const { data: result } = await axios.get('/api/oracle/data/transfers', { params });

        if (result.data) {
          this.agencies = result.data.agencies || [];
          this.services = result.data.services || [];
          this.organizeDataHierarchically();
        } else {
          throw new Error('Format de données invalide');
        }
      } catch (error) {
        console.error('Erreur lors de la récupération des données de transferts:', error);
        const msg = (error.response && error.response.data && error.response.data.message)
          || error.message
          || 'Erreur réseau';
        this.errorMessage = `Erreur: ${msg}`;
      } finally {
        this.loading = false;
      }
    },
    selectService(service) {
      this.selectedService = service;
      this.fetchTransferData();
    },
    organizeDataHierarchically() {
      // Réinitialiser les structures mais préserver la structure des territoires
      const territoryNames = {
        territoire_dakar_ville: 'TERRITOIRE DAKAR VILLE',
        territoire_dakar_banlieue: 'TERRITOIRE DAKAR BANLIEUE',
        territoire_province_centre_sud: 'TERRITOIRE PROVINCE CENTRE-SUD',
        territoire_province_nord: 'TERRITOIRE PROVINCE NORD'
      };
      
      this.hierarchicalData = {
        TERRITOIRE: {
          territoire_dakar_ville: {
            name: territoryNames.territoire_dakar_ville,
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_dakar_banlieue: {
            name: territoryNames.territoire_dakar_banlieue,
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_province_centre_sud: {
            name: territoryNames.territoire_province_centre_sud,
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          },
          territoire_province_nord: {
            name: territoryNames.territoire_province_nord,
            data: [],
            total: { objectif: 0, volume_m1: 0, volume_m: 0, variation_volume: 0, variation_pct: 0, tro: 0, contribution: 0, commission: 0 }
          }
        }
      };
      this.grandCompte = null;
      
      // Zonage officiel : clés du plus spécifique au plus court (évite ex. TAMBA ⊂ TAMBACOUNDA)
      const territoryEntries = [
        ['AGENCE PRINCIPALE POINT E', 'territoire_dakar_ville'],
        ['AGENCE LINGUERE LA GUEDIAWAYE', 'territoire_dakar_banlieue'],
        ['AGENCE LINGUERLA', 'territoire_dakar_banlieue'],
        ['AGENCE ZINGUINCHOR', 'territoire_province_centre_sud'],
        ['AGENCE LAMINE GUEYE', 'territoire_dakar_ville'],
        ['AGENCE CASTORS', 'territoire_dakar_ville'],
        ['AGENCE MARISTES', 'territoire_dakar_ville'],
        ['AGENCE TAMBACOUNDA', 'territoire_province_centre_sud'],
        ['AGENCE TOUBA KHAYRA', 'territoire_province_nord'],
        ['AGENCE SAINT LOUIS', 'territoire_province_nord'],
        ['AGENCE SAINT-LOUIS', 'territoire_province_nord'],
        ['NIARRY TALLY', 'territoire_dakar_ville'],
        ['NIARRY TALLI', 'territoire_dakar_ville'],
        ['NIARY TALLY', 'territoire_dakar_ville'],
        ['SCAT URBAM', 'territoire_dakar_ville'],
        ['LAMINE GUEYE', 'territoire_dakar_ville'],
        ['CASTORS', 'territoire_dakar_ville'],
        ['CASTOR', 'territoire_dakar_ville'],
        ['MARISTES', 'territoire_dakar_ville'],
        ['LINGUERLA', 'territoire_dakar_banlieue'],
        ['LINGUERE', 'territoire_dakar_banlieue'],
        ['GUEDIAWAYE', 'territoire_dakar_banlieue'],
        ['PARCELLES', 'territoire_dakar_banlieue'],
        ['PIKINE', 'territoire_dakar_banlieue'],
        ['RUFISQUE', 'territoire_dakar_banlieue'],
        ['TAMBACOUNDA', 'territoire_province_centre_sud'],
        ['ZINGUINCHOR', 'territoire_province_centre_sud'],
        ['ZIGUINCHOR', 'territoire_province_centre_sud'],
        ['VITRINE LAMINE', 'territoire_dakar_ville'],
        ['NGUELAW', 'territoire_dakar_ville'],
        ['GUEYE', 'territoire_dakar_ville'],
        ['POINT E', 'territoire_dakar_ville'],
        ['KEUR MASSAR', 'territoire_dakar_banlieue'],
        ['MBOUR', 'territoire_province_centre_sud'],
        ['THIES', 'territoire_province_centre_sud'],
        ['KAOLACK', 'territoire_province_centre_sud'],
        ['SAINT LOUIS', 'territoire_province_nord'],
        ['SAINT-LOUIS', 'territoire_province_nord'],
        ['LOUGA', 'territoire_province_nord'],
        ['DIOURBEL', 'territoire_province_nord'],
        ['OUROSSOGUI', 'territoire_province_nord'],
        ['TOUBA KHAYRA', 'territoire_province_nord'],
        ['TOUBA', 'territoire_province_nord']
      ];
      
      // Organiser les entités par territoire
      const entitiesByTerritory = {
        territoire_dakar_ville: [],
        territoire_dakar_banlieue: [],
        territoire_province_centre_sud: [],
        territoire_province_nord: []
      };
      
      this.agencies.forEach(agency => {
        const agenceUpper = String(agency.agence || '').toUpperCase();
        
        // GRAND COMPTE
        if (agenceUpper.includes('GRAND COMPTE')) {
          this.grandCompte = agency;
          return;
        }
        
        // Ignorer TOTAL
        if (agenceUpper === 'TOTAL') {
          return;
        }
        
        // Ignorer les zones, corporate et retail
        if (agenceUpper.includes('ZONE DAKAR') || 
            agenceUpper.includes('ZONE PROVINCE') || 
            agenceUpper.includes('CORPORATE') || 
            agenceUpper.includes('RETAIL')) {
          return;
        }
        
        let territoryKey = null;
        for (const [key, territory] of territoryEntries) {
          if (agenceUpper.includes(key)) {
            territoryKey = territory;
            break;
          }
        }
        if (!territoryKey) {
          territoryKey = 'territoire_dakar_ville';
        }
        entitiesByTerritory[territoryKey].push(agency);
      });
      
      // Construire la structure hiérarchique - mettre à jour les territoires existants
      Object.entries(entitiesByTerritory).forEach(([key, entities]) => {
        // Mettre à jour le territoire avec les données
        if (this.hierarchicalData.TERRITOIRE[key]) {
          this.hierarchicalData.TERRITOIRE[key].data = entities;
          this.hierarchicalData.TERRITOIRE[key].total = this.calculateTerritoryTotal(entities);
        }
      });
      
      // Calculer les contributions pour chaque entité
      this.calculateContributions();
    },
    calculateTerritoryTotal(entities) {
      const total = {
        objectif: 0,
        volume_m1: 0,
        volume_m: 0,
        variation_volume: 0,
        variation_pct: 0,
        tro: 0,
        contribution: 0,
        commission: 0
      };
      
      entities.forEach(entity => {
        total.objectif += entity.objectif || 0;
        total.volume_m1 += entity.volume_m1 || 0;
        total.volume_m += entity.volume_m || 0;
        total.commission += entity.commission || 0;
      });
      
      total.variation_volume = total.volume_m - total.volume_m1;
      total.variation_pct = total.volume_m1 > 0 
        ? ((total.variation_volume / total.volume_m1) * 100) 
        : 0;
      total.tro = total.objectif > 0 
        ? (total.volume_m / total.objectif) * 100 
        : 0;
      
      return total;
    },
    calculateContributions() {
      // Calculer les contributions pour chaque territoire
      Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
        const totalM = territory.data.reduce((sum, entity) => sum + (entity.volume_m || 0), 0);
        territory.data.forEach(entity => {
          entity.contribution = totalM > 0 ? ((entity.volume_m || 0) / totalM) * 100 : 0;
        });
      });
    },
    toggleExpand(section) {
      if (!this.expandedSections.hasOwnProperty(section)) {
        this.$set(this.expandedSections, section, false);
      }
      this.expandedSections[section] = !this.expandedSections[section];
    },
    handlePeriodChange() {
      this.fetchTransferData();
    },
    handleDateChange() {
      this.fetchTransferData();
    },
    handleMonthChange() {
      this.fetchTransferData();
    },
    handleYearChange() {
      this.fetchTransferData();
    },
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        if (this.selectedDate) {
          const date = new Date(this.selectedDate);
          return `Semaine du ${date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })}`;
        }
        return 'Semaine';
      } else if (this.selectedPeriod === 'month') {
        return `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
      } else if (this.selectedPeriod === 'year') {
        return `Année ${this.selectedYear}`;
      }
      return '';
    },
    formatNumber(value, decimals = 0) {
      if (value === null || value === undefined) return '0';
      return Number(value).toLocaleString('fr-FR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      });
    },
    formatPercent(value) {
      if (value === null || value === undefined) return '0%';
      return `${Number(value).toFixed(0)}%`;
    },
    formatTRO(value) {
      if (value === null || value === undefined || value === 0) return '-';
      return `${Number(value).toFixed(0)}%`;
    },
    formatVariation(value) {
      if (value === null || value === undefined) return '-';
      const num = Number(value);
      const formatted = num.toLocaleString('fr-FR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      });
      return num >= 0 ? `+${formatted}` : formatted;
    },
    formatVariationPercent(value) {
      if (value === null || value === undefined) return '-';
      const num = Number(value);
      const formatted = Math.abs(num).toFixed(2);
      return num >= 0 ? `▲${formatted}%` : `▼${formatted}%`;
    },
    getVariationClass(value) {
      if (value === null || value === undefined) return '';
      if (value < 0) return 'negative';
      return 'positive';
    },
    getTROClass(value) {
      if (value === null || value === undefined || value === 0) return '';
      if (value >= 100) return 'positive';
      if (value >= 80) return 'moderate';
      return 'negative';
    },
    getContributionClass(value) {
      if (value === null || value === undefined) return '';
      if (value === 100) return 'positive'; // Vert pour 100%
      if (value > 0) return 'moderate'; // Jaune pour autres valeurs positives
      return 'negative'; // Rouge pour 0 ou négatif
    },
    getServiceInitials(serviceName) {
      if (!serviceName) return '?';
      const words = serviceName.split(' ');
      if (words.length >= 2) {
        return words[0][0] + words[1][0];
      }
      return serviceName.substring(0, 2).toUpperCase();
    },
    getGrandTotal(field) {
      const territoire = this.territoireTotal[field] || 0;
      const grandCompte = this.grandCompte ? (this.grandCompte[field] || 0) : 0;
      return territoire + grandCompte;
    }
  }
}
</script>

<style scoped>
.money-transfer-section {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: white;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: #1A4D3A;
  margin: 0;
}

.service-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  background: white;
  padding: 15px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.service-btn {
  padding: 10px 20px;
  border: 2px solid #DC2626;
  background: white;
  color: #DC2626;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.service-btn:hover {
  background: #DC2626;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(220, 38, 38, 0.3);
}

.service-btn.active {
  background: #DC2626;
  color: white;
  box-shadow: 0 2px 4px rgba(220, 38, 38, 0.2);
}

.period-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.period-select,
.month-select,
.year-select,
.date-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.period-select:hover,
.month-select:hover,
.year-select:hover,
.date-select:hover {
  border-color: #1A4D3A;
}

.period-select:focus,
.month-select:focus,
.year-select:focus,
.date-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.1);
}

.loading-message,
.error-message {
  padding: 20px;
  text-align: center;
  background: white;
  border-radius: 4px;
  margin-bottom: 20px;
}

.error-message {
  background: #fee;
  color: #c33;
}

.transfer-content {
  display: block;
}

.zone-agencies-section {
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow-x: auto;
}

.table-container {
  overflow-x: auto;
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
  color: #333;
}

.level-3 {
  font-size: 13px;
  padding-left: 48px !important;
}

.expand-btn {
  background: transparent;
  border: 1px solid currentColor;
  color: inherit;
  width: 20px;
  height: 20px;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  padding: 0;
  flex-shrink: 0;
}

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
}

.positive {
  color: #22c55e;
  font-weight: 600;
}

.negative {
  color: #ef4444;
  font-weight: 600;
}

.moderate {
  color: #f59e0b;
  font-weight: 600;
}

</style>
