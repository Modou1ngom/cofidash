<template>
  <div class="dashboard">
    <div class="top-grey-bar"></div>
    <div class="dashboard-top">
      <DashboardHeader />
    </div>
    <div class="dashboard-body">
      <Sidebar 
        :selectedZone="selectedZone" 
        :activeSection="activeSection"
        :activeSubSection="activeSubSection"
        @zone-selected="handleZoneSelected"
        @section-selected="handleSectionSelected"
        @sub-section-selected="handleSubSectionSelected"
      />
      <div class="main-content">
        <ClientSection v-if="activeSection === 'client'" :selectedZoneProp="selectedZone" />
        <CollectionSection 
          v-if="activeSection === 'collection'" 
          :selectedZoneProp="selectedZone"
        />
        
        <!-- Section Production avec boutons de navigation -->
        <div v-if="activeSection === 'production'" class="production-wrapper">
          <div class="production-tabs">
            <button 
              @click="handleSubSectionSelected('production')" 
              class="production-tab" 
              :class="{ active: activeSubSection === 'production' }"
            >
              Production en nombre
            </button>
            <button 
              @click="handleSubSectionSelected('production-volume')" 
              class="production-tab" 
              :class="{ active: activeSubSection === 'production-volume' }"
            >
              Production en volume
            </button>
            <button 
              @click="handleSubSectionSelected('encours-credit')" 
              class="production-tab" 
              :class="{ active: activeSubSection === 'encours-credit' }"
            >
              Evolution encours crédit
            </button>
          </div>
          
          <ProductionSection v-if="activeSubSection === 'production'" :selectedZoneProp="selectedZone" />
          <ProductionVolumeSection v-if="activeSubSection === 'production-volume'" :selectedZoneProp="selectedZone" />
          <EncoursCreditSection v-if="activeSubSection === 'encours-credit'" />
        </div>
        
        <!-- Sections CREDIT -->
        <div v-if="activeSection === 'renouvellement'" class="section-placeholder">
          <h2>Renouvellement</h2>
          <p>Section Renouvellement en cours de développement</p>
        </div>
        <div v-if="activeSection === 'restructuration'" class="section-placeholder">
          <h2>Restructuration</h2>
          <p>Section Restructuration en cours de développement</p>
        </div>
        <div v-if="activeSection === 'commission-credit'" class="section-placeholder">
          <h2>Commission de crédit</h2>
          <p>Section Commission de crédit en cours de développement</p>
        </div>
        <div v-if="activeSection === 'recouvrement'" class="section-placeholder">
          <h2>Recouvrement</h2>
          <p>Section Recouvrement en cours de développement</p>
        </div>
        
        <AddObjectiveSection v-if="activeSection === 'objectives' && activeSubSection === 'add'" />
        <ValidationSection v-if="activeSection === 'objectives' && activeSubSection === 'validation'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance-client'" :dataType="'client'" />
        <AgencyPerformanceSection 
          v-if="activeSection === 'performance-collection'" 
          :dataType="'collection'"
        />
        <AgencyPerformanceSection v-if="activeSection === 'performance-credit'" :dataType="'credit'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance-prepaid-cards'" :dataType="'prepaid-cards'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance-money-transfers'" :dataType="'money-transfers'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance-eps'" :dataType="'eps'" />
        <AgencyPerformanceSection v-if="activeSection === 'performance-divers'" :dataType="'divers'" />
        <PrepaidCardSalesSection v-if="activeSection === 'prepaid-cards' && activeSubSection === 'sales'" />
        <PrepaidCardRechargeSection v-if="activeSection === 'prepaid-cards' && activeSubSection === 'recharge'" />
        <TerritoryAgencyManagement v-if="activeSection === 'management'" />
        <MoneyTransferSection v-if="activeSection === 'money-transfers'" />
        <EnvironmentsSection v-if="activeSection === 'environments'" />
      </div>
    </div>
  </div>
</template>

