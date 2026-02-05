<template>
  <div class="agency-performance-section">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-text">Performance des Agences</span>
        <span class="chart-icon">📊</span>
      </h2>
    </div>
    
    <div v-if="loading" class="loading-message">
      <p>🔄 Chargement des données depuis Oracle...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>⚠️ {{ errorMessage }}</p>
    </div>

    <div class="performance-container">
      <!-- Section AGENCE (uniquement pour collection) -->
      <div v-if="dataType === 'collection'" class="performance-category" data-category="agence">
        <div class="category-label">
          <span class="label-text">AGENCE</span>
        </div>
        <div class="top-flop-container">
          <!-- Top 5 Agence -->
          <div class="agency-list top-list">
            <div class="list-header top-header">
              <div class="header-content">
                <span class="thumbs-icon">👍</span>
                <span class="list-title">Top 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in top5Agence" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator top-indicator">▲</span>
              </li>
              <li v-if="top5Agence.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>

          <!-- Flop 5 Agence -->
          <div class="agency-list flop-list">
            <div class="list-header flop-header">
              <div class="header-content">
                <span class="thumbs-icon">👎</span>
                <span class="list-title">Flop 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in flop5Agence" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator flop-indicator">▼</span>
              </li>
              <li v-if="flop5Agence.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>
        </div>
      </div>

      <!-- Section NOMBRE (pour les autres types de données) -->
      <div v-else class="performance-category" data-category="nombre">
        <div class="category-label">
          <span class="label-text">NOMBRE</span>
        </div>
        <div class="top-flop-container">
          <!-- Top 5 Agence -->
          <div class="agency-list top-list">
            <div class="list-header top-header">
              <div class="header-content">
                <span class="thumbs-icon">👍</span>
                <span class="list-title">Top 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in top5Nombre" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator top-indicator">▲</span>
              </li>
              <li v-if="top5Nombre.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>

          <!-- Flop 5 Agence -->
          <div class="agency-list flop-list">
            <div class="list-header flop-header">
              <div class="header-content">
                <span class="thumbs-icon">👎</span>
                <span class="list-title">Flop 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in flop5Nombre" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator flop-indicator">▼</span>
              </li>
              <li v-if="flop5Nombre.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>
        </div>
      </div>

      <!-- Ligne de séparation rouge -->
      <div class="separator-line">
        <div class="separator-glow"></div>
      </div>

      <!-- Section CAF (uniquement pour collection) -->
      <div v-if="dataType === 'collection'" class="performance-category" data-category="caf">
        <div class="category-label">
          <span class="label-text">CAF</span>
        </div>
        <div class="top-flop-container">
          <!-- Top 5 CAF -->
          <div class="agency-list top-list">
            <div class="list-header top-header">
              <div class="header-content">
                <span class="thumbs-icon">👍</span>
                <span class="list-title">Top 5 CAF</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(caf, index) in top5CAF" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ caf }}</span>
                <span class="rank-indicator top-indicator">▲</span>
              </li>
              <li v-if="top5CAF.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>

          <!-- Flop 5 CAF -->
          <div class="agency-list flop-list">
            <div class="list-header flop-header">
              <div class="header-content">
                <span class="thumbs-icon">👎</span>
                <span class="list-title">Flop 5 CAF</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(caf, index) in flop5CAF" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ caf }}</span>
                <span class="rank-indicator flop-indicator">▼</span>
              </li>
              <li v-if="flop5CAF.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>
        </div>
      </div>

      <!-- Section VOLUME (pour les autres types de données) -->
      <div v-else class="performance-category" data-category="volume">
        <div class="category-label">
          <span class="label-text">VOLUME</span>
        </div>
        <div class="top-flop-container">
          <!-- Top 5 Agence -->
          <div class="agency-list top-list">
            <div class="list-header top-header">
              <div class="header-content">
                <span class="thumbs-icon">👍</span>
                <span class="list-title">Top 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in top5Volume" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator top-indicator">▲</span>
              </li>
              <li v-if="top5Volume.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>

          <!-- Flop 5 Agence -->
          <div class="agency-list flop-list">
            <div class="list-header flop-header">
              <div class="header-content">
                <span class="thumbs-icon">👎</span>
                <span class="list-title">Flop 5 Agence</span>
              </div>
              <div class="header-decoration"></div>
            </div>
            <ol class="agency-items">
              <li 
                v-for="(agency, index) in flop5Volume" 
                :key="index" 
                class="agency-item"
                :style="{ animationDelay: `${index * 0.1}s` }"
              >
                <span class="agency-number-badge">{{ index + 1 }}</span>
                <span class="agency-name">{{ agency }}</span>
                <span class="rank-indicator flop-indicator">▼</span>
              </li>
              <li v-if="flop5Volume.length === 0" class="agency-item no-data">
                <span class="agency-name">Aucune donnée disponible</span>
              </li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { extractAgencies, getPerformanceMetrics } from '../utils/performanceMetrics.js';

