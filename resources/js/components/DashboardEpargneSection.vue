<template>
  <div class="dashboard-epargne-section">
    <!-- Section de sélection de période -->
    <div class="period-selector-section">
      <div class="period-selector">
        <label class="period-label">Période :</label>
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

    <!-- Indicateur de chargement -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p class="loading-text">Chargement des données...</p>
      </div>
    </div>

    <!-- Section KPIs -->
    <div class="kpi-section" :class="{ 'loading-blur': loading }">
      <div class="kpi-grid">
        <div class="kpi-box kpi-primary">
          <div class="kpi-icon">💰</div>
          <div class="kpi-label">ENCOURS_TOTAL_M</div>
          <div class="kpi-value">{{ formatNumber(kpiData.encoursTotalM) }}</div>
        </div>
        <div class="kpi-box kpi-blue">
          <div class="kpi-icon">🏦</div>
          <div class="kpi-label">ENCOURS_COMPTE_COURANT</div>
          <div class="kpi-value">{{ formatNumber(kpiData.encoursCompteCourant) }}</div>
        </div>
        <div class="kpi-box kpi-green">
          <div class="kpi-icon">💵</div>
          <div class="kpi-label">ENCOURS_COMPTE_EPARGNE</div>
          <div class="kpi-value">{{ formatNumber(kpiData.encoursCompteEpargne) }}</div>
        </div>
        <div class="kpi-box kpi-orange">
          <div class="kpi-icon">📊</div>
          <div class="kpi-label">ENCOURS_DAT</div>
          <div class="kpi-value">{{ formatNumber(kpiData.encoursDat) }}</div>
        </div>
        <div class="kpi-box kpi-purple">
          <div class="kpi-icon">🎯</div>
          <div class="kpi-label">COMPTE_EPARGNE_PROJ</div>
          <div class="kpi-value">{{ formatNumber(kpiData.compteEpargneProj) }}</div>
        </div>
        <div class="kpi-box kpi-teal">
          <div class="kpi-icon">🔒</div>
          <div class="kpi-label">ENCOURS_DEPOT_GARANT</div>
          <div class="kpi-value">{{ formatNumber(kpiData.encoursDepotGarant) }}</div>
        </div>
        <div class="kpi-box kpi-red">
          <div class="kpi-icon">📈</div>
          <div class="kpi-label">TAUX DE COUVERTURE RESEAU</div>
          <div class="kpi-value">{{ kpiData.tauxCouvertureReseau }}%</div>
        </div>
      </div>
    </div>

    <!-- Section principale avec filtres et graphique -->
    <div class="main-dashboard-section" :class="{ 'loading-blur': loading }">
      <!-- Left Panel - Filtre AGENCE -->
      <div class="filter-panel left-panel">
        <div class="filter-header">
          <span class="filter-icon">🔍</span>
          <h3 class="filter-title">AGENCE</h3>
        </div>
        <div class="filter-list">
          <div v-if="filteredAgencies.length === 0" class="filter-empty">
            Aucune agence disponible pour cette zone
          </div>
          <div 
            v-for="agency in filteredAgencies" 
            :key="agency"
            class="filter-item"
            :class="{ active: selectedAgency === agency }"
            @click="toggleAgency(agency)"
            :title="agency"
          >
            {{ agency }}
          </div>
        </div>
      </div>

      <!-- Center Panel - Graphique -->
      <div class="chart-panel">
        <div class="chart-header">
          <h3 class="chart-title">Somme de ENCOURS_TOTAL_M ENCOURS_COMPTE_EPARGNE</h3>
          <select v-model="selectedZone" class="zone-select" @change="updateChart">
            <option value="">Toutes les zones</option>
            <option v-for="zone in zones" :key="zone" :value="zone">{{ zone }}</option>
          </select>
        </div>
        <div class="chart-container" ref="chartContainer"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardEpargneSection',
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
      selectedZone: '',
      selectedAgencies: [],
      selectedAgency: null, // Pour la sélection unique
      selectedPeriod: 'month',
      selectedDate: (() => {
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      })(),
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      kpiData: {
        encoursTotalM: 62084239881,
        encoursCompteCourant: 15587348585,
        encoursCompteEpargne: 5145254350,
        encoursDat: 0,
        compteEpargneProj: 103303288,
        encoursDepotGarant: 4796144967,
        tauxCouvertureReseau: 69
      },
      agenciesByZone: {
        'DAKAR VILLE': [
          'AGENCE CASTORS',
          'AGENCE LAMINE GUEYE',
          'AGENCE PARCELLES',
          'AGENCE PIKINE',
          'AGENCE PRINCIPALE POINT E'
        ],
        'DAKAR BANLIEUE': [
          'AGENCE KEUR MASSAR',
          'AGENCE LINGUERLA'
        ],
        'PROVINCE NORD': [
          'AGENCE KAOLACK',
          'AGENCE MBOUR'
        ],
        'PROVINCE CENTRE SUD': [],
        'GRAND COMPTE': [
          'AGENCE GRAND COMPTE'
        ]
      },
      zones: [
        'DAKAR BANLIEUE',
        'DAKAR VILLE',
        'GRAND COMPTE',
        'PROVINCE CENTRE SUD',
        'PROVINCE NORD'
      ],
      chartData: {
        labels: ['GRAND COMPTE', 'DAKAR VILLE', 'PROVINCE NORD', 'DAKAR BANLIEUE', 'PROVINCE CENTRE SUD'],
        encoursTotalM: [0, 28000000000, 5000000000, 13000000000, 12000000000],
        encoursCompteEpargne: [0, 3000000000, 500000000, 1000000000, 645254350],
        displayMode: 'zones'
      },
      allAgenciesData: [], // Stocker toutes les données d'agences pour le filtrage
      allZoneData: {} // Stocker toutes les données par zone
    }
  },
  mounted() {
    this.fetchDashboardData();
    this.$nextTick(() => {
      this.renderChart();
    });
  },
  computed: {
    filteredAgencies() {
      if (!this.selectedZone || this.selectedZone === '') {
        // Si aucune zone n'est sélectionnée, afficher toutes les agences
        return Object.values(this.agenciesByZone).flat();
      }
      // Filtrer les agences selon la zone sélectionnée
      return this.agenciesByZone[this.selectedZone] || [];
    },
    years() {
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let i = currentYear - 5; i <= currentYear + 2; i++) {
        years.push(i);
      }
      return years;
    }
  },
  watch: {
    selectedZoneProp(newVal) {
      if (newVal) {
        this.selectedZone = newVal;
        this.updateChart();
      }
    },
    selectedZone() {
      // Réinitialiser la sélection d'agence quand la zone change
      this.selectedAgency = null;
      this.selectedAgencies = [];
      this.updateChart();
    },
    selectedPeriod() {
      // Recharger les données quand la période change
      this.fetchDashboardData();
    },
    selectedDate() {
      // Recharger les données quand la date change (pour semaine)
      if (this.selectedPeriod === 'week') {
        this.fetchDashboardData();
      }
    },
    selectedMonth(newVal, oldVal) {
      // Recharger les données quand le mois change (pour mois)
      if (newVal !== oldVal && oldVal !== undefined && this.selectedPeriod === 'month') {
        this.fetchDashboardData();
      }
    },
    selectedYear(newVal, oldVal) {
      // Recharger les données quand l'année change
      if (newVal !== oldVal && oldVal !== undefined) {
        this.fetchDashboardData();
      }
    }
  },
  methods: {
    formatNumber(num) {
      if (!num && num !== 0) return '-';
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    handlePeriodChange() {
      this.fetchDashboardData();
    },
    handleDateChange() {
      if (this.selectedPeriod === 'week') {
        this.fetchDashboardData();
      }
    },
    handleMonthChange() {
      if (this.selectedPeriod === 'month') {
        this.fetchDashboardData();
      }
    },
    handleYearChange() {
      this.fetchDashboardData();
    },
    toggleAgency(agency) {
      // Sélection unique : si l'agence est déjà sélectionnée, la désélectionner
      // Sinon, remplacer la sélection précédente par la nouvelle
      if (this.selectedAgency === agency) {
        this.selectedAgency = null;
        this.selectedAgencies = [];
      } else {
        this.selectedAgency = agency;
        this.selectedAgencies = [agency];
      }
      this.updateChart();
    },
    async fetchDashboardData() {
      this.loading = true;
      try {
        // Récupérer les données d'encours (epargne-pep-simple contient toutes les données nécessaires)
        const params = {
          period: this.selectedPeriod,
          type: 'epargne-pep-simple'
        };
        
        // Ajouter les paramètres selon la période sélectionnée
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'week') {
          params.date = this.selectedDate;
        }
        
        console.log('📅 Chargement des données pour la période:', params);
        
        const response = await window.axios.get('/api/oracle/data/encours', { params });
        
        if (response.data && response.data.data && response.data.data.hierarchicalData) {
          const hierarchicalData = response.data.data.hierarchicalData;
          const agenciesByZone = {};
          const zoneData = {}; // Pour stocker les données par zone
          
          // Initialiser toutes les zones
          this.zones.forEach(zone => {
            agenciesByZone[zone] = [];
            zoneData[zone] = {
              encoursTotalM: 0,
              encoursCompteCourant: 0,
              encoursCompteEpargne: 0,
              encoursDat: 0,
              compteEpargneProj: 0,
              encoursDepotGarant: 0
            };
          });
          
          // Variables pour les totaux globaux
          let totalEncoursTotalM = 0;
          let totalEncoursCompteCourant = 0;
          let totalEncoursCompteEpargne = 0;
          let totalEncoursDat = 0;
          let totalCompteEpargneProj = 0;
          let totalEncoursDepotGarant = 0;
          
          // Fonction helper pour extraire une valeur numérique
          const getValue = (agency, field) => {
            const value = agency[field] || agency[field.toUpperCase()] || 0;
            return typeof value === 'number' ? value : parseFloat(value) || 0;
          };
          
          // Extraire les agences de TERRITOIRE
          if (hierarchicalData.TERRITOIRE) {
            Object.keys(hierarchicalData.TERRITOIRE).forEach(territoryKey => {
              const territory = hierarchicalData.TERRITOIRE[territoryKey];
              if (territory && territory.agencies) {
                territory.agencies.forEach(agency => {
                  const agencyName = agency.name || agency.BRANCH_NAME || '';
                  // Déterminer la zone selon le territoire
                  let zone = 'DAKAR VILLE'; // Par défaut
                  if (territoryKey.includes('dakar_ville')) {
                    zone = 'DAKAR VILLE';
                  } else if (territoryKey.includes('dakar_banlieue')) {
                    zone = 'DAKAR BANLIEUE';
                  } else if (territoryKey.includes('province_nord')) {
                    zone = 'PROVINCE NORD';
                  } else if (territoryKey.includes('province_centre_sud')) {
                    zone = 'PROVINCE CENTRE SUD';
                  } else if (territoryKey.includes('grand_compte')) {
                    zone = 'GRAND COMPTE';
                  }
                  
                  if (agencyName && !agenciesByZone[zone].includes(agencyName)) {
                    agenciesByZone[zone].push(agencyName);
                  }
                  
                  // Accumuler les données par zone
                  const encoursTotalM = getValue(agency, 'ENCOURS_TOTAL_M');
                  const encoursCompteCourant = getValue(agency, 'M_ENCOURS_COMPTE_COURANT');
                  const encoursCompteEpargne = getValue(agency, 'M_ENCOURS_COMPTE_EPARGNE');
                  const encoursDat = getValue(agency, 'M_ENCOURS_DAT');
                  const compteEpargneProj = getValue(agency, 'M_ENCOURS_COMPTE_EPARGNE_PROJET');
                  const encoursDepotGarant = getValue(agency, 'M_ENCOURS_DEPOT_GARANTIE');
                  
                  zoneData[zone].encoursTotalM += encoursTotalM;
                  zoneData[zone].encoursCompteCourant += encoursCompteCourant;
                  zoneData[zone].encoursCompteEpargne += encoursCompteEpargne;
                  zoneData[zone].encoursDat += encoursDat;
                  zoneData[zone].compteEpargneProj += compteEpargneProj;
                  zoneData[zone].encoursDepotGarant += encoursDepotGarant;
                  
                  // Totaux globaux
                  totalEncoursTotalM += encoursTotalM;
                  totalEncoursCompteCourant += encoursCompteCourant;
                  totalEncoursCompteEpargne += encoursCompteEpargne;
                  totalEncoursDat += encoursDat;
                  totalCompteEpargneProj += compteEpargneProj;
                  totalEncoursDepotGarant += encoursDepotGarant;
                });
              }
            });
          }
          
          this.agenciesByZone = agenciesByZone;
          
          // Stocker toutes les données pour le filtrage
          this.allZoneData = zoneData;
          this.allAgenciesData = [];
          
          // Stocker toutes les agences avec leurs données et zones
          if (hierarchicalData.TERRITOIRE) {
            Object.keys(hierarchicalData.TERRITOIRE).forEach(territoryKey => {
              const territory = hierarchicalData.TERRITOIRE[territoryKey];
              if (territory && territory.agencies) {
                territory.agencies.forEach(agency => {
                  const agencyName = agency.name || agency.BRANCH_NAME || '';
                  let zone = 'DAKAR VILLE';
                  if (territoryKey.includes('dakar_ville')) {
                    zone = 'DAKAR VILLE';
                  } else if (territoryKey.includes('dakar_banlieue')) {
                    zone = 'DAKAR BANLIEUE';
                  } else if (territoryKey.includes('province_nord')) {
                    zone = 'PROVINCE NORD';
                  } else if (territoryKey.includes('province_centre_sud')) {
                    zone = 'PROVINCE CENTRE SUD';
                  } else if (territoryKey.includes('grand_compte')) {
                    zone = 'GRAND COMPTE';
                  }
                  this.allAgenciesData.push({
                    name: agencyName,
                    zone: zone,
                    data: agency
                  });
                });
              }
            });
          }
          
          // Calculer le TAUX DE COUVERTURE RESEAU selon la formule :
          // (M_ENCOURS_COMPTE_COURANT + M_ENCOURS_COMPTE_EPARGNE + M_ENCOURS_COMPTE_EPARGNE_PROJET + M_ENCOURS_DAT + M_ENCOURS_DEPOT_GARANTIE) / ENCOURS_TOTAL_M
          const numerateur = totalEncoursCompteCourant + totalEncoursCompteEpargne + totalCompteEpargneProj + totalEncoursDat + totalEncoursDepotGarant;
          const tauxCouvertureReseau = totalEncoursTotalM > 0 
            ? Math.round((numerateur / totalEncoursTotalM) * 100 * 100) / 100 // Arrondir à 2 décimales
            : 0;
          
          // Mettre à jour les KPIs avec les données réelles
          this.kpiData = {
            encoursTotalM: totalEncoursTotalM,
            encoursCompteCourant: totalEncoursCompteCourant,
            encoursCompteEpargne: totalEncoursCompteEpargne,
            encoursDat: totalEncoursDat,
            compteEpargneProj: totalCompteEpargneProj,
            encoursDepotGarant: totalEncoursDepotGarant,
            tauxCouvertureReseau: tauxCouvertureReseau
          };
          
          // Mettre à jour les données du graphique (sans filtre initial)
          this.updateChart();
          
          // Re-rendre le graphique avec les nouvelles données
          this.$nextTick(() => {
            this.renderChart();
          });
        }
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        this.errorMessage = 'Erreur lors du chargement des données';
      } finally {
        this.loading = false;
      }
    },
    async renderChart() {
      if (!this.$refs.chartContainer) return;

      try {
        const Plotly = (await import('plotly.js-dist')).default;

        const trace1 = {
          x: this.chartData.labels,
          y: this.chartData.encoursTotalM.map(v => v / 1000000000), // Convertir en milliards
          name: 'Somme de ENCOURS_TOTAL_M',
          type: 'bar',
          marker: {
            color: '#3b82f6',
            line: {
              color: '#1e40af',
              width: 2
            },
            opacity: 0.95
          },
          text: this.chartData.encoursTotalM.map(v => {
            const value = v / 1000000000;
            if (value === 0) return '';
            return value >= 1 ? value.toFixed(1) + ' Md' : value.toFixed(2) + ' Md';
          }),
          textposition: 'outside',
          textfont: {
            color: '#f1f5f9',
            size: 10,
            family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }
        };

        const trace2 = {
          x: this.chartData.labels,
          y: this.chartData.encoursCompteEpargne.map(v => v / 1000000000), // Convertir en milliards
          name: 'ENCOURS_COMPTE_EPARGNE',
          type: 'bar',
          marker: {
            color: '#ef4444',
            line: {
              color: '#dc2626',
              width: 2
            },
            opacity: 0.95
          },
          text: this.chartData.encoursCompteEpargne.map(v => {
            const value = v / 1000000000;
            if (value === 0) return '';
            return value >= 1 ? value.toFixed(1) + ' Md' : value.toFixed(2) + ' Md';
          }),
          textposition: 'outside',
          textfont: {
            color: '#f1f5f9',
            size: 10,
            family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }
        };

        const data = [trace1, trace2];

        const layout = {
          barmode: 'group',
          bargap: 0.2,
          bargroupgap: 0.15,
          xaxis: {
            title: {
              text: '',
              font: { 
                size: 15, 
                color: '#f1f5f9',
                family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                weight: 500
              }
            },
            tickangle: this.chartData.displayMode === 'agencies' ? -45 : -25,
            tickfont: {
              size: 12,
              color: '#cbd5e1',
              family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              weight: 500
            },
            gridcolor: 'rgba(255, 255, 255, 0.08)',
            gridwidth: 1,
            showgrid: true,
            linecolor: 'rgba(255, 255, 255, 0.15)',
            linewidth: 1,
            tickmode: 'linear',
            automargin: true,
            ticklen: 5,
            tickwidth: 1
          },
          yaxis: {
            title: {
              text: 'Milliards',
              font: { 
                size: 15, 
                color: '#f1f5f9',
                family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                weight: 600
              },
              standoff: 15
            },
            tickfont: {
              size: 13,
              color: '#cbd5e1',
              family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              weight: 500
            },
            gridcolor: 'rgba(255, 255, 255, 0.12)',
            gridwidth: 1,
            showgrid: true,
            linecolor: 'rgba(255, 255, 255, 0.15)',
            linewidth: 1,
            zeroline: true,
            zerolinecolor: 'rgba(255, 255, 255, 0.25)',
            zerolinewidth: 1,
            tickformat: '.1f'
          },
          legend: {
            x: 1,
            y: 1,
            xanchor: 'right',
            yanchor: 'top',
            orientation: 'v',
            bgcolor: 'rgba(15, 23, 42, 0.85)',
            bordercolor: 'rgba(255, 255, 255, 0.2)',
            borderwidth: 1,
            borderpad: 10,
            font: {
              size: 11,
              color: '#f1f5f9',
              family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              weight: 500
            },
            itemclick: 'toggleothers',
            itemdoubleclick: 'toggle',
            tracegroupgap: 15,
            itemwidth: 18,
            itemgap: 10
          },
          margin: { l: 80, r: 40, t: 80, b: 160 },
          paper_bgcolor: 'rgba(0, 0, 0, 0)',
          plot_bgcolor: 'rgba(30, 41, 59, 0.4)',
          font: { 
            color: '#ffffff',
            family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size: 13
          },
          showlegend: true,
          hovermode: 'x unified',
          hoverlabel: {
            bgcolor: 'rgba(15, 23, 42, 0.95)',
            bordercolor: 'rgba(255, 255, 255, 0.2)',
            borderwidth: 1,
            font: {
              size: 13,
              color: '#f1f5f9',
              family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              weight: 500
            },
            namelength: 50
          }
        };

        const config = {
          responsive: true,
          displayModeBar: false,
          displaylogo: false
        };

        const plotDiv = this.$refs.chartContainer;
        Plotly.newPlot(plotDiv, data, layout, config);
        
        // Ajouter un gestionnaire d'événement pour permettre la sélection d'agences en cliquant sur les barres
        if (this.chartData.displayMode === 'agencies') {
          plotDiv.on('plotly_click', (eventData) => {
            if (eventData && eventData.points && eventData.points.length > 0) {
              const point = eventData.points[0];
              const agencyName = point.x;
              if (agencyName) {
                this.toggleAgency(agencyName);
              }
            }
          });
        }
      } catch (error) {
        console.error('Erreur lors du rendu du graphique:', error);
      }
    },
    updateChart() {
      // Filtrer les données selon les sélections
      const getValue = (agency, field) => {
        const value = agency[field] || agency[field.toUpperCase()] || 0;
        return typeof value === 'number' ? value : parseFloat(value) || 0;
      };
      
      // Initialiser les données filtrées par zone
      const filteredZoneData = {};
      this.zones.forEach(zone => {
        filteredZoneData[zone] = {
          encoursTotalM: 0,
          encoursCompteEpargne: 0
        };
      });
      
      // Filtrer les agences selon les sélections
      let filteredAgencies = this.allAgenciesData;
      
      // Filtrer par zone si une zone est sélectionnée
      if (this.selectedZone && this.selectedZone !== '') {
        filteredAgencies = filteredAgencies.filter(agency => agency.zone === this.selectedZone);
      }
      
      // Filtrer par agences sélectionnées si des agences sont sélectionnées
      // Cela fonctionne même si une zone est sélectionnée (filtre combiné)
      if (this.selectedAgencies && this.selectedAgencies.length > 0) {
        filteredAgencies = filteredAgencies.filter(agency => 
          this.selectedAgencies.includes(agency.name)
        );
      }
      
      // Variables pour les totaux globaux filtrés
      let totalEncoursTotalM = 0;
      let totalEncoursCompteCourant = 0;
      let totalEncoursCompteEpargne = 0;
      let totalEncoursDat = 0;
      let totalCompteEpargneProj = 0;
      let totalEncoursDepotGarant = 0;
      
      // Calculer les totaux par zone et globaux pour les agences filtrées
      filteredAgencies.forEach(agency => {
        const zone = agency.zone;
        const agencyData = agency.data;
        
        const encoursTotalM = getValue(agencyData, 'ENCOURS_TOTAL_M');
        const encoursCompteCourant = getValue(agencyData, 'M_ENCOURS_COMPTE_COURANT');
        const encoursCompteEpargne = getValue(agencyData, 'M_ENCOURS_COMPTE_EPARGNE');
        const encoursDat = getValue(agencyData, 'M_ENCOURS_DAT');
        const compteEpargneProj = getValue(agencyData, 'M_ENCOURS_COMPTE_EPARGNE_PROJET');
        const encoursDepotGarant = getValue(agencyData, 'M_ENCOURS_DEPOT_GARANTIE');
        
        filteredZoneData[zone].encoursTotalM += encoursTotalM;
        filteredZoneData[zone].encoursCompteEpargne += encoursCompteEpargne;
        
        // Totaux globaux filtrés
        totalEncoursTotalM += encoursTotalM;
        totalEncoursCompteCourant += encoursCompteCourant;
        totalEncoursCompteEpargne += encoursCompteEpargne;
        totalEncoursDat += encoursDat;
        totalCompteEpargneProj += compteEpargneProj;
        totalEncoursDepotGarant += encoursDepotGarant;
      });
      
      // Calculer le TAUX DE COUVERTURE RESEAU selon la formule :
      // (M_ENCOURS_COMPTE_COURANT + M_ENCOURS_COMPTE_EPARGNE + M_ENCOURS_COMPTE_EPARGNE_PROJET + M_ENCOURS_DAT + M_ENCOURS_DEPOT_GARANTIE) / ENCOURS_TOTAL_M
      const numerateur = totalEncoursCompteCourant + totalEncoursCompteEpargne + totalCompteEpargneProj + totalEncoursDat + totalEncoursDepotGarant;
      const tauxCouvertureReseau = totalEncoursTotalM > 0 
        ? Math.round((numerateur / totalEncoursTotalM) * 100 * 100) / 100 // Arrondir à 2 décimales
        : 0;
      
      // Mettre à jour les KPIs avec les données filtrées
      this.kpiData = {
        encoursTotalM: totalEncoursTotalM,
        encoursCompteCourant: totalEncoursCompteCourant,
        encoursCompteEpargne: totalEncoursCompteEpargne,
        encoursDat: totalEncoursDat,
        compteEpargneProj: totalCompteEpargneProj,
        encoursDepotGarant: totalEncoursDepotGarant,
        tauxCouvertureReseau: tauxCouvertureReseau
      };
      
      // Mettre à jour les données du graphique avec les données filtrées
      // Si une zone est sélectionnée OU des agences sont sélectionnées, afficher les agences
      if ((this.selectedZone && this.selectedZone !== '') || (this.selectedAgencies && this.selectedAgencies.length > 0)) {
        // Grouper les agences filtrées par nom et calculer les totaux
        const agenciesData = {};
        filteredAgencies.forEach(agency => {
          const agencyName = agency.name;
          if (!agenciesData[agencyName]) {
            agenciesData[agencyName] = {
              encoursTotalM: 0,
              encoursCompteEpargne: 0
            };
          }
          const agencyData = agency.data;
          agenciesData[agencyName].encoursTotalM += getValue(agencyData, 'ENCOURS_TOTAL_M');
          agenciesData[agencyName].encoursCompteEpargne += getValue(agencyData, 'M_ENCOURS_COMPTE_EPARGNE');
        });
        
        // Trier les agences par nom pour un affichage cohérent
        const sortedAgencies = Object.keys(agenciesData).sort();
        
        this.chartData = {
          labels: sortedAgencies,
          encoursTotalM: sortedAgencies.map(agency => agenciesData[agency].encoursTotalM),
          encoursCompteEpargne: sortedAgencies.map(agency => agenciesData[agency].encoursCompteEpargne),
          displayMode: 'agencies' // Mode agences
        };
      } else {
        // Si aucune zone ni agence n'est sélectionnée, afficher les zones
        this.chartData = {
          labels: this.zones,
          encoursTotalM: this.zones.map(zone => filteredZoneData[zone].encoursTotalM),
          encoursCompteEpargne: this.zones.map(zone => filteredZoneData[zone].encoursCompteEpargne),
          displayMode: 'zones' // Mode zones
        };
      }
      
      // Re-rendre le graphique avec les nouvelles données filtrées
      this.$nextTick(() => {
        this.renderChart();
      });
    }
  }
}
</script>

