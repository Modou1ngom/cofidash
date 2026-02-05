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
        <div class="nav-section-header" @click.stop="selectSection('collection')" :class="{ active: activeSection === 'collection' || activeSection === 'performance-collection' }">
          <span class="nav-title">
            <span class="nav-icon">💰</span>
            <span class="nav-label">DEPOT</span>
          </span>
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
        <div class="nav-section-header" @click.stop="toggleCredit" :class="{ active: activeSection === 'production' || activeSection === 'renouvellement' || activeSection === 'restructuration' || activeSection === 'commission-credit' || activeSection === 'recouvrement' }">
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
          <a href="#" @click.stop.prevent="selectSection('renouvellement')" class="nav-link indent" :class="{ active: activeSection === 'renouvellement' }">
            Renouvellement
          </a>
          <a href="#" @click.stop.prevent="selectSection('restructuration')" class="nav-link indent" :class="{ active: activeSection === 'restructuration' }">
            Restructuration
          </a>
          <a href="#" @click.stop.prevent="selectSection('commission-credit')" class="nav-link indent" :class="{ active: activeSection === 'commission-credit' }">
            Commission de crédit
          </a>
          <a href="#" @click.stop.prevent="selectSection('recouvrement')" class="nav-link indent" :class="{ active: activeSection === 'recouvrement' }">
            Recouvrement
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
        <div class="nav-section-header" @click.stop="toggleEps" :class="{ active: activeSection === 'eps ' || activeSection === 'performance-eps' }">
          <span class="nav-title">
            <span class="nav-icon">💵</span>
            <span class="nav-label">DESC EPS </span>
          </span>
          <span class="toggle-icon">{{ epsExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="epsExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('eps ')" class="nav-link indent" :class="{ active: activeSection === 'eps ' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-eps')" class="nav-link indent" :class="{ active: activeSection === 'performance-eps' }">
            📊 Performance
          </a>
        </div>

          <div class="nav-section-header" @click.stop="toggleDivers" :class="{ active: activeSection === 'divers ' || activeSection === 'performance-divers' }">
          <span class="nav-title">
            <span class="nav-icon">💼</span>
            <span class="nav-label">PRODUITS DIVERS </span>
          </span>
          <span class="toggle-icon">{{ diversExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="diversExpanded" class="nav-section-items">
          <a href="#" @click.stop.prevent="selectSection('divers ')" class="nav-link indent" :class="{ active: activeSection === 'divers ' }">
            Données
          </a>
          <a href="#" @click.stop.prevent="selectSection('performance-divers')" class="nav-link indent" :class="{ active: activeSection === 'performance-divers' }">
            📊 Performance
          </a>
        </div>
        <div class="nav-section-header" @click.stop="selectSection('objectives')" :class="{ active: activeSection === 'objectives' }">
          <span class="nav-title">
            <span class="nav-icon">🎯</span>
            <span class="nav-label">Objectifs</span>
          </span>
          <span class="toggle-icon">{{ objectivesExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-if="activeSection === 'objectives'" class="nav-section-items">
          <a v-if="profileCode !== 'MD'" href="#" @click.stop.prevent="selectSubSection('add')" class="nav-link indent" :class="{ active: activeSubSection === 'add' }">➕ Ajouter</a>
          <a href="#" @click.stop.prevent="selectSubSection('validation')" class="nav-link indent" :class="{ active: activeSubSection === 'validation' }">✅ Valider</a>
         
        </div>

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
      creditExpanded: false,
      zoneExpanded: true,
      objectivesExpanded: false,
      performanceExpanded: false,
      prepaidCardsExpanded: false,
      managementExpanded: false,
      moneyTransfersExpanded: false,
      epsExpanded: false,
      diversExpanded: false
    }
  },
  watch: {
    activeSection(newVal) {
      if (newVal === 'client' || newVal === 'performance-client') {
        this.clientExpanded = true;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'collection' || newVal === 'performance-collection') {
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'production' || newVal === 'renouvellement' || newVal === 'restructuration' || newVal === 'commission-credit' || newVal === 'recouvrement' || newVal === 'performance-credit') {
        this.creditExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
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
      } else if (newVal === 'eps ' || newVal === 'performance-eps') {
        this.epsExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'divers ' || newVal === 'performance-divers') {
        this.diversExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (newVal === 'management' || newVal === 'performance-management' || newVal === 'environments') {
        this.managementExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
      }
    }
  },
  mounted() {
    // Initialiser l'état selon la section active
    if (this.activeSection === 'client' || this.activeSection === 'performance-client') {
      this.clientExpanded = true;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'collection' || this.activeSection === 'performance-collection') {
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'production' || this.activeSection === 'renouvellement' || this.activeSection === 'restructuration' || this.activeSection === 'commission-credit' || this.activeSection === 'recouvrement' || this.activeSection === 'performance-credit') {
      this.creditExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.managementExpanded = false;
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
    } else if (this.activeSection === 'eps ' || this.activeSection === 'performance-eps') {
      this.epsExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'divers ' || this.activeSection === 'performance-divers') {
      this.diversExpanded = true;
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = false;
    } else if (this.activeSection === 'management' || this.activeSection === 'performance-management' || this.activeSection === 'environments') {
      this.clientExpanded = false;
      this.objectivesExpanded = false;
      this.performanceExpanded = false;
      this.prepaidCardsExpanded = false;
      this.managementExpanded = true;
    }
  },
  computed: {
    profileCode() {
      return ProfileManager.getProfileCode();
    }
  },
  methods: {
    toggleClient() {
      this.clientExpanded = !this.clientExpanded;
    },
    toggleCredit() {
      this.creditExpanded = !this.creditExpanded;
    },
    togglePrepaidCards() {
      this.prepaidCardsExpanded = !this.prepaidCardsExpanded;
    },
    toggleMoneyTransfers() {
      this.moneyTransfersExpanded = !this.moneyTransfersExpanded;
    },
    toggleEps() {
      this.epsExpanded = !this.epsExpanded;
    },
    toggleDivers() {
      this.diversExpanded = !this.diversExpanded;
    },
    toggleManagement() {
      this.managementExpanded = !this.managementExpanded;
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
      } else if (section === 'collection' || section === 'performance-collection') {
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'production' || section === 'renouvellement' || section === 'restructuration' || section === 'commission-credit' || section === 'recouvrement' || section === 'performance-credit') {
        this.creditExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.managementExpanded = false;
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
      } else if (section === 'eps ' || section === 'performance-eps') {
        this.epsExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'divers ' || section === 'performance-divers') {
        this.diversExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
        this.managementExpanded = false;
      } else if (section === 'management' || section === 'performance-management' || section === 'environments') {
        this.managementExpanded = true;
        this.clientExpanded = false;
        this.objectivesExpanded = false;
        this.performanceExpanded = false;
        this.prepaidCardsExpanded = false;
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
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff, #f5f5f5);
  border-right: 1px solid #e5e7eb;
  height: 100%;
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(15, 23, 42, 0.06);
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
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
  box-shadow: inset 4px 0 0 #f97316;
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
  padding: 16px 20px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90px;
  background: #f9fafb;
}

.building-image {
  width: 100%;
  height: 140px;
  object-fit: cover;
  border-radius: 10px;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.15);
}
</style>