export default {
  name: 'AgencyPerformanceSection',
  props: {
    dataType: {
      type: String,
      default: 'default',
      validator: (value) => {
        return ['default', 'client', 'collection', 'credit', 'prepaid-cards', 'money-transfers', 'eps', 'divers'].includes(value);
      }
    },
    tableData: {
      type: Object,
      default: null
    }
  },
  inject: {
    collectionTab: {
      from: 'collectionTab',
      default: () => () => 'collecte'
    }
  },
  computed: {
    currentCollectionTab() {
      // Si on est dans le contexte de collection, utiliser l'onglet injecté
      if (this.dataType === 'collection') {
        return this.collectionTab();
      }
      return 'collecte';
    }
  },
  data() {
    return {
      loading: false,
      errorMessage: null,
      allAgencies: [], // Toutes les agences avec leurs données
      allCAFs: [], // Tous les CAF avec leurs données agrégées
      // Données calculées pour la section AGENCE (collection)
      top5Agence: [],
      flop5Agence: [],
      // Données calculées pour la section CAF (collection)
      top5CAF: [],
      flop5CAF: [],
      // Données calculées pour la section NOMBRE (autres types)
      top5Nombre: [],
      flop5Nombre: [],
      // Données calculées pour la section VOLUME (autres types)
      top5Volume: [],
      flop5Volume: [],
      // Cache pour éviter de retraiter les mêmes données
      lastProcessedDataHash: null,
      processingTimeout: null
    }
  },
  mounted() {
    // Traiter les données (depuis props ou API)
    this.processPerformanceData();
  },
  watch: {
    dataType() {
      // Recharger les données quand le type change
      this.lastProcessedDataHash = null; // Réinitialiser le cache
      this.processPerformanceData();
    },
    currentCollectionTab() {
      // Recharger les données quand l'onglet collection change
      if (this.dataType === 'collection') {
        this.lastProcessedDataHash = null; // Réinitialiser le cache
        this.processPerformanceData();
      }
    },
    tableData: {
      handler(newVal) {
        // Vérifier si les données ont vraiment changé
        if (!newVal || !newVal.hierarchicalData) {
          return;
        }
        
        // Créer un hash simple pour éviter de retraiter les mêmes données
        const dataHash = this.getDataHash(newVal);
        if (dataHash === this.lastProcessedDataHash) {
          return; // Les données n'ont pas changé, ne pas retraiter
        }
        
        // Débouncer le traitement pour éviter les appels multiples
        if (this.processingTimeout) {
          clearTimeout(this.processingTimeout);
        }
        
        this.processingTimeout = setTimeout(() => {
          this.processPerformanceData();
        }, 100);
      },
      immediate: true
    }
  },
  methods: {
    getDataHash(data) {
      // Créer un hash simple basé sur la structure des données
      if (!data || !data.hierarchicalData) {
        return null;
      }
      
      // Utiliser le nombre d'agences et de CAF comme hash simple
      let agencyCount = 0;
      let cafCount = 0;
      
      if (data.hierarchicalData.TERRITOIRE) {
        Object.values(data.hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory.agencies) {
            agencyCount += territory.agencies.length;
          }
        });
      }
      
      if (data.chargeAffaireDetails) {
        cafCount = Object.keys(data.chargeAffaireDetails).length;
      }
      
      return `${this.dataType}-${this.currentCollectionTab}-${agencyCount}-${cafCount}`;
    },
    
    processPerformanceData() {
      // Utiliser les données des tableaux si disponibles, sinon faire un appel API
      if (this.tableData && this.tableData.hierarchicalData) {
        // Vérifier le hash pour éviter de retraiter
        const dataHash = this.getDataHash(this.tableData);
        if (dataHash === this.lastProcessedDataHash) {
          return; // Déjà traité
        }
        
        this.lastProcessedDataHash = dataHash;
        this.loading = false;
        this.errorMessage = null;
        
        // Utiliser nextTick pour différer le traitement lourd
        this.$nextTick(() => {
          try {
            // Préparer les données au format attendu
            const data = {
              data: {
                hierarchicalData: this.tableData.hierarchicalData,
                chargeAffaireDetails: this.tableData.chargeAffaireDetails || {}
              }
            };
            
            // Extraire les agences depuis les données
            const agencies = extractAgencies(data, this.dataType, this.currentCollectionTab, (agency) => this.getAgencyName(agency));
            
            // Extraire et agréger les CAF si c'est pour la collection
            if (this.dataType === 'collection') {
              const cafs = this.extractCAFs(data);
              this.classifyCAFs(cafs);
            } else {
              this.top5CAF = [];
              this.flop5CAF = [];
            }
            
            // Classer les agences
            this.classifyAgencies(agencies);
          } catch (error) {
            console.error('Erreur lors du traitement des données de performance:', error);
            this.errorMessage = 'Erreur lors du traitement des données.';
            this.setDefaultData();
          }
        });
      } else {
        // Si pas de données en props, faire un appel API (fallback)
        this.fetchPerformanceData();
      }
    },
    
    async fetchPerformanceData() {
      this.loading = true;
      this.errorMessage = null;
      
      try {
        const now = new Date();
        
        // Pour la collection, utiliser l'endpoint de collection pour obtenir les détails CAF
        if (this.dataType === 'collection') {
          const collectionEndpoint = '/api/oracle/data/collection';
          const collectionParams = {
            period: 'month',
            month: now.getMonth() + 1,
            year: now.getFullYear()
          };
          
          const collectionResponse = await window.axios.get(collectionEndpoint, {
            params: collectionParams,
            timeout: 120000,
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            }
          });
          
          // Extraire les agences depuis la réponse
          const agencies = extractAgencies(collectionResponse.data, this.dataType, this.currentCollectionTab, (agency) => this.getAgencyName(agency));
          
          // Extraire et agréger les CAF
          const cafs = this.extractCAFs(collectionResponse.data);
          this.classifyCAFs(cafs);
          
          // Classer les agences
          this.classifyAgencies(agencies);
        } else {
          // Pour les autres types, utiliser l'endpoint de performance
          const endpoint = '/api/oracle/data/agency-performance';
          const params = {
            data_type: this.dataType,
            period: 'month',
            month: now.getMonth() + 1,
            year: now.getFullYear()
          };
          
          const response = await window.axios.get(endpoint, { 
            params,
            timeout: 120000,
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            }
          });
          
          // Extraire les agences depuis la réponse
          const agencies = extractAgencies(response.data, this.dataType, this.currentCollectionTab, (agency) => this.getAgencyName(agency));
          
          // Pas de CAF pour les autres types
          this.top5CAF = [];
          this.flop5CAF = [];
          
          // Classer les agences
          this.classifyAgencies(agencies);
        }
        
      } catch (error) {
        console.error('Erreur lors du chargement des données de performance:', error);
        this.errorMessage = 'Erreur lors du chargement des données. Utilisation des données par défaut.';
        // En cas d'erreur, utiliser les données par défaut
        this.setDefaultData();
      } finally {
        this.loading = false;
      }
    },
    
    classifyAgencies(agencies) {
      if (!agencies || agencies.length === 0) {
        this.setDefaultData();
        return;
      }

      if (this.dataType === 'collection') {
        // Pour la collection : trier par collecteM
        const sortedByCollecteM = [...agencies].sort((a, b) => {
          const aValue = a.collecteM || a.COLLECTE_M || 0;
          const bValue = b.collecteM || b.COLLECTE_M || 0;
          return bValue - aValue;
        });
        this.top5Agence = sortedByCollecteM.slice(0, 5).map(a => a.name);
        this.flop5Agence = sortedByCollecteM.slice(-5).reverse().map(a => a.name);
      } else {
        // Pour les autres types : trier par nombre et volume
        const sortedByNombre = [...agencies].sort((a, b) => b.nombre - a.nombre);
        this.top5Nombre = sortedByNombre.slice(0, 5).map(a => a.name);
        this.flop5Nombre = sortedByNombre.slice(-5).reverse().map(a => a.name);

        const sortedByVolume = [...agencies].sort((a, b) => b.volume - a.volume);
        this.top5Volume = sortedByVolume.slice(0, 5).map(a => a.name);
        this.flop5Volume = sortedByVolume.slice(-5).reverse().map(a => a.name);
      }
    },
    
    extractCAFs(data) {
      const cafMap = new Map();
      
      // Accéder aux chargeAffaireDetails depuis la réponse
      let chargeAffaireDetails = null;
      if (data && data.data && data.data.chargeAffaireDetails) {
        chargeAffaireDetails = data.data.chargeAffaireDetails;
      } else if (data && data.chargeAffaireDetails) {
        chargeAffaireDetails = data.chargeAffaireDetails;
      }
      
      // Extraire les données hiérarchiques pour obtenir les branch codes
      let hierarchicalData = null;
      if (data && data.data && data.data.hierarchicalData) {
        hierarchicalData = data.data.hierarchicalData;
      } else if (data && data.hierarchicalData) {
        hierarchicalData = data.hierarchicalData;
      } else if (data && data.data) {
        hierarchicalData = data.data;
      }
      
      if (!chargeAffaireDetails || !hierarchicalData) {
        return [];
      }
      
      // Parcourir tous les détails de chargé d'affaire
      Object.keys(chargeAffaireDetails).forEach(branchCode => {
        const chargeDetails = chargeAffaireDetails[branchCode];
        if (chargeDetails && Array.isArray(chargeDetails)) {
          chargeDetails.forEach(charge => {
            const cafName = charge.chargeAffaire || charge.CHARGE_AFFAIRE || '-';
            if (cafName && cafName !== '-') {
              const collecteM = parseFloat(charge.collecteM || charge.COLLECTE_M || 0);
              
              if (cafMap.has(cafName)) {
                cafMap.set(cafName, cafMap.get(cafName) + collecteM);
              } else {
                cafMap.set(cafName, collecteM);
              }
            }
          });
        }
      });
      
      // Convertir la Map en tableau d'objets
      return Array.from(cafMap.entries()).map(([name, collecteM]) => ({
        name,
        collecteM
      }));
    },
    
    classifyCAFs(cafs) {
      if (!cafs || cafs.length === 0) {
        this.top5CAF = [];
        this.flop5CAF = [];
        return;
      }

      // Trier par collecteM (croissant pour flop, décroissant pour top)
      const sortedByCollecteM = [...cafs].sort((a, b) => b.collecteM - a.collecteM);
      this.top5CAF = sortedByCollecteM.slice(0, 5).map(c => c.name);
      this.flop5CAF = sortedByCollecteM.slice(-5).reverse().map(c => c.name);
    },
    
    getAgencyName(agency) {
      // Essayer différents champs pour obtenir le nom de l'agence
      return agency.name || 
             agency.AGENCE || 
             agency.agency || 
             agency.agencyName ||
             (agency.BRANCH_CODE ? `Agence ${agency.BRANCH_CODE}` : null) ||
             'Agence inconnue';
    },
    
    setDefaultData() {
      // Données par défaut si aucune donnée n'est disponible
      if (this.dataType === 'collection') {
        this.top5Agence = [
          'SAINT-LOUIS',
          'LOUGA',
          'DIOURBEL',
          'LINGUERE LA',
          'RUFISQUE'
        ];
        this.flop5Agence = [
          'GRAND COMPTE',
          'OUROSSOGUI',
          'THIES',
          'SCAT URBAM',
          'CASTOR'
        ];
        this.top5CAF = [];
        this.flop5CAF = [];
      } else {
        this.top5Nombre = [
          'SAINT-LOUIS',
          'LOUGA',
          'DIOURBEL',
          'LINGUERE LA',
          'RUFISQUE'
        ];
        this.flop5Nombre = [
          'GRAND COMPTE',
          'OUROSSOGUI',
          'THIES',
          'SCAT URBAM',
          'CASTOR'
        ];
        this.top5Volume = [
          'LOUGA',
          'POINT E',
          'NIARRY TALLY',
          'RUFISQUE',
          'CASTOR'
        ];
        this.flop5Volume = [
          'GRAND COMPTE',
          'THIES',
          'KAOLACK',
          'LAMINE GUEYE',
          'MBOUR'
        ];
      }
    }
  }
}
</script>