<style scoped>
.dashboard-epargne-section {
  padding: 30px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  min-height: 100vh;
}

.kpi-section {
  margin-bottom: 40px;
}

.period-selector-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.period-selector {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.period-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.period-select,
.month-select,
.year-select,
.date-select {
  padding: 10px 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: #1e293b;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 150px;
}

.period-select:hover,
.month-select:hover,
.year-select:hover,
.date-select:hover {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.period-select:focus,
.month-select:focus,
.year-select:focus,
.date-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading-blur {
  opacity: 0.6;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 20px;
}

.kpi-box {
  background: white;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-top: 4px solid transparent;
}

.kpi-box::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--kpi-color);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.kpi-box:hover::before {
  transform: scaleX(1);
}

.kpi-box:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.kpi-primary {
  --kpi-color: #1A4D3A;
  border-top-color: #1A4D3A;
}

.kpi-blue {
  --kpi-color: #3b82f6;
  border-top-color: #3b82f6;
}

.kpi-green {
  --kpi-color: #10b981;
  border-top-color: #10b981;
}

.kpi-orange {
  --kpi-color: #f59e0b;
  border-top-color: #f59e0b;
}

.kpi-purple {
  --kpi-color: #8b5cf6;
  border-top-color: #8b5cf6;
}

.kpi-teal {
  --kpi-color: #14b8a6;
  border-top-color: #14b8a6;
}

.kpi-red {
  --kpi-color: #ef4444;
  border-top-color: #ef4444;
}

.kpi-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.9;
}