<script>
import DashboardHeader from '../components/DashboardHeader.vue';
import Sidebar from '../components/Sidebar.vue';
import ClientSection from '../components/ClientSection.vue';
import CollectionSection from '../components/CollectionSection.vue';
import ProductionSection from '../components/ProductionSection.vue';
import ProductionVolumeSection from '../components/ProductionVolumeSection.vue';
import EncoursCreditSection from '../components/EncoursCreditSection.vue';
import AddObjectiveSection from '../components/AddObjectiveSection.vue';
import ValidationSection from '../components/ValidationSection.vue';
import AgencyPerformanceSection from '../components/AgencyPerformanceSection.vue';
import PrepaidCardSalesSection from '../components/PrepaidCardSalesSection.vue';
import PrepaidCardRechargeSection from '../components/PrepaidCardRechargeSection.vue';
import TerritoryAgencyManagement from '../components/TerritoryAgencyManagement.vue';
import MoneyTransferSection from '../components/MoneyTransferSection.vue';
import EnvironmentsSection from '../components/EnvironmentsSection.vue';
import { ProfileManager } from '../utils/profiles.js';

export default {
  name: 'Dashboard',
  components: {
    DashboardHeader,
    Sidebar,
    ClientSection,
    CollectionSection,
    ProductionSection,
    ProductionVolumeSection,
    EncoursCreditSection,
    AddObjectiveSection,
    ValidationSection,
    AgencyPerformanceSection,
    PrepaidCardSalesSection,
    PrepaidCardRechargeSection,
    TerritoryAgencyManagement,
    MoneyTransferSection,
    EnvironmentsSection
  },
  data() {
    return {
      selectedZone: null,
      activeSection: 'client',
      activeSubSection: 'production'
    }
  },
  methods: {
    handleZoneSelected(zone) {
      this.selectedZone = zone;
    },
    handleSectionSelected(section) {
      console.log('Section sélectionnée:', section);
      this.activeSection = section;
      if (section === 'production') {
        this.activeSubSection = 'production';
      } else if (section === 'renouvellement' || section === 'restructuration' || section === 'commission-credit' || section === 'recouvrement') {
        this.activeSubSection = null;
      } else if (section === 'objectives') {
        // Pour le MD, rediriger vers 'validation' au lieu de 'add'
        const profileCode = ProfileManager.getProfileCode();
        this.activeSubSection = profileCode === 'MD' ? 'validation' : 'add';
      } else if (section === 'client') {
        this.activeSubSection = null;
      } else if (section === 'collection') {
        this.activeSubSection = null;
      } else if (section === 'environments') {
        this.activeSubSection = null;
      } else if (section === 'prepaid-cards') {
        this.activeSubSection = 'sales';
      } else if (section.startsWith('performance-')) {
        // Les sections de performance n'ont pas de sous-section
        this.activeSubSection = null;
      } else if (section === 'performance') {
        this.activeSubSection = null;
      }
      console.log('Active section:', this.activeSection, 'Active sub-section:', this.activeSubSection);
    },
    handleSubSectionSelected(subSection) {
      console.log('Sub-section sélectionnée:', subSection);
      this.activeSubSection = subSection;
    }
  }
}
</script>

<style scoped>
.dashboard {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-grey-bar {
  width: 100%;
  height: 4px;
  background: #2A2A2A;
}

.dashboard-top {
  width: 100%;
  display: flex;
  align-items: stretch;
}

.dashboard-body {
  flex: 1;
  overflow: hidden;
  background: #FFFFFF;
  display: flex;
}

.main-content {
  flex: 1;
  background: #FFFFFF;
  overflow-y: auto;
  padding: 20px;
}

.production-wrapper {
  width: 100%;
}

.production-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0;
  background: #f9fafb;
  padding: 8px;
  border-radius: 8px 8px 0 0;
}

.production-tab {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-bottom: none;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  bottom: -2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.production-tab:hover {
  color: #1A4D3A;
  background-color: #f0fdf4;
  border-color: #1A4D3A;
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(26, 77, 58, 0.15);
}

.production-tab.active {
  color: #ffffff;
  font-weight: 600;
  background-color: #1A4D3A;
  border-color: #1A4D3A;
  box-shadow: 0 2px 8px rgba(26, 77, 58, 0.3);
  z-index: 1;
}

.production-tab.active:hover {
  background-color: #153d2a;
}

.section-placeholder {
  padding: 40px;
  text-align: center;
  background: #f9fafb;
  border-radius: 8px;
  margin-top: 20px;
}

.section-placeholder h2 {
  color: #1A4D3A;
  margin-bottom: 10px;
  font-size: 24px;
}

.section-placeholder p {
  color: #6b7280;
  font-size: 16px;
}
</style>