<style scoped>
.agency-performance-section {
  width: 100%;
  padding: 50px;
  background: transparent;
  min-height: calc(100vh - 100px);
  position: relative;
  overflow: hidden;
}


.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
}

.section-title {
  font-size: 42px;
  font-weight: 800;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 20px;
  letter-spacing: 1px;
  position: relative;
}

.title-text {
  color: #333;
  position: relative;
}


.chart-icon {
  font-size: 48px;
  color: #DC2626;
  filter: 
    drop-shadow(0 0 10px rgba(220, 38, 38, 0.8))
    drop-shadow(0 0 20px rgba(220, 38, 38, 0.4));
  animation: pulse 2s ease-in-out infinite, rotate 10s linear infinite;
  display: inline-block;
  transform-origin: center;
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.performance-container {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  z-index: 1;
}

.performance-category {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  padding: 40px 0;
  gap: 30px;
  animation: fadeInUp 0.6s ease-out;
}

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

.category-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 28px;
  font-weight: 900;
  color: #333;
  padding: 25px 15px;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 20px;
  letter-spacing: 6px;
  border: 2px solid #ddd;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
}


.category-label:hover {
  background: transparent;
  transform: scale(1.08) translateX(-5px);
  border-color: #999;
}

.top-flop-container {
  display: flex;
  gap: 25px;
  flex: 1;
}

