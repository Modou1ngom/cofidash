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
        <PortefeuilleRisqueSection v-if="activeSection === 'portefeuille-risque' && activeSubSection === 'simple'" />
        <PortefeuilleRisqueGlobalSection v-if="activeSection === 'portefeuille-risque' && activeSubSection === 'global'" />
        
        <!-- Sections DEPOT -->
        <div v-if="activeSection === 'domiciliation-flux'" class="section-placeholder">
          <h2>Domiciliation de flux</h2>
          <p>Section Domiciliation de flux en cours de développement</p>
        </div>
        <VolumeDatSection v-if="activeSection === 'encours-dat'" />
        <EncoursSection v-if="activeSection === 'encours-epargne'" :selectedZoneProp="selectedZone" />
        <DepotGarantieSection v-if="activeSection === 'depot-garantie'" />
        
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
        <ReferenceCompteSection v-if="activeSection === 'reporting-financier' && activeSubSection === 'reference-compte'" />
        <CRParAgenceSection v-if="activeSection === 'reporting-financier' && activeSubSection === 'cr-par-agence'" />
        <div v-if="activeSection === 'reporting-financier' && !activeSubSection" class="section-placeholder">
          <h2>Reporting Financier</h2>
          <p>Sélectionnez un sous-menu dans la barre latérale.</p>
        </div>
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
import DepotGarantieSection from '../components/DepotGarantieSection.vue';
import VolumeDatSection from '../components/VolumeDatSection.vue';
import EncoursSection from '../components/EncoursSection.vue';
import PortefeuilleRisqueSection from '../components/PortefeuilleRisqueSection.vue';
import PortefeuilleRisqueGlobalSection from '../components/PortefeuilleRisqueGlobalSection.vue';
import CRParAgenceSection from '../components/CRParAgenceSection.vue';
import ReferenceCompteSection from '../components/ReferenceCompteSection.vue';
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
    EnvironmentsSection,
    DepotGarantieSection,
    VolumeDatSection,
    EncoursSection,
    PortefeuilleRisqueSection,
    PortefeuilleRisqueGlobalSection,
    CRParAgenceSection,
    ReferenceCompteSection
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
      } else if (section === 'portefeuille-risque') {
        // Si aucune sous-section n'est définie, utiliser 'simple' par défaut
        if (!this.activeSubSection || (this.activeSubSection !== 'simple' && this.activeSubSection !== 'global')) {
          this.activeSubSection = 'simple';
        }
      } else if (section === 'objectives') {
        // Ne pas forcer la sous-section si elle est déjà 'add' ou 'validation'
        // Sinon, pour le MD, rediriger vers 'validation' au lieu de 'add'
        if (this.activeSubSection !== 'add' && this.activeSubSection !== 'validation') {
          const profileCode = ProfileManager.getProfileCode();
          this.activeSubSection = profileCode === 'MD' ? 'validation' : 'add';
        }
      } else if (section === 'client') {
        this.activeSubSection = null;
      } else if (section === 'collection') {
        this.activeSubSection = null;
      } else if (section === 'domiciliation-flux' || section === 'encours-dat' || section === 'encours-epargne' || section === 'depot-garantie') {
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
  width: 100%;
  min-height: 100vh;
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
  flex-shrink: 0;
  display: flex;
  align-items: stretch;
}

.dashboard-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #FFFFFF;
  display: flex;
}

.main-content {
  flex: 1;
  min-width: 0;
  width: 100%;
  background: #FFFFFF;
  overflow-y: auto;
  overflow-x: auto;
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

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .main-content {
    padding: 15px;
  }
  
  .production-tabs {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .production-tab {
    padding: 10px 18px;
    font-size: 13px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .dashboard-body {
    flex-direction: column;
  }
  
  .dashboard-body :deep(.sidebar) {
    max-height: 45vh;
  }
  
  .main-content {
    padding: 15px;
    width: 100%;
    flex: 1;
    min-height: 0;
  }
  
  .production-tabs {
    flex-direction: column;
    gap: 4px;
  }
  
  .production-tab {
    width: 100%;
    padding: 10px 16px;
    font-size: 13px;
    border-radius: 6px;
    bottom: 0;
  }
  
  .section-placeholder {
    padding: 30px 20px;
  }
  
  .section-placeholder h2 {
    font-size: 20px;
  }
  
  .section-placeholder p {
    font-size: 14px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .main-content {
    padding: 10px;
  }
  
  .production-tabs {
    padding: 6px;
  }
  
  .production-tab {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .section-placeholder {
    padding: 20px 15px;
  }
  
  .section-placeholder h2 {
    font-size: 18px;
  }
  
  .section-placeholder p {
    font-size: 13px;
  }
}
</style>