.kpi-label {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 10px;
  font-weight: 600;
  line-height: 1.5;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

.kpi-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.3;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  letter-spacing: -0.3px;
}

.main-dashboard-section {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 25px;
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.filter-panel {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-radius: 12px;
  padding: 20px;
  max-height: 650px;
  overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.filter-panel::-webkit-scrollbar {
  width: 8px;
}

.filter-panel::-webkit-scrollbar-track {
  background: #1e293b;
  border-radius: 4px;
}

.filter-panel::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.filter-panel::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.filter-icon {
  font-size: 18px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.filter-title {
  font-size: 15px;
  font-weight: 600;
  color: white;
  margin: 0;
  letter-spacing: 0.3px;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  text-transform: uppercase;
}

.filter-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item {
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 12px;
  font-weight: 500;
  position: relative;
  overflow: hidden;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  letter-spacing: 0.1px;
  line-height: 1.5;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  min-height: 44px;
  display: flex;
  align-items: center;
  hyphens: auto;
}

.filter-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #1A4D3A;
  transform: scaleY(0);
  transition: transform 0.3s ease;
}

.filter-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transform: translateX(5px);
  border-color: rgba(255, 255, 255, 0.2);
}

.filter-item:hover::before {
  transform: scaleY(1);
}

.filter-item.active {
  background: linear-gradient(135deg, #1A4D3A 0%, #2d6a4f 100%);
  color: white;
  font-weight: 600;
  border-color: #1A4D3A;
  box-shadow: 0 4px 12px rgba(26, 77, 58, 0.3);
}

.filter-item.active::before {
  transform: scaleY(1);
  background: white;
}

.filter-empty {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  font-style: italic;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

.chart-panel {
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-radius: 12px;
  padding: 25px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chart-panel {
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-radius: 12px;
  padding: 25px;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e2e8f0;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  letter-spacing: 0.2px;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

.zone-select {
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  background: white;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 180px;
  font-family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  letter-spacing: 0.1px;
}

.zone-select:hover {
  border-color: #1A4D3A;
  box-shadow: 0 2px 8px rgba(26, 77, 58, 0.1);
}

.zone-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.chart-container {
  width: 100%;
  height: 500px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  position: relative;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.1) 0%, transparent 50%);
  pointer-events: none;
  border-radius: 12px;
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.kpi-box {
  animation: fadeInUp 0.5s ease-out;
  animation-fill-mode: both;
}

.kpi-box:nth-child(1) { animation-delay: 0.1s; }
.kpi-box:nth-child(2) { animation-delay: 0.2s; }
.kpi-box:nth-child(3) { animation-delay: 0.3s; }
.kpi-box:nth-child(4) { animation-delay: 0.4s; }
.kpi-box:nth-child(5) { animation-delay: 0.5s; }
.kpi-box:nth-child(6) { animation-delay: 0.6s; }
.kpi-box:nth-child(7) { animation-delay: 0.7s; }

@media (max-width: 1400px) {
  .main-dashboard-section {
    grid-template-columns: 240px 1fr;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .main-dashboard-section {
    grid-template-columns: 1fr;
  }
  
  .filter-panel {
    max-height: 350px;
  }
  
  .chart-container {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .dashboard-epargne-section {
    padding: 15px;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }
  
  .dashboard-title {
    font-size: 20px;
  }
  
  .logo {
    height: 60px;
  }
}
</style>