.agency-list {
  flex: 1;
  background: transparent;
  border-radius: 24px;
  padding: 30px;
  box-shadow: none;
  min-height: 260px;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  border: 2px solid #ddd;
}


.agency-list:hover {
  transform: translateY(-8px) scale(1.02);
}

.top-list {
  border-color: #10B981;
}

.top-list:hover {
  border-color: #059669;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.flop-list {
  border-color: #DC2626;
}

.flop-list:hover {
  border-color: #B91C1C;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.2);
}

.list-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  position: relative;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.top-header .header-content {
  color: #10B981;
}

.flop-header .header-content {
  color: #DC2626;
}

.header-decoration {
  height: 3px;
  border-radius: 2px;
  background: transparent;
  opacity: 0.6;
}

.top-header .header-decoration {
  background: #10B981;
}

.flop-header .header-decoration {
  background: #DC2626;
}

.thumbs-icon {
  font-size: 28px;
  animation: bounce 2s ease-in-out infinite;
  filter: 
    drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))
    drop-shadow(0 0 10px currentColor);
  transition: all 0.3s ease;
}

.top-header .thumbs-icon {
  filter: 
    drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))
    drop-shadow(0 0 15px rgba(16, 185, 129, 0.6));
}

.flop-header .thumbs-icon {
  filter: 
    drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))
    drop-shadow(0 0 15px rgba(220, 38, 38, 0.6));
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.list-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 1px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.top-list .list-title {
  font-size: 28px;
  font-weight: 900;
}

