<template>
  <div class="prepaid-card-sales-section">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-text">Vente Cartes <span class="title-highlight">prépayées</span></span>
        <span class="card-icon">💳</span>
      </h2>
    </div>

    <div class="content-container">
      <!-- Message de chargement en haut -->
      <div v-if="loading" class="loading-banner">
        <div class="loading-spinner"></div>
        <span>Chargement des données en cours... Cette opération peut prendre quelques instants.</span>
      </div>
      
      <!-- Message d'erreur -->
      <div v-if="error && !loading" class="error-message">
        <p>{{ error }}</p>
        <button @click="fetchPrepaidCardSalesData" class="retry-btn">Réessayer</button>
      </div>
      
      <!-- Message si pas de données -->
      <div v-if="!loading && !error && !hierarchicalData" class="info-message">
        <p>ℹ️ Aucune donnée disponible.</p>
        <button @click="fetchPrepaidCardSalesData" class="retry-btn">Charger les données</button>
      </div>
      
      <!-- Tableau de données -->
      <div v-if="!loading" class="table-container">
        <table class="sales-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Objectif</th>
              <th>Vente CofiCarte M-1</th>
              <th>Vente CofiCarte M</th>
              <th>Variation (nombre)</th>
              <th>Variation (%)</th>
              <th>Atteinte</th>
              <th>Contribution agence</th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr v-if="territoireTotal" class="category-row">
              <td class="category-cell">
                <button @click="toggleSection('TERRITOIRE')" class="expand-btn">
                  {{ expandedSections.TERRITOIRE ? '-' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>{{ formatNumber(territoireTotal.objectif) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.m1) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.m) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.variation)">
                <strong>{{ formatNumber(territoireTotal.variation) }}</strong>
              </td>
              <td :class="getVariationClass(territoireTotal.variation_pourcent)">
                <strong>{{ formatPercent(territoireTotal.variation_pourcent) }}</strong>
              </td>
              <td :class="getAtteinteClass(territoireTotal.atteinte)">
                <strong>{{ formatPercent(territoireTotal.atteinte) }}</strong>
              </td>
              <td class="contribution">
                <strong>{{ formatPercent(territoireTotal.contribution) }}</strong>
              </td>
            </tr>

            <!-- TERRITOIRES -->
            <template v-if="hierarchicalData && hierarchicalData.TERRITOIRE && Object.keys(hierarchicalData.TERRITOIRE).length > 0">
              <template v-for="(territory, territoryKey) in hierarchicalData.TERRITOIRE" :key="territoryKey">
                <tr class="sub-agency level-2-row">
                  <td class="indent-cell level-2">
                    <button @click="toggleSection(`TERRITOIRE_${territoryKey}`)" class="expand-btn">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '-' : '+' }}
                    </button>
                    {{ territory.name || territoryKey }}
                  </td>
                  <td><strong>{{ formatNumber(territory.total?.objectif) }}</strong></td>
                  <td><strong>{{ formatNumber(territory.total?.m1) }}</strong></td>
                  <td>
                    <strong>
                      <span class="with-indicator">{{ formatNumber(territory.total?.m) }}</span>
                      <span v-if="territory.total && territory.total.m > territory.total.m1" class="indicator-up">▲</span>
                    </strong>
                  </td>
                  <td :class="getVariationClass(territory.total?.variation)">
                    <strong>{{ formatNumber(territory.total?.variation) }}</strong>
                  </td>
                  <td :class="getVariationClass(territory.total?.variation_pourcent)">
                    <strong>{{ formatPercent(territory.total?.variation_pourcent) }}</strong>
                  </td>
                  <td :class="getAtteinteClass(territory.total?.atteinte)">
                    <strong>{{ formatPercent(territory.total?.atteinte) }}</strong>
                  </td>
                  <td class="contribution">
                    <strong>{{ formatPercent(territory.total?.contribution) }}</strong>
                  </td>
                </tr>
                
                <!-- Agences du territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`] && territory.data">
                  <tr v-for="agency in territory.data" :key="agency.CODE_AGENCE || agency.AGENCE" class="sub-agency">
                    <td class="indent-cell level-3">{{ agency.AGENCE || agency.DESCRIPTION }}</td>
                    <td>{{ formatNumber(agency.OBJECTIF_COFICARTE || agency.objectif) }}</td>
                    <td>{{ formatNumber(agency.NOMBRE_COFICARTE_VENDU_M_1 || agency.m1) }}</td>
                    <td>{{ formatNumber(agency.NOMBRE_COFICARTE_VENDU_M || agency.m) }}</td>
                    <td :class="getVariationClass(agency.Variation_Nombre || agency.variationNombre)">
                      {{ formatNumber(agency.Variation_Nombre || agency.variationNombre) }}
                    </td>
                    <td :class="getVariationClass(agency['VARIATION%'] || agency.variationPourcent)">
                      {{ formatPercent(agency['VARIATION%'] || agency.variationPourcent) }}
                    </td>
                    <td :class="getAtteinteClass(agency.TAUX_REALISATION || agency.atteinte)">
                      {{ formatPercent(agency.TAUX_REALISATION || agency.atteinte) }}
                    </td>
                    <td class="contribution">
                      {{ formatPercent(agency.CONTRIBUTION || agency.contribution) }}
                    </td>
                  </tr>
                </template>
              </template>
            </template>

            <!-- POINT SERVICES -->
            <tr v-if="servicePointsTotal && hierarchicalData && hierarchicalData['POINT SERVICES']" class="category-row">
              <td class="category-cell">
                <button @click="toggleSection('POINT SERVICES')" class="expand-btn">
                  {{ expandedSections['POINT SERVICES'] ? '-' : '+' }}
                </button>
                <strong>POINT SERVICES</strong>
              </td>
              <td><strong>{{ formatNumber(servicePointsTotal.objectif) }}</strong></td>
              <td><strong>{{ formatNumber(servicePointsTotal.m1) }}</strong></td>
              <td><strong>{{ formatNumber(servicePointsTotal.m) }}</strong></td>
              <td :class="getVariationClass(servicePointsTotal.variation)">
                <strong>{{ formatNumber(servicePointsTotal.variation) }}</strong>
              </td>
              <td :class="getVariationClass(servicePointsTotal.variation_pourcent)">
                <strong>{{ formatPercent(servicePointsTotal.variation_pourcent) }}</strong>
              </td>
              <td :class="getAtteinteClass(servicePointsTotal.atteinte)">
                <strong>{{ formatPercent(servicePointsTotal.atteinte) }}</strong>
              </td>
              <td class="contribution">
                <strong>{{ formatPercent(servicePointsTotal.contribution) }}</strong>
              </td>
            </tr>
            
            <!-- Agences des points de service -->
            <template v-if="expandedSections['POINT SERVICES'] && hierarchicalData && hierarchicalData['POINT SERVICES']">
              <template v-if="hierarchicalData['POINT SERVICES'].service_points && hierarchicalData['POINT SERVICES'].service_points.data && hierarchicalData['POINT SERVICES'].service_points.data.length > 0">
                <tr v-for="(agency, index) in hierarchicalData['POINT SERVICES'].service_points.data" 
                    :key="`sp-${agency.CODE_AGENCE || agency.AGENCE || index}`" 
                    class="sub-agency">
                  <td class="indent-cell level-2">{{ agency.AGENCE || agency.DESCRIPTION || 'N/A' }}</td>
                  <td>{{ formatNumber(agency.OBJECTIF_COFICARTE || agency.objectif) }}</td>
                  <td>{{ formatNumber(agency.NOMBRE_COFICARTE_VENDU_M_1 || agency.m1) }}</td>
                  <td>{{ formatNumber(agency.NOMBRE_COFICARTE_VENDU_M || agency.m) }}</td>
                  <td :class="getVariationClass(agency.Variation_Nombre || agency.variationNombre)">
                    {{ formatNumber(agency.Variation_Nombre || agency.variationNombre) }}
                  </td>
                  <td :class="getVariationClass(agency['VARIATION%'] || agency.variationPourcent)">
                    {{ formatPercent(agency['VARIATION%'] || agency.variationPourcent) }}
                  </td>
                  <td :class="getAtteinteClass(agency.TAUX_REALISATION || agency.atteinte)">
                    {{ formatPercent(agency.TAUX_REALISATION || agency.atteinte) }}
                  </td>
                  <td class="contribution">
                    {{ formatPercent(agency.CONTRIBUTION || agency.contribution) }}
                  </td>
                </tr>
              </template>
              <tr v-else class="no-data-sub-row">
                <td colspan="8" class="indent-cell level-2" style="text-align: center; color: #999; padding: 20px;">
                  Aucune agence de point de service disponible
                </td>
              </tr>
            </template>

            <!-- TOTAL -->
            <tr v-if="globalTotal && hierarchicalData" class="total-row">
              <td class="category-cell">TOTAL</td>
              <td>{{ formatNumber(globalTotal.objectif) }}</td>
              <td>{{ formatNumber(globalTotal.m1) }}</td>
              <td>{{ formatNumber(globalTotal.m) }}</td>
              <td :class="getVariationClass(globalTotal.variation)">
                {{ formatNumber(globalTotal.variation) }}
              </td>
              <td :class="getVariationClass(globalTotal.variation_pourcent)">
                {{ formatPercent(globalTotal.variation_pourcent) }}
              </td>
              <td :class="getAtteinteClass(globalTotal.atteinte)">
                {{ formatPercent(globalTotal.atteinte) }}
              </td>
              <td>-</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Graphiques -->
      <div class="charts-container">
        <!-- TOP 5 Chart -->
        <div class="chart-wrapper">
          <h3 class="chart-title">TOP 5 VENTE COFI'CARTES</h3>
          <div class="chart-container">
            <canvas ref="top5Chart"></canvas>
          </div>
        </div>

        <!-- FLOP 5 Chart -->
        <div class="chart-wrapper">
          <h3 class="chart-title">FLOP 5 VENTE COFI'CARTES</h3>
          <div class="chart-container">
            <canvas ref="flop5Chart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  BarController,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

// S'assurer que tous les composants nécessaires sont enregistrés
// Dans Chart.js v4, BarElement inclut automatiquement le contrôleur
function ensureChartRegistered() {
  if (typeof ChartJS === 'undefined') {
    console.error('❌ Chart.js n\'est pas défini');
    return false;
  }
  
  try {
    // Vérifier si le contrôleur est déjà enregistré
    const registry = ChartJS.registry;
    if (registry) {
      try {
        const barController = registry.getController('bar');
        if (barController) {
          console.log('✅ Contrôleur bar déjà enregistré');
          return true;
        }
      } catch (e) {
        // Le contrôleur n'est pas enregistré, continuer
      }
    }
    
    // Enregistrer les composants
    ChartJS.register(
      CategoryScale,
      LinearScale,
      BarElement,
      BarController,
      Title,
      Tooltip,
      Legend
    );
    console.log('✅ Chart.js composants enregistrés avec succès (incluant BarController)');
    return true;
  } catch (error) {
    // Ignorer si déjà enregistré
    if (error.message && error.message.includes('already registered')) {
      console.log('✅ Chart.js déjà enregistré');
      return true;
    }
    console.error('❌ Erreur lors de l\'enregistrement de Chart.js:', error);
    return false;
  }
}

// Enregistrer immédiatement
ensureChartRegistered();

export default {
  name: 'PrepaidCardSalesSection',
  data() {
    const now = new Date();
    return {
      loading: false,
      error: null,
      hierarchicalData: null,
      expandedSections: {
        TERRITOIRE: true,
        'POINT SERVICES': false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false,
        'POINT SERVICES_service_points': false
      },
      selectedPeriod: 'month',
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      top5ChartInstance: null,
      flop5ChartInstance: null
    };
  },
  computed: {
    territoireTotal() {
      if (!this.hierarchicalData || !this.hierarchicalData.TERRITOIRE) return null;
      const territories = this.hierarchicalData.TERRITOIRE;
      let total = { objectif: 0, m1: 0, m: 0, variation: 0, variation_pourcent: 0, atteinte: 0, contribution: 0 };
      Object.values(territories).forEach(territory => {
        if (territory && territory.total) {
          total.objectif += territory.total.objectif || 0;
          total.m1 += territory.total.m1 || 0;
          total.m += territory.total.m || 0;
        }
      });
      total.variation = total.m - total.m1;
      if (total.m1 > 0) {
        total.variation_pourcent = Math.round((total.variation / total.m1) * 100);
      }
      if (total.objectif > 0) {
        total.atteinte = Math.round((total.m / total.objectif) * 100);
      }
      const globalTotal = total.m + (this.servicePointsTotal?.m || 0);
      if (globalTotal > 0) {
        total.contribution = Math.round((total.m / globalTotal) * 100);
      }
      return total;
    },
    servicePointsTotal() {
      if (!this.hierarchicalData || !this.hierarchicalData['POINT SERVICES']) return null;
      const sp = this.hierarchicalData['POINT SERVICES'].service_points;
      return sp && sp.total ? sp.total : null;
    },
    globalTotal() {
      const territoire = this.territoireTotal || { m: 0, m1: 0, objectif: 0 };
      const servicePoints = this.servicePointsTotal || { m: 0, m1: 0, objectif: 0 };
      return {
        objectif: territoire.objectif + servicePoints.objectif,
        m1: territoire.m1 + servicePoints.m1,
        m: territoire.m + servicePoints.m,
        variation: (territoire.m + servicePoints.m) - (territoire.m1 + servicePoints.m1),
        variation_pourcent: territoire.m1 + servicePoints.m1 > 0 
          ? Math.round((((territoire.m + servicePoints.m) - (territoire.m1 + servicePoints.m1)) / (territoire.m1 + servicePoints.m1)) * 100)
          : 0,
        atteinte: territoire.objectif + servicePoints.objectif > 0
          ? Math.round(((territoire.m + servicePoints.m) / (territoire.objectif + servicePoints.objectif)) * 100)
          : 0
      };
    },
    top5Agencies() {
      if (!this.hierarchicalData) return [];
      const allAgencies = [];
      if (this.hierarchicalData.TERRITOIRE) {
        Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.data) {
            allAgencies.push(...territory.data);
          }
        });
      }
      if (this.hierarchicalData['POINT SERVICES'] && this.hierarchicalData['POINT SERVICES'].service_points) {
        allAgencies.push(...(this.hierarchicalData['POINT SERVICES'].service_points.data || []));
      }
      return allAgencies
        .sort((a, b) => (b.NOMBRE_COFICARTE_VENDU_M || 0) - (a.NOMBRE_COFICARTE_VENDU_M || 0))
        .slice(0, 5);
    },
    flop5Agencies() {
      if (!this.hierarchicalData) return [];
      const allAgencies = [];
      if (this.hierarchicalData.TERRITOIRE) {
        Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.data) {
            allAgencies.push(...territory.data);
          }
        });
      }
      if (this.hierarchicalData['POINT SERVICES'] && this.hierarchicalData['POINT SERVICES'].service_points) {
        allAgencies.push(...(this.hierarchicalData['POINT SERVICES'].service_points.data || []));
      }
      return allAgencies
        .filter(a => (a.NOMBRE_COFICARTE_VENDU_M || 0) > 0)
        .sort((a, b) => (a.NOMBRE_COFICARTE_VENDU_M || 0) - (b.NOMBRE_COFICARTE_VENDU_M || 0))
        .slice(0, 5);
    }
  },
  mounted() {
    this.fetchPrepaidCardSalesData();
  },
  beforeUnmount() {
    if (this.top5ChartInstance) {
      try {
        this.top5ChartInstance.destroy();
      } catch (e) {
        console.warn('Erreur lors de la destruction du graphique TOP 5:', e);
      }
      this.top5ChartInstance = null;
    }
    if (this.flop5ChartInstance) {
      try {
        this.flop5ChartInstance.destroy();
      } catch (e) {
        console.warn('Erreur lors de la destruction du graphique FLOP 5:', e);
      }
      this.flop5ChartInstance = null;
    }
  },
  watch: {
    hierarchicalData: {
      handler() {
        this.$nextTick(() => {
          this.createCharts();
        });
      },
      deep: true
    }
  },
  methods: {
    async fetchPrepaidCardSalesData() {
      this.loading = true;
      this.error = null;
      
      try {
        const params = {
          period: this.selectedPeriod
        };
        
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        params._t = Date.now();
        
        const response = await window.axios.get('/api/oracle/data/prepaid-card-sales', {
          params,
          timeout: 300000,
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        
        let data = null;
        if (response.data && response.data.data) {
          data = response.data.data;
        } else if (response.data) {
          data = response.data;
        }
        
        if (data && data.hierarchicalData) {
          this.hierarchicalData = data.hierarchicalData;
          console.log('✅ Données récupérées:', this.hierarchicalData);
          console.log('📋 POINT SERVICES:', this.hierarchicalData['POINT SERVICES']);
          if (this.hierarchicalData['POINT SERVICES'] && this.hierarchicalData['POINT SERVICES'].service_points) {
            console.log('📋 service_points.data:', this.hierarchicalData['POINT SERVICES'].service_points.data);
            console.log('📋 Nombre d\'agences:', this.hierarchicalData['POINT SERVICES'].service_points.data?.length || 0);
          }
          // Attendre que le DOM soit mis à jour puis créer les graphiques
          this.$nextTick(() => {
            setTimeout(() => {
              this.createCharts();
            }, 100);
          });
        } else {
          throw new Error('Format de données inattendu');
        }
      } catch (error) {
        console.error('❌ Erreur lors de la récupération des données:', error);
        this.error = error.response?.data?.detail || error.message || 'Erreur lors de la récupération des données';
      } finally {
        this.loading = false;
      }
    },
    toggleSection(sectionKey) {
      this.expandedSections[sectionKey] = !this.expandedSections[sectionKey];
    },
    createCharts() {
      console.log('📊 Création des graphiques...');
      console.log('📊 top5Agencies:', this.top5Agencies);
      console.log('📊 flop5Agencies:', this.flop5Agencies);
      
      // S'assurer que Chart.js est enregistré
      if (!ensureChartRegistered()) {
        console.error('❌ Impossible d\'enregistrer Chart.js');
        return;
      }
      
      // Vérifier que Chart.js est bien chargé
      if (typeof ChartJS === 'undefined') {
        console.error('❌ Chart.js n\'est pas chargé');
        return;
      }
      
      // Vérifier que le contrôleur 'bar' est disponible
      try {
        const registry = ChartJS.registry;
        if (registry) {
          const barController = registry.getController('bar');
          if (!barController) {
            console.error('❌ Contrôleur bar non trouvé dans le registre après enregistrement');
            return;
          }
          console.log('✅ Contrôleur bar trouvé dans le registre');
        }
      } catch (e) {
        console.warn('⚠️ Impossible de vérifier le registre:', e);
        // Continuer quand même, peut-être que le registre n'est pas accessible de cette façon
      }
      
      // Détruire les graphiques existants d'abord
      if (this.top5ChartInstance) {
        try {
          this.top5ChartInstance.destroy();
        } catch (e) {
          console.warn('Erreur lors de la destruction du graphique TOP 5:', e);
        }
        this.top5ChartInstance = null;
      }
      
      if (this.flop5ChartInstance) {
        try {
          this.flop5ChartInstance.destroy();
        } catch (e) {
          console.warn('Erreur lors de la destruction du graphique FLOP 5:', e);
        }
        this.flop5ChartInstance = null;
      }
      
      this.$nextTick(() => {
        // Attendre un peu pour s'assurer que Chart.js est prêt
        setTimeout(() => {
          // TOP 5 Chart
          const top5Canvas = this.$refs.top5Chart;
          console.log('📊 top5Canvas:', top5Canvas);
          console.log('📊 top5Agencies.length:', this.top5Agencies?.length || 0);
          
          if (top5Canvas) {
            if (this.top5Agencies && this.top5Agencies.length > 0) {
              const ctx = top5Canvas.getContext('2d');
              if (ctx) {
                // Vérifier si un graphique existe déjà sur ce canvas
                try {
                  const existingChart = ChartJS.getChart(ctx);
                  if (existingChart) {
                    existingChart.destroy();
                  }
                } catch (e) {
                  console.warn('⚠️ Erreur lors de la vérification du graphique existant:', e);
                }
              
              const maxValue = Math.max(...this.top5Agencies.map(a => a.NOMBRE_COFICARTE_VENDU_M || 0));
              const normalizedData = this.top5Agencies.map(a => {
                const value = a.NOMBRE_COFICARTE_VENDU_M || 0;
                return maxValue > 0 ? (value / maxValue) * 2 : 0;
              });
              
              this.top5ChartInstance = new ChartJS(ctx, {
                type: 'bar',
                data: {
                  labels: this.top5Agencies.map(a => a.AGENCE || 'N/A'),
                  datasets: [{
                    label: 'Vente Cofi\'cartes',
                    data: normalizedData,
                    backgroundColor: '#DC2626',
                    borderRadius: 0
                  }]
                },
                options: {
                  indexAxis: 'y',
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      titleColor: '#fff',
                      bodyColor: '#fff',
                      padding: 10,
                      callbacks: {
                        label: (context) => {
                          const index = context.dataIndex;
                          const agency = this.top5Agencies[index];
                          return `Vente: ${agency.NOMBRE_COFICARTE_VENDU_M || 0}`;
                        }
                      }
                    }
                  },
                  scales: {
                    x: {
                      beginAtZero: true,
                      max: 2,
                      ticks: {
                        stepSize: 0.5,
                        font: { size: 11 },
                        color: '#e5e7eb'
                      },
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        lineWidth: 1
                      }
                    },
                    y: {
                      ticks: {
                        font: { size: 11 },
                        color: '#e5e7eb'
                      },
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        lineWidth: 1
                      }
                    }
                  }
                }
              });
              console.log('✅ Graphique TOP 5 créé');
            } else {
              console.warn('⚠️ Impossible d\'obtenir le contexte 2D pour TOP 5');
            }
          } else {
            console.warn('⚠️ Pas de données pour TOP 5');
          }
        } else {
          console.warn('⚠️ Canvas TOP 5 non trouvé');
        }
          
          // FLOP 5 Chart
          const flop5Canvas = this.$refs.flop5Chart;
          console.log('📊 flop5Canvas:', flop5Canvas);
          console.log('📊 flop5Agencies.length:', this.flop5Agencies?.length || 0);
          
          if (flop5Canvas) {
            if (this.flop5Agencies && this.flop5Agencies.length > 0) {
              const ctx = flop5Canvas.getContext('2d');
              if (ctx) {
                // Vérifier si un graphique existe déjà sur ce canvas
                try {
                  const existingChart = ChartJS.getChart(ctx);
                  if (existingChart) {
                    existingChart.destroy();
                  }
                } catch (e) {
                  console.warn('⚠️ Erreur lors de la vérification du graphique existant:', e);
                }
              
              const maxValue = Math.max(...this.flop5Agencies.map(a => a.NOMBRE_COFICARTE_VENDU_M || 0));
              const normalizedData = this.flop5Agencies.map(a => {
                const value = a.NOMBRE_COFICARTE_VENDU_M || 0;
                return maxValue > 0 ? (value / maxValue) * 0.16 : 0;
              });
              
              this.flop5ChartInstance = new ChartJS(ctx, {
                type: 'bar',
                data: {
                  labels: this.flop5Agencies.map(a => a.AGENCE || 'N/A'),
                  datasets: [{
                    label: 'Vente Cofi\'cartes',
                    data: normalizedData,
                    backgroundColor: '#DC2626',
                    borderRadius: 0
                  }]
                },
                options: {
                  indexAxis: 'y',
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      titleColor: '#fff',
                      bodyColor: '#fff',
                      padding: 10,
                      callbacks: {
                        label: (context) => {
                          const index = context.dataIndex;
                          const agency = this.flop5Agencies[index];
                          return `Vente: ${agency.NOMBRE_COFICARTE_VENDU_M || 0}`;
                        }
                      }
                    }
                  },
                  scales: {
                    x: {
                      beginAtZero: true,
                      max: 0.16,
                      ticks: {
                        stepSize: 0.02,
                        font: { size: 11 },
                        color: '#e5e7eb'
                      },
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        lineWidth: 1
                      }
                    },
                    y: {
                      ticks: {
                        font: { size: 11 },
                        color: '#e5e7eb'
                      },
                      grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        lineWidth: 1
                      }
                    }
                  }
                }
              });
              console.log('✅ Graphique FLOP 5 créé');
            } else {
              console.warn('⚠️ Impossible d\'obtenir le contexte 2D pour FLOP 5');
            }
          } else {
            console.warn('⚠️ Pas de données pour FLOP 5');
          }
        } else {
          console.warn('⚠️ Canvas FLOP 5 non trouvé');
        }
        }, 100);
      });
    },
    formatNumber(value) {
      if (value === null || value === undefined || value === '') return '-';
      return Number(value).toLocaleString('fr-FR');
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '') return '-';
      return `${Math.round(Number(value))}%`;
    },
    getVariationClass(variation) {
      if (variation === null || variation === undefined || variation === '') return '';
      const num = Number(variation);
      return num >= 0 ? 'positive' : 'negative';
    },
    getAtteinteClass(atteinte) {
      if (atteinte === null || atteinte === undefined || atteinte === '') return '';
      const num = Number(atteinte);
      return num >= 100 ? 'positive' : 'negative';
    }
  }
}
</script>

<style scoped>
.prepaid-card-sales-section {
  width: 100%;
  padding: 30px;
  background: #FFFFFF;
  min-height: calc(100vh - 100px);
  position: relative;
}

.section-header {
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

.section-title {
  font-size: 36px;
  font-weight: 800;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 15px;
  letter-spacing: 1px;
}

.title-text {
  color: #1f2937;
}

.title-highlight {
  color: #DC2626;
  -webkit-text-fill-color: #DC2626;
}

.card-icon {
  font-size: 40px;
  color: #DC2626;
  filter: 
    drop-shadow(0 0 10px rgba(220, 38, 38, 0.8))
    drop-shadow(0 0 20px rgba(220, 38, 38, 0.4));
}

.content-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
  position: relative;
  z-index: 1;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sales-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  min-width: 1200px;
  font-size: 13px;
}

.sales-table thead {
  background: #DC2626;
  color: white;
}

.sales-table th {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  border-right: 1px solid #444;
  white-space: nowrap;
}

.sales-table th:first-child {
  text-align: left;
  padding-left: 16px;
}

.sales-table td {
  padding: 10px 8px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #EEE;
  border-right: 1px solid #F0F0F0;
}

.sales-table td:first-child {
  text-align: left;
  padding-left: 16px;
}

.category-row {
  background: #2A2A2A;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.category-cell {
  font-size: 16px;
  padding-left: 16px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.sub-agency {
  background: white;
}

.sub-agency:hover {
  background: #f5f5f5;
}

.indent-cell {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
}

.level-2 {
  padding-left: 32px !important;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: white !important;
}

.level-2-row {
  background: #4A4A4A !important;
  color: white !important;
  font-weight: 600;
  cursor: pointer;
}

.level-2-row:hover {
  background: #5A5A5A !important;
}

.level-2-row td {
  color: white !important;
}

.level-3 {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
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

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.category-cell {
  font-size: 16px;
  padding-left: 16px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.positive {
  color: #10B981;
  font-weight: 600;
}

.negative {
  color: #EF4444;
  font-weight: 600;
}

.contribution {
  color: #10B981;
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

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
  color: #333;
}

.with-indicator {
  display: inline-block;
  margin-right: 5px;
}

.indicator-up {
  color: #10B981;
  font-size: 12px;
  display: inline-block;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.chart-wrapper {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: none;
  min-height: 250px;
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 15px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-container {
  height: 200px;
  position: relative;
  background: #2a2a2a;
  flex: 1;
  width: 100%;
  min-height: 200px;
  display: block;
}

.chart-container canvas {
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  max-width: 100%;
}

@media (max-width: 1200px) {
  .content-container {
    grid-template-columns: 1fr;
  }
  
  .charts-container {
    flex-direction: row;
  }
  
  .chart-wrapper {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .prepaid-card-sales-section {
    padding: 15px;
  }
  
  .section-title {
    font-size: 24px;
  }
  
  .card-icon {
    font-size: 28px;
  }
  
  .charts-container {
    flex-direction: column;
  }
  
  .sales-table {
    font-size: 11px;
  }
  
  .sales-table th,
  .sales-table td {
    padding: 8px 4px;
  }
}

.loading-banner {
  padding: 15px 20px;
  background: #f0f9ff;
  border: 1px solid #0ea5e9;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0369a1;
  font-weight: 500;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #e0f2fe;
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  text-align: center;
  background: #fee;
  border: 1px solid #DC2626;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #DC2626;
}

.info-message {
  padding: 20px;
  text-align: center;
  background: #f0f9ff;
  border: 1px solid #0ea5e9;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #0369a1;
}

.retry-btn {
  margin-top: 10px;
  padding: 8px 16px;
  background: #DC2626;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.retry-btn:hover {
  background: #b91c1c;
}

</style>
