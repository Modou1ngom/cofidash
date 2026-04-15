<template>
  <aside class="sidebar">
    <nav class="sidebar-nav">
      <div class="nav-section">
        <div class="nav-section-header" @click.stop="toggleClient" :class="{ active: activeSection === 'client' || activeSection === 'performance-client' }">
          <span class="nav-title">
            <span class="nav-icon">👤</span>
            <span class="nav-label">RELATION</span>
          </span>
          <span class="toggle-icon">{{ clientExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="clientExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('client')" class="nav-link indent" :class="{ active: activeSection === 'client' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-client')" class="nav-link indent" :class="{ active: activeSection === 'performance-client' }">
            📊 Performance
          </a>
        </div>
        <div class="nav-section-header" @click.stop="toggleDepot" :class="{ active: activeSection === 'collection' || activeSection === 'performance-collection' || activeSection === 'domiciliation-flux' || activeSection === 'encours-dat' || activeSection === 'encours-epargne' || activeSection === 'depot-garantie' }">
          <span class="nav-title">
            <span class="nav-icon">💰</span>
            <span class="nav-label">DEPOT</span>
          </span>
          <span class="toggle-icon">{{ depotExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="depotExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('collection')" class="nav-link indent" :class="{ active: activeSection === 'collection' }">
            Domiciliation de flux
          </a>
          <a href="#" @click.stop.prevent="selectSection('encours-dat')" class="nav-link indent" :class="{ active: activeSection === 'encours-dat' }">
            Encours DAT
          </a>
          <a href="#" @click.stop.prevent="selectSection('encours-epargne')" class="nav-link indent" :class="{ active: activeSection === 'encours-epargne' }">
            Encours Épargne
          </a>
          <a href="#" @click.stop.prevent="selectSection('depot-garantie')" class="nav-link indent" :class="{ active: activeSection === 'depot-garantie' }">
            Dépôt de Garantie
          </a>
        </div>
       <!-- <div v-if="activeSection === 'client'" class="nav-section-items">
          <div class="nav-section">
            <div class="nav-section-header indent" @click.stop="toggleZone">
              <span>Zone</span>
              <span class="toggle-icon">{{ zoneExpanded ? '▼' : '▶' }}</span>
            </div>
            <div v-if="zoneExpanded" class="nav-section-items">
              <a href="#" @click.stop.prevent="selectZone('zone1')" class="nav-link double-indent" :class="{ active: selectedZone === 'zone1' }">Zone 1</a>
              <a href="#" @click.stop.prevent="selectZone('zone2')" class="nav-link double-indent" :class="{ active: selectedZone === 'zone2' }">Zone 2</a>
            </div>
          </div>
        </div>-->
        <div class="nav-section-header" @click.stop="toggleCredit" :class="{ active: activeSection === 'production' || activeSection === 'renouvellement' || activeSection === 'restructuration' || activeSection === 'commission-credit' || activeSection === 'recouvrement' || activeSection === 'portefeuille-risque' || activeSection === 'performance-credit' }">
          <span class="nav-title">
            <span class="nav-icon">💳</span>
            <span class="nav-label">CREDIT</span>
          </span>
          <span class="toggle-icon">{{ creditExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="creditExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('production')" class="nav-link indent" :class="{ active: activeSection === 'production' }">
            Production
          </a>
          <div class="nav-section-header indent" @click.stop="togglePortefeuilleRisque">
            <span>Portefeuille à risque</span>
            <span class="toggle-icon">{{ portefeuilleRisqueExpanded ? '▼' : '▶' }}</span>
          </div>
          <div v-if="portefeuilleRisqueExpanded" class="nav-section-items">
           <!--<a href="#" @click.stop.prevent="handlePortefeuilleRisqueSection('simple')" class="nav-link double-indent" :class="{ active: activeSection === 'portefeuille-risque' && activeSubSection === 'simple' }">
              PAR SIMPLE
            </a>-->
            <a href="#" @click.stop.prevent="handlePortefeuilleRisqueSection('global')" class="nav-link double-indent" :class="{ active: activeSection === 'portefeuille-risque' && activeSubSection === 'global' }">
              PAR GLOBAL
            </a>
          </div>
          <a href="#" @click.stop.prevent="selectSection('renouvellement')" class="nav-link indent" :class="{ active: activeSection === 'renouvellement' }">
            Renouvellement
          </a>
          <a href="#" @click.stop.prevent="selectSection('restructuration')" class="nav-link indent" :class="{ active: activeSection === 'restructuration' }">
            Restructuration
          </a>
          <a href="#" @click.stop.prevent="selectSection('commission-credit')" class="nav-link indent" :class="{ active: activeSection === 'commission-credit' }">
            Commission de crédit
          </a>
         
         
          <a href="#" @click.stop.prevent="selectSection('performance-credit')" class="nav-link indent" :class="{ active: activeSection === 'performance-credit' }">
            📊 Performance
          </a>
        </div>
       
       <!-- <div class="nav-section-header" @click.stop="selectSection('performance')" :class="{ active: activeSection === 'performance' }">
          <span class="nav-title">
            <span class="nav-icon">📊</span>
            <span class="nav-label">Performance</span>
          </span>
        </div>-->
        <div class="nav-section-header" @click.stop="togglePrepaidCards" :class="{ active: activeSection === 'prepaid-cards' || activeSection === 'performance-prepaid-cards' }">
          <span class="nav-title">
            <span class="nav-icon">💳</span>
            <span class="nav-label">DESC MONETIQUE</span>
          </span>
          <span class="toggle-icon">{{ prepaidCardsExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="prepaidCardsExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="handlePrepaidCardSection('sales')" class="nav-link indent" :class="{ active: activeSection === 'prepaid-cards' && activeSubSection === 'sales' }">Vente</a>
          <a href="#" @click.stop.prevent="handlePrepaidCardSection('recharge')" class="nav-link indent" :class="{ active: activeSection === 'prepaid-cards' && activeSubSection === 'recharge' }">Rechargement</a>
          <a href="#" @click.stop.prevent="selectSection('performance-prepaid-cards')" class="nav-link indent" :class="{ active: activeSection === 'performance-prepaid-cards' }">
            📊 Performance
          </a>
        </div>
        <div class="nav-section-header" @click.stop="toggleMoneyTransfers" :class="{ active: activeSection === 'money-transfers' || activeSection === 'performance-money-transfers' }">
          <span class="nav-title">
            <span class="nav-icon">💸</span>
            <span class="nav-label">DESC TRANSFERTS</span>
          </span>
          <span class="toggle-icon">{{ moneyTransfersExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="moneyTransfersExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('money-transfers')" class="nav-link indent" :class="{ active: activeSection === 'money-transfers' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-money-transfers')" class="nav-link indent" :class="{ active: activeSection === 'performance-money-transfers' }">
            📊 Performance
          </a>
        </div>
        <div class="nav-section-header" @click.stop="toggleEps" :class="{ active: activeSection === 'eps' || activeSection === 'performance-eps' }">
          <span class="nav-title">
            <span class="nav-icon">💵</span>
            <span class="nav-label">DESC EPS</span>
          </span>
          <span class="toggle-icon">{{ epsExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="epsExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('eps')" class="nav-link indent" :class="{ active: activeSection === 'eps' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-eps')" class="nav-link indent" :class="{ active: activeSection === 'performance-eps' }">
            📊 Performance
          </a>
        </div>

          <div class="nav-section-header" @click.stop="toggleDivers" :class="{ active: activeSection === 'divers' || activeSection === 'performance-divers' }">
          <span class="nav-title">
            <span class="nav-icon">💼</span>
            <span class="nav-label">PRODUITS DIVERS</span>
          </span>
          <span class="toggle-icon">{{ diversExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="diversExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('divers')" class="nav-link indent" :class="{ active: activeSection === 'divers' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-divers')" class="nav-link indent" :class="{ active: activeSection === 'performance-divers' }">
            📊 Performance
          </a>
        </div>
        <div class="nav-section-header" @click.stop="toggleObjectives" :class="{ active: activeSection === 'objectives' }">
          <span class="nav-title">
            <span class="nav-icon">🎯</span>
            <span class="nav-label">Objectifs</span>
          </span>
          <span class="toggle-icon">{{ objectivesExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="objectivesExpanded" class="nav-section-items">
          <a v-if="profileCode !== 'MD'" href="#" @click.stop.prevent="handleObjectiveSubSection('add')" class="nav-link indent" :class="{ active: activeSubSection === 'add' }">➕ Ajouter</a>
          <a href="#" @click.stop.prevent="handleObjectiveSubSection('validation')" class="nav-link indent" :class="{ active: activeSubSection === 'validation' }">✅ Valider</a>
         
        </div>

        <div class="nav-section-header" @click.stop="toggleReportingFinancier" :class="{ active: activeSection === 'reporting-financier' }">
          <span class="nav-title">
            <span class="nav-icon">📑</span>
            <span class="nav-label">Reporting Financier</span>
          </span>
          <span class="toggle-icon">{{ reportingFinancierExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="reportingFinancierExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="handleReportingFinancierSection('reference-compte')" class="nav-link indent" :class="{ active: activeSection === 'reporting-financier' && activeSubSection === 'reference-compte' }">
            Référence compte
          </a>
          <a href="#" @click.stop.prevent="handleReportingFinancierSection('cr-par-agence')" class="nav-link indent" :class="{ active: activeSection === 'reporting-financier' && activeSubSection === 'cr-par-agence' }">
            CR par Agence
          </a>
        </div>

        <template v-if="isAdmin">
          <div class="nav-section-header" @click.stop="toggleManagement" :class="{ active: activeSection === 'management' || activeSection === 'performance-management' || activeSection === 'environments' }">
            <span class="nav-title">
              <span class="nav-icon">⚙️</span>
              <span class="nav-label">Gestion</span>
            </span>
            <span class="toggle-icon">{{ managementExpanded ? '▼' : '▶' }}</span>
          </div>
          <div v-if="managementExpanded" class="nav-section-items">
            <a href="#" @click.stop.prevent="selectSection('management')" class="nav-link indent" :class="{ active: activeSection === 'management' }">
              Données
            </a>
            <a href="#" @click.stop.prevent="selectSection('environments')" class="nav-link indent" :class="{ active: activeSection === 'environments' }">
              Environnements
            </a>
          </div>
        </template>
      </div>
    </nav>
    <div class="sidebar-footer">
      <div> <img src="/téléchargement.jpeg" alt="COFINA Logo" class="building-image"></div>
    </div>
  </aside>
</template>

<script>
import { ProfileManager } from '../utils/profiles.js';

export default {
  name: 'Sidebar',
  props: {
    selectedZone: {
      type: String,
      default: null
    },
    activeSection: {
      type: String,
      default: 'client'
    },
    activeSubSection: {
      type: String,
      default: 'production'
    }
  },
  data() {
    return {
      clientExpanded: true,
      depotExpanded: false,
      creditExpanded: false,
      zoneExpanded: true,
      objectivesExpanded: false,
      performanceExpanded: false,
      prepaidCardsExpanded: false,
      managementExpanded: false,
      moneyTransfersExpanded: false,
      epsExpanded: false,
      diversExpanded: false,
      portefeuilleRisqueExpanded: false,
      reportingFinancierExpanded: false
    }
  },
  watch: {
    activeSection(newVal) {
      if (newVal === 'client' || newVal === 'performance-client') {
        this.clientExpanded = true;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'collection' || newVal === 'performance-collection' || newVal === 'domiciliation-flux' || newVal === 'encours-dat' || newVal === 'encours-epargne' || newVal === 'depot-garantie') {
        this.depotExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'production' || newVal === 'renouvellement' || newVal === 'restructuration' || newVal === 'commission-credit' || newVal === 'recouvrement' || newVal === 'portefeuille-risque' || newVal === 'performance-credit') {
        this.creditExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
        if (newVal === 'portefeuille-risque') {
          this.portefeuilleRisqueExpanded = true;
        }
      } else if (newVal === 'objectives' || newVal === 'performance-objectives') {
        this.objectivesExpanded = true;
        this.clientExpanded = false;
        this.performanceExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'performance') {
        this.performanceExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'prepaid-cards' || newVal === 'performance-prepaid-cards') {
        this.prepaidCardsExpanded = true;
        this.performanceExpanded = false;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'money-transfers' || newVal === 'performance-money-transfers') {
        this.moneyTransfersExpanded = true;
        this.managementExpanded = false;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      } else if (newVal === 'eps' || newVal === 'performance-eps') {
        this.epsExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'divers' || newVal === 'performance-divers') {
        this.diversExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'reporting-financier') {
        this.reportingFinancierExpanded = true;
        this.clientExpanded = false;
        this.depotExpanded = false;
        this.creditExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
        this.prepaidCardsExpanded = false;
        this.moneyTransfersExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      } else if (newVal === 'management' || newVal === 'performance-management' || newVal === 'environments') {
        this.managementExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.moneyTransfersExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      }
    }
  },
  mounted() {
    // Initialiser l'état selon la section active
    if (this.activeSection === 'client' || this.activeSection === 'performance-client') {
      this.clientExpanded = true;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'collection' || this.activeSection === 'performance-collection' || this.activeSection === 'domiciliation-flux' || this.activeSection === 'encours-dat' || this.activeSection === 'encours-epargne' || this.activeSection === 'depot-garantie') {
      this.depotExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
      } else if (this.activeSection === 'production' || this.activeSection === 'renouvellement' || this.activeSection === 'restructuration' || this.activeSection === 'commission-credit' || this.activeSection === 'recouvrement' || this.activeSection === 'portefeuille-risque' || this.activeSection === 'performance-credit') {
        this.creditExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
        if (this.activeSection === 'portefeuille-risque') {
          this.portefeuilleRisqueExpanded = true;
        }
    } else if (this.activeSection === 'objectives' || this.activeSection === 'performance-objectives') {
      this.clientExpanded = false;
      this.objectivesExpanded = true;
      this.performanceExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'performance') {
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = true;
      this.managementExpanded = false;
    } else if (this.activeSection === 'prepaid-cards' || this.activeSection === 'performance-prepaid-cards') {
      this.prepaidCardsExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'money-transfers' || this.activeSection === 'performance-money-transfers') {
      this.moneyTransfersExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = false;
      this.epsExpanded = false;
      this.diversExpanded = false;
    } else if (this.activeSection === 'eps' || this.activeSection === 'performance-eps') {
        this.epsExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (this.activeSection === 'divers' || this.activeSection === 'performance-divers') {
      this.diversExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'reporting-financier') {
      this.reportingFinancierExpanded = true;
      this.clientExpanded = false;
      this.depotExpanded = false;
      this.creditExpanded = false;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
      this.prepaidCardsExpanded = false;
      this.moneyTransfersExpanded = false;
      this.epsExpanded = false;
      this.diversExpanded = false;
    } else if (this.activeSection === 'management' || this.activeSection === 'performance-management' || this.activeSection === 'environments') {
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = true;
      this.moneyTransfersExpanded = false;
      this.epsExpanded = false;
      this.diversExpanded = false;
    }
  },
  computed: {
    profileCode() {
      return ProfileManager.getProfileCode();
    },
    isAdmin() {
      return ProfileManager.isAdmin();
    }
  },
  methods: {
    /** Ferme toutes les sections du menu sauf celle indiquée (comportement accordéon). */
    closeAllNavSectionsExcept(except) {
      const keep = {
        client: 'clientExpanded',
        depot: 'depotExpanded',
        credit: 'creditExpanded',
        prepaidCards: 'prepaidCardsExpanded',
        moneyTransfers: 'moneyTransfersExpanded',
        eps: 'epsExpanded',
        divers: 'diversExpanded',
        objectives: 'objectivesExpanded',
        reportingFinancier: 'reportingFinancierExpanded',
        management: 'managementExpanded'
      };
      const keepProp = keep[except];
      Object.values(keep).forEach((prop) => {
        if (prop !== keepProp) {
          this[prop] = false;
        }
      });
      this.performanceExpanded = false;
      if (except !== 'credit') {
        this.portefeuilleRisqueExpanded = false;
      }
    },
    toggleClient() {
      const next = !this.clientExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('client');
      }
      this.clientExpanded = next;
    },
    toggleDepot() {
      const next = !this.depotExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('depot');
      }
      this.depotExpanded = next;
    },
    toggleCredit() {
      const next = !this.creditExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('credit');
      }
      this.creditExpanded = next;
      if (!next) {
        this.portefeuilleRisqueExpanded = false;
      }
    },
    togglePrepaidCards() {
      const next = !this.prepaidCardsExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('prepaidCards');
      }
      this.prepaidCardsExpanded = next;
    },
    toggleMoneyTransfers() {
      const next = !this.moneyTransfersExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('moneyTransfers');
      }
      this.moneyTransfersExpanded = next;
    },
    toggleEps() {
      const next = !this.epsExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('eps');
      }
      this.epsExpanded = next;
    },
    toggleDivers() {
      const next = !this.diversExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('divers');
      }
      this.diversExpanded = next;
    },
    togglePortefeuilleRisque() {
      this.portefeuilleRisqueExpanded = !this.portefeuilleRisqueExpanded;
    },
    handlePortefeuilleRisqueSection(subSection) {
      this.$emit('section-selected', 'portefeuille-risque');
      this.$nextTick(() => {
        this.$emit('sub-section-selected', subSection);
      });
    },
    toggleObjectives() {
      const next = !this.objectivesExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('objectives');
      }
      this.objectivesExpanded = next;
      // Toujours sélectionner la section objectives quand on clique sur le header
      this.$emit('section-selected', 'objectives');
    },
    handleObjectiveSubSection(subSection) {
      // S'assurer que la section objectives est sélectionnée et définir la sous-section
      this.$emit('section-selected', 'objectives');
      // Utiliser setTimeout pour s'assurer que la section est bien mise à jour avant la sous-section
      setTimeout(() => {
        this.$emit('sub-section-selected', subSection);
      }, 0);
    },
    toggleReportingFinancier() {
      const next = !this.reportingFinancierExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('reportingFinancier');
      }
      this.reportingFinancierExpanded = next;
      if (this.reportingFinancierExpanded) {
        this.$emit('section-selected', 'reporting-financier');
      }
    },
    handleReportingFinancierSection(subSection) {
      this.$emit('section-selected', 'reporting-financier');
      this.$nextTick(() => {
        this.$emit('sub-section-selected', subSection);
      });
    },
    toggleManagement() {
      const next = !this.managementExpanded;
      if (next) {
        this.closeAllNavSectionsExcept('management');
      }
      this.managementExpanded = next;
    },
    handlePrepaidCardSection(subSection) {
      this.$emit('section-selected', 'prepaid-cards');
      this.$nextTick(() => {
        this.$emit('sub-section-selected', subSection);
      });
    },
    selectSection(section) {
      // Gérer l'expansion des sections selon la section sélectionnée
      if (section === 'client' || section === 'performance-client') {
        this.clientExpanded = true;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'collection' || section === 'performance-collection' || section === 'domiciliation-flux' || section === 'encours-dat' || section === 'encours-epargne' || section === 'depot-garantie') {
        this.depotExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'production' || section === 'renouvellement' || section === 'restructuration' || section === 'commission-credit' || section === 'recouvrement' || section === 'portefeuille-risque' || section === 'performance-credit') {
        this.creditExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
        if (section === 'portefeuille-risque') {
          this.portefeuilleRisqueExpanded = true;
        }
      } else if (section === 'objectives' || section === 'performance-objectives') {
        this.objectivesExpanded = true;
        this.clientExpanded = false;
        this.performanceExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'performance') {
        this.performanceExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'prepaid-cards' || section === 'performance-prepaid-cards') {
        this.prepaidCardsExpanded = true;
        this.performanceExpanded = false;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'money-transfers' || section === 'performance-money-transfers') {
        this.moneyTransfersExpanded = true;
        this.managementExpanded = false;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      } else if (section === 'eps' || section === 'performance-eps') {
        this.epsExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'divers' || section === 'performance-divers') {
        this.diversExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'reporting-financier') {
        this.reportingFinancierExpanded = true;
        this.clientExpanded = false;
        this.depotExpanded = false;
        this.creditExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
        this.prepaidCardsExpanded = false;
        this.moneyTransfersExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      } else if (section === 'management' || section === 'performance-management' || section === 'environments') {
        this.managementExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.moneyTransfersExpanded = false;
        this.epsExpanded = false;
        this.diversExpanded = false;
      }
      this.$emit('section-selected', section);
    },
    selectSubSection(subSection) {
      this.$emit('sub-section-selected', subSection);
    },
    toggleZone() {
      this.zoneExpanded = !this.zoneExpanded;
    },
    selectZone(zone) {
      this.$emit('zone-selected', zone);
      console.log('Zone sélectionnée:', zone);
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background: linear-gradient(180deg, #ffffff, #f5f5f5);
  border-right: 1px solid #e5e7eb;
  height: 100%;
  max-height: 100vh;
  min-height: 0;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(15, 23, 42, 0.06);
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 0 0;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.nav-section {
  margin-top: 4px;
}

.nav-section-header {
  padding: 10px 20px;
  font-size: 0.8rem; /* ~13px */
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s ease, color 0.2s ease;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: auto;
  position: relative;
  z-index: 1;
}

.nav-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.nav-icon {
  font-size: 1rem;
}

.nav-label {
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.nav-section-header.indent {
  padding-left: 35px;
  font-size: 0.78rem;
}

.nav-section-header:hover {
  background-color: #e5e7eb;
}

.nav-section-header.active {
  background-color: #1A4D3A !important;
  color: #ffffff !important;
  box-shadow: inset 4px 0 0 #34d399;
}

.toggle-icon {
  font-size: 0.7rem;
  color: inherit;
  opacity: 0.75;
}

.nav-section-items {
  display: flex;
  flex-direction: column;
  padding: 4px 0 6px;
}

.nav-link {
  color: #374151;
  text-decoration: none;
  padding: 8px 22px;
  font-size: 0.85rem;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  display: block;
  cursor: pointer;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: auto;
  position: relative;
  z-index: 1;
  border-left: 3px solid transparent;
}

.nav-link.indent {
  padding-left: 32px;
}

.nav-link.double-indent {
  padding-left: 44px;
}

.nav-link:hover {
  background-color: #edf2f7;
  color: #1A4D3A;
}

.nav-link.active {
  background-color: rgba(26, 77, 58, 0.12) !important;
  color: #1A4D3A !important;
  font-weight: 600;
  border-left-color: #1A4D3A;
}

.nav-button {
  margin: 4px 12px;
  padding: 10px 16px;
  border-radius: 6px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.nav-button:hover {
  background-color: #f3f4f6;
  border-color: #1A4D3A;
  box-shadow: 0 2px 4px rgba(26, 77, 58, 0.1);
  transform: translateY(-1px);
}

.nav-button.active {
  background-color: #1A4D3A !important;
  color: #ffffff !important;
  border-color: #1A4D3A !important;
  box-shadow: 0 2px 6px rgba(26, 77, 58, 0.2);
  font-weight: 600;
}

.nav-button.active:hover {
  background-color: #153d2a !important;
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  background-color: rgba(26, 77, 58, 0.06);
  font-weight: 600;
}

.sidebar-footer {
  margin-top: auto;
  flex-shrink: 0;
  padding: 16px 20px 20px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.sidebar-footer > div {
  width: 100%;
}

.building-image {
  width: 100%;
  height: 140px;
  max-height: 140px;
  object-fit: cover;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.15);
  display: block;
}

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .sidebar {
    width: 220px;
  }
  
  .sidebar-nav {
    padding-bottom: 0;
  }
  
  .nav-section-header {
    padding: 10px 15px;
    font-size: 0.75rem;
  }
  
  .nav-link {
    padding: 8px 18px;
    font-size: 0.8rem;
  }
  
  .nav-link.indent {
    padding-left: 28px;
  }
  
  .nav-link.double-indent {
    padding-left: 38px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .sidebar {
    width: 200px;
    min-width: 200px;
  }
  
  .nav-section-header {
    padding: 10px 15px;
    font-size: 0.75rem;
  }
  
  .nav-link {
    padding: 8px 18px;
    font-size: 0.8rem;
  }
  
  .nav-link.indent {
    padding-left: 25px;
  }
  
  .nav-link.double-indent {
    padding-left: 35px;
  }
  
  .sidebar-nav {
    padding-bottom: 0;
  }
  
  .sidebar-footer {
    padding: 12px 15px 15px;
  }
  
  .building-image {
    height: 120px;
    max-height: 120px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .sidebar {
    width: 100%;
  }
  
  .nav-section-header {
    padding: 10px 15px;
    font-size: 0.8rem;
  }
  
  .nav-icon {
    font-size: 0.9rem;
  }
  
  .nav-label {
    font-size: 0.75rem;
  }
  
  .nav-link {
    padding: 8px 18px;
    font-size: 0.8rem;
  }
  
  .nav-link.indent {
    padding-left: 25px;
  }
  
  .nav-link.double-indent {
    padding-left: 35px;
  }
  
  .sidebar-nav {
    padding-bottom: 0;
  }
  
  .sidebar-footer {
    padding: 10px 12px 12px;
  }
  
  .building-image {
    height: 100px;
    max-height: 100px;
  }
}
</style>