.flop-list .list-title {
  font-size: 28px;
  font-weight: 900;
}

.agency-items {
  list-style: none;
  padding: 0;
  margin: 0;
}

.agency-item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px 16px;
  margin-bottom: 10px;
  border-radius: 14px;
  background: transparent;
  border-left: 4px solid transparent;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  animation: slideIn 0.6s ease-out backwards;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.agency-item:hover {
  transform: translateX(8px) scale(1.02);
  background: transparent;
  border-left-width: 5px;
}

.top-list .agency-item:hover {
  border-left-color: #10B981;
  box-shadow: 
    0 4px 15px rgba(16, 185, 129, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 0 20px rgba(16, 185, 129, 0.1);
}

.flop-list .agency-item:hover {
  border-left-color: #DC2626;
  box-shadow: 
    0 4px 15px rgba(220, 38, 38, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    0 0 20px rgba(220, 38, 38, 0.1);
}

.agency-item:last-child {
  margin-bottom: 0;
}

.agency-item.no-data {
  opacity: 0.6;
  font-style: italic;
  justify-content: center;
}

.agency-item.no-data .agency-name {
  color: #9ca3af;
}

.agency-number-badge {
  font-weight: 900;
  min-width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 18px;
  border-radius: 14px;
  position: relative;
  z-index: 1;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.top-list .agency-number-badge {
  background: #10B981;
  color: white;
}

.flop-list .agency-number-badge {
  background: #DC2626;
  color: white;
}

.agency-item:hover .agency-number-badge {
  transform: scale(1.15) rotate(8deg);
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
}

.top-list .agency-item:hover .agency-number-badge {
  box-shadow: 
    0 6px 20px rgba(16, 185, 129, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3),
    0 0 25px rgba(16, 185, 129, 0.4);
}

.flop-list .agency-item:hover .agency-number-badge {
  box-shadow: 
    0 6px 20px rgba(220, 38, 38, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3),
    0 0 25px rgba(220, 38, 38, 0.4);
}

.agency-name {
  color: #1f2937;
  font-size: 17px;
  font-weight: 700;
  flex: 1;
  position: relative;
  z-index: 1;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.agency-item:hover .agency-name {
  color: #111827;
  transform: translateX(3px);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.rank-indicator {
  font-size: 22px;
  position: relative;
  z-index: 1;
  opacity: 0.8;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  font-weight: 900;
}

.agency-item:hover .rank-indicator {
  opacity: 1;
  transform: scale(1.3) translateY(-2px);
}

.top-indicator {
  color: #10B981;
  filter: 
    drop-shadow(0 0 8px rgba(16, 185, 129, 0.8))
    drop-shadow(0 2px 4px rgba(16, 185, 129, 0.4));
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
}

.flop-indicator {
  color: #DC2626;
  filter: 
    drop-shadow(0 0 8px rgba(220, 38, 38, 0.8))
    drop-shadow(0 2px 4px rgba(220, 38, 38, 0.4));
  text-shadow: 0 0 10px rgba(220, 38, 38, 0.6);
}

.separator-line {
  width: 100%;
  height: 6px;
  background: #DC2626;
  margin: 50px 0;
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.separator-glow {
  display: none;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.loading-message {
  background: #E3F2FD;
  border: 1px solid #2196F3;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  text-align: center;
  color: #1976D2;
  font-weight: 500;
  font-size: 16px;
}

.error-message {
  background: #FFEBEE;
  border: 1px solid #F44336;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  text-align: center;
  color: #C62828;
  font-weight: 500;
  font-size: 16px;
}

@media (max-width: 768px) {
  .agency-performance-section {
    padding: 20px;
  }

  .section-title {
    font-size: 24px;
  }

  .chart-icon {
    font-size: 28px;
  }

  .performance-category {
    flex-direction: column;
    padding: 30px 0;
  }

  .category-label {
    writing-mode: horizontal-tb;
    text-orientation: mixed;
    min-width: auto;
    width: 100%;
    margin-right: 0;
    margin-bottom: 20px;
    padding: 15px;
  }

  .top-flop-container {
    flex-direction: column;
    gap: 20px;
  }

  .agency-list {
    min-height: auto;
  }
}
</style>
