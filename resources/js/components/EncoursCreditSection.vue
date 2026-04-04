<template>
  <div class="client-section">
    <div class="section-header">
      <h2 class="section-title">Evolution de l'encours crédit - {{ getPeriodTitle }}</h2>
      <div class="period-selector">
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
    
    <!-- Message de chargement en haut -->
    <div v-if="loading" class="loading-banner">
      <div class="loading-spinner-small"></div>
      <span>Chargement des données en cours... Cette opération peut prendre jusqu'à 5 minutes.</span>
    </div>
    
    <!-- Message d'erreur -->
    <div v-if="error" class="error-message">
      ⚠️ {{ error }}
    </div>
    
    <!-- Tableau d'évolution encours crédit -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th rowspan="2">AGENCE</th>
              <th colspan="4">PTF (Portefeuille)</th>
              <th colspan="4">Produit d'intérêt</th>
            </tr>
            <tr>
              <!-- PTF columns -->
              <th>PTF {{ periodLabels.m1 }}</th>
              <th>PTF {{ periodLabels.m }}</th>
              <th>Variation en Millions de FCFA</th>
              <th>Taux de croissance (%)</th>
              <!-- Produit d'intérêt columns -->
              <th>Produit d'intérêt {{ periodLabels.m1 }}</th>
              <th>Produit d'intérêt {{ periodLabels.m }}</th>
              <th>Variation en Millions de FCFA</th>
              <th>Taux de croissance (%)</th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr v-if="filteredHierarchicalData && filteredHierarchicalData.TERRITOIRE && Object.keys(filteredHierarchicalData.TERRITOIRE).length > 0" class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>{{ formatCurrency(territoireTotal.PTF_M1 || 0) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.PTF_M || 0) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.VARIATION_PTF || 0)">
                <strong>{{ formatVariationCurrency(territoireTotal.VARIATION_PTF || 0) }}</strong>
              </td>
              <td :class="getGrowthRateClass(territoireTotal.TAUX_CROISSANCE_PTF || 0)">
                <strong>{{ formatVariationPercent(territoireTotal.TAUX_CROISSANCE_PTF || 0) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(territoireTotal.PRODUIT_INT_M1 || 0) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.PRODUIT_INT_M || 0) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.VARIATION_PRODUIT_INT || 0)">
                <strong>{{ formatVariationCurrency(territoireTotal.VARIATION_PRODUIT_INT || 0) }}</strong>
              </td>
              <td :class="getGrowthRateClass(territoireTotal.TAUX_CROISSANCE_PRODUIT_INT || 0)">
                <strong>{{ formatVariationPercent(territoireTotal.TAUX_CROISSANCE_PRODUIT_INT || 0) }}</strong>
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
                  <td><strong>{{ formatCurrency(territory.total.PTF_M1 || 0) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.total.PTF_M || 0) }}</strong></td>
                  <td :class="getVariationClass(territory.total.VARIATION_PTF || 0)">
                    <strong>{{ formatVariationCurrency(territory.total.VARIATION_PTF || 0) }}</strong>
                  </td>
                  <td :class="getGrowthRateClass(territory.total.TAUX_CROISSANCE_PTF || 0)">
                    <strong>{{ formatVariationPercent(territory.total.TAUX_CROISSANCE_PTF || 0) }}</strong>
                  </td>
                  <td><strong>{{ formatCurrency(territory.total.PRODUIT_INT_M1 || 0) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.total.PRODUIT_INT_M || 0) }}</strong></td>
                  <td :class="getVariationClass(territory.total.VARIATION_PRODUIT_INT || 0)">
                    <strong>{{ formatVariationCurrency(territory.total.VARIATION_PRODUIT_INT || 0) }}</strong>
                  </td>
                  <td :class="getGrowthRateClass(territory.total.TAUX_CROISSANCE_PRODUIT_INT || 0)">
                    <strong>{{ formatVariationPercent(territory.total.TAUX_CROISSANCE_PRODUIT_INT || 0) }}</strong>
                  </td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <tr 
                    v-for="agency in territory.data" 
                    :key="agency.CODE_AGENCE || agency.AGENCE" 
                    class="level-3-row"
                  >
                    <td class="level-3">{{ agency.AGENCE || agency.name }}</td>
                    <td>{{ formatCurrency(agency.PTF_M1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.PTF_M || 0) }}</td>
                    <td :class="getVariationClass(agency.VARIATION_PTF || 0)">
                      {{ formatVariationCurrency(agency.VARIATION_PTF || 0) }}
                    </td>
                    <td :class="getGrowthRateClass(agency.TAUX_CROISSANCE_PTF || 0)">
                      {{ formatVariationPercent(agency.TAUX_CROISSANCE_PTF || 0) }}
                    </td>
                    <td>{{ formatCurrency(agency.PRODUIT_INT_M1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.PRODUIT_INT_M || 0) }}</td>
                    <td :class="getVariationClass(agency.VARIATION_PRODUIT_INT || 0)">
                      {{ formatVariationCurrency(agency.VARIATION_PRODUIT_INT || 0) }}
                    </td>
                    <td :class="getGrowthRateClass(agency.TAUX_CROISSANCE_PRODUIT_INT || 0)">
                      {{ formatVariationPercent(agency.TAUX_CROISSANCE_PRODUIT_INT || 0) }}
                    </td>
                  </tr>
                </template>
              </template>
            </template>

            <!-- TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>{{ formatCurrency(totalData.PTF_M1 || 0) }}</strong></td>
              <td><strong>{{ formatCurrency(totalData.PTF_M || 0) }}</strong></td>
              <td :class="getVariationClass(totalData.VARIATION_PTF || 0)">
                <strong>{{ formatVariationCurrency(totalData.VARIATION_PTF || 0) }}</strong>
              </td>
              <td :class="getGrowthRateClass(totalData.TAUX_CROISSANCE_PTF || 0)">
                <strong>{{ formatVariationPercent(totalData.TAUX_CROISSANCE_PTF || 0) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(totalData.PRODUIT_INT_M1 || 0) }}</strong></td>
              <td><strong>{{ formatCurrency(totalData.PRODUIT_INT_M || 0) }}</strong></td>
              <td :class="getVariationClass(totalData.VARIATION_PRODUIT_INT || 0)">
                <strong>{{ formatVariationCurrency(totalData.VARIATION_PRODUIT_INT || 0) }}</strong>
              </td>
              <td :class="getGrowthRateClass(totalData.TAUX_CROISSANCE_PRODUIT_INT || 0)">
                <strong>{{ formatVariationPercent(totalData.TAUX_CROISSANCE_PRODUIT_INT || 0) }}</strong>
              </td>
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
  name: 'EncoursCreditSection',
  data() {
    const now = new Date();
    return {
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      loading: false,
      error: null,
      hierarchicalDataFromBackend: null,
      expandedSections: {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      }
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
    getPeriodTitle() {
      return `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
    },
    periodLabels() {
      const m1Month = this.selectedMonth === 1 ? 12 : this.selectedMonth - 1;
      const m1Year = this.selectedMonth === 1 ? this.selectedYear - 1 : this.selectedYear;
      return {
        m: `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`,
        m1: `${this.months[m1Month - 1]} ${m1Year}`
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
      return null;
    },
    filteredHierarchicalData() {
      return this.hierarchicalData;
    },
    territoireTotal() {
      if (!this.filteredHierarchicalData || !this.filteredHierarchicalData.TERRITOIRE) {
        return { PTF_M1: 0, PTF_M: 0, VARIATION_PTF: 0, TAUX_CROISSANCE_PTF: 0, PRODUIT_INT_M1: 0, PRODUIT_INT_M: 0, VARIATION_PRODUIT_INT: 0, TAUX_CROISSANCE_PRODUIT_INT: 0 };
      }
      
      let totalPTF_M1 = 0;
      let totalPTF_M = 0;
      let totalPROD_INT_M1 = 0;
      let totalPROD_INT_M = 0;
      
      // Les totaux territoire viennent de l’API déjà en millions de FCFA (comme les lignes agence)
      Object.values(this.filteredHierarchicalData.TERRITOIRE).forEach(territory => {
        if (territory.total) {
          totalPTF_M1 += territory.total.PTF_M1 || 0;
          totalPTF_M += territory.total.PTF_M || 0;
          totalPROD_INT_M1 += territory.total.PRODUIT_INT_M1 || 0;
          totalPROD_INT_M += territory.total.PRODUIT_INT_M || 0;
        }
      });
      
      const variationPTF = totalPTF_M - totalPTF_M1;
      const tauxCroissancePTF = totalPTF_M1 > 0 ? (variationPTF / totalPTF_M1) * 100 : 0;
      
      const variationProdInt = totalPROD_INT_M - totalPROD_INT_M1;
      const tauxCroissanceProdInt = totalPROD_INT_M1 > 0 ? (variationProdInt / totalPROD_INT_M1) * 100 : 0;
      
      return {
        PTF_M1: totalPTF_M1,
        PTF_M: totalPTF_M,
        VARIATION_PTF: variationPTF,
        TAUX_CROISSANCE_PTF: tauxCroissancePTF,
        PRODUIT_INT_M1: totalPROD_INT_M1,
        PRODUIT_INT_M: totalPROD_INT_M,
        VARIATION_PRODUIT_INT: variationProdInt,
        TAUX_CROISSANCE_PRODUIT_INT: tauxCroissanceProdInt
      };
    },
    totalData() {
      if (!this.filteredHierarchicalData || !this.filteredHierarchicalData.TERRITOIRE) {
        return { PTF_M1: 0, PTF_M: 0, VARIATION_PTF: 0, TAUX_CROISSANCE_PTF: 0, PRODUIT_INT_M1: 0, PRODUIT_INT_M: 0, VARIATION_PRODUIT_INT: 0, TAUX_CROISSANCE_PRODUIT_INT: 0 };
      }
      
      const territoire = this.territoireTotal;
      
      const totalPTF_M1 = territoire.PTF_M1;
      const totalPTF_M = territoire.PTF_M;
      const totalPROD_INT_M1 = territoire.PRODUIT_INT_M1;
      const totalPROD_INT_M = territoire.PRODUIT_INT_M;
      
      const variationPTF = totalPTF_M - totalPTF_M1;
      const tauxCroissancePTF = totalPTF_M1 > 0 ? (variationPTF / totalPTF_M1) * 100 : 0;
      
      const variationProdInt = totalPROD_INT_M - totalPROD_INT_M1;
      const tauxCroissanceProdInt = totalPROD_INT_M1 > 0 ? (variationProdInt / totalPROD_INT_M1) * 100 : 0;
      
      return {
        PTF_M1: totalPTF_M1,
        PTF_M: totalPTF_M,
        VARIATION_PTF: variationPTF,
        TAUX_CROISSANCE_PTF: tauxCroissancePTF,
        PRODUIT_INT_M1: totalPROD_INT_M1,
        PRODUIT_INT_M: totalPROD_INT_M,
        VARIATION_PRODUIT_INT: variationProdInt,
        TAUX_CROISSANCE_PRODUIT_INT: tauxCroissanceProdInt
      };
    }
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    async fetchData() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get('/api/oracle/data/encours-credit', {
          params: {
            month_m: this.selectedMonth,
            year_m: this.selectedYear
          }
        });
        
        if (response.data && response.data.hierarchicalData) {
          this.hierarchicalDataFromBackend = response.data.hierarchicalData;
        } else if (response.data && response.data.data) {
          // Fallback si pas de structure hiérarchique
          this.hierarchicalDataFromBackend = { TERRITOIRE: {} };
        } else {
          this.hierarchicalDataFromBackend = { TERRITOIRE: {} };
        }
      } catch (err) {
        console.error('Erreur lors de la récupération des données encours crédit:', err);
        
        let errorMessage = 'Erreur lors de la récupération des données';
        
        // Détecter les erreurs de timeout
        const errorDetail = err.response?.data?.detail || err.response?.data?.error || '';
        const isTimeout = err.code === 'ECONNABORTED' || 
                         err.message?.includes('timeout') || 
                         err.message?.includes('timed out') ||
                         errorDetail.includes('timeout') ||
                         errorDetail.includes('cURL error 28') ||
                         errorDetail.includes('Operation timed out');
        
        if (isTimeout) {
          errorMessage = `⏱️ Le chargement prend plus de temps que prévu. Les calculs Oracle sont en cours, veuillez patienter. Vous pouvez rafraîchir la page dans quelques instants.`;
        } else if (err.response) {
          errorMessage = err.response.data?.detail || err.response.data?.error || `Erreur HTTP ${err.response.status}`;
        } else if (err.request) {
          errorMessage = `⚠️ Impossible de se connecter au service Python`;
        } else {
          errorMessage = err.message || 'Erreur inconnue';
        }
        
        this.error = errorMessage;
        this.hierarchicalDataFromBackend = { TERRITOIRE: {} };
      } finally {
        this.loading = false;
      }
    },
    handleMonthChange() {
      this.fetchData();
    },
    handleYearChange() {
      this.fetchData();
    },
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    formatCurrency(value) {
      if (value === null || value === undefined || isNaN(value)) return '0,00 M F CFA';
      // Valeurs API déjà en millions de FCFA
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value) + ' M F CFA';
    },
    formatVariationCurrency(value) {
      if (value === null || value === undefined || isNaN(value)) return '-';
      const formatted = new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(Math.abs(value));
      return value >= 0 ? `+${formatted}` : `-${formatted}`;
    },
    formatVariationPercent(value) {
      if (value === null || value === undefined || isNaN(value)) return '0%';
      return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value) + '%';
    },
    getVariationClass(value) {
      if (value > 0) return 'positive';
      if (value < 0) return 'negative';
      return '';
    },
    getGrowthRateClass(value) {
      if (value > 0) return 'positive';
      if (value < 0) return 'negative';
      return '';
    }
  }
};
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

.month-select:hover,
.year-select:hover {
  border-color: #1A4D3A;
}

.month-select:focus,
.year-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.1);
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

.total-row {
  background: #DC2626;
  font-weight: 600;
  color: white;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
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

.loading-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
  border: 2px solid #0EA5E9;
  border-radius: 8px;
  color: #0369A1;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid #BAE6FD;
  border-top: 3px solid #0EA5E9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  text-align: left;
  background: #FEF2F2;
  border: 2px solid #EF4444;
  border-radius: 8px;
  color: #DC2626;
  font-weight: 500;
  margin: 20px 0;
  white-space: pre-line;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .section-header {
    flex-wrap: wrap;
    gap: 15px;
  }
  
  .agencies-table {
    min-width: 1000px;
    font-size: 12px;
  }
  
  .agencies-table th {
    padding: 10px 6px;
    font-size: 11px;
  }
  
  .agencies-table td {
    padding: 8px 6px;
    font-size: 12px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .client-section {
    padding: 15px;
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
  .year-select {
    flex: 1;
    min-width: 120px;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .agencies-table {
    min-width: 900px;
    font-size: 11px;
  }
  
  .agencies-table th {
    padding: 8px 4px;
    font-size: 10px;
  }
  
  .agencies-table td {
    padding: 6px 4px;
    font-size: 11px;
  }
  
  .agencies-table th:first-child,
  .agencies-table td:first-child {
    padding-left: 10px;
  }
  
  .level-1 {
    font-size: 14px;
    padding-left: 10px !important;
  }
  
  .level-2 {
    font-size: 13px;
    padding-left: 25px !important;
  }
  
  .loading-banner {
    padding: 10px 15px;
    font-size: 13px;
  }
  
  .error-message {
    padding: 12px 15px;
    font-size: 13px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .client-section {
    padding: 10px;
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
  .year-select {
    width: 100%;
    min-width: 100%;
    padding: 8px 10px;
    font-size: 12px;
  }
  
  .agencies-table {
    min-width: 800px;
    font-size: 10px;
  }
  
  .agencies-table th {
    padding: 6px 3px;
    font-size: 9px;
  }
  
  .agencies-table td {
    padding: 5px 3px;
    font-size: 10px;
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
  
  .loading-banner {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .error-message {
    padding: 10px 12px;
    font-size: 12px;
  }
}
</style>
