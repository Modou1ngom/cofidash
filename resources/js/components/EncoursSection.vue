<template>
  <div class="encours-section">
    <div class="encours-tabs">
      
      <button 
        @click="handleTabChange('compte-courant')" 
        class="encours-tab" 
        :class="{ active: activeTab === 'compte-courant' }"
      >
        ENCOURS COMPTE COURANT
      </button>
      <div class="encours-tab-group">
        <button 
          @click="handleTabChange('epargne-pep-simple')" 
          class="encours-tab" 
          :class="{ active: activeTab === 'epargne-pep-simple' }"
        >
          ENCOURS EPARGNE
        </button>
        <div v-if="isEpargneTabActive" class="sub-tabs">
          <button 
            @click.stop="handleSubTabChange('epargne-simple')" 
            class="sub-tab" 
            :class="{ active: activeTab === 'epargne-simple' }"
          >
            SIMPLE
          </button>
          <button 
            @click.stop="handleSubTabChange('epargne-projet')" 
            class="sub-tab" 
            :class="{ active: activeTab === 'epargne-projet' }"
          >
           PROJET
          </button>
        </div>
      </div>
      <button 
        @click="goToDashboardEpargne" 
        class="encours-tab dashboard-epargne-tab"
        :class="{ active: activeTab === 'dashboard-epargne' }"
      >
        📊 Dashboard Épargne
      </button>
    </div>
    
    <EncoursCompteCourantSection 
      v-if="activeTab === 'compte-courant'"
      :selectedZoneProp="selectedZoneProp"
    />
    
    <EncoursEpargnePepSimpleSection 
      v-if="isEpargneTabActive || activeTab === 'epargne-pep-simple'"
      :key="`epargne-${activeTab}`"
      :selectedZoneProp="selectedZoneProp"
      :filterType="activeTab"
    />
    
    <DashboardEpargneSection 
      v-if="activeTab === 'dashboard-epargne'"
      :selectedZoneProp="selectedZoneProp"
    />
  </div>
</template>

<script>
import EncoursCompteCourantSection from './EncoursCompteCourantSection.vue';
import EncoursEpargnePepSimpleSection from './EncoursEpargnePepSimpleSection.vue';
import DashboardEpargneSection from './DashboardEpargneSection.vue';

export default {
  name: 'EncoursSection',
  components: {
    EncoursCompteCourantSection,
    EncoursEpargnePepSimpleSection,
    DashboardEpargneSection
  },
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      activeTab: 'epargne-pep-simple'
    }
  },
  computed: {
    isEpargneTabActive() {
      return this.activeTab === 'epargne-simple' || 
             this.activeTab === 'epargne-projet' ||
             this.activeTab === 'epargne-pep-simple';
    }
  },
  methods: {
    goToDashboardEpargne() {
      this.activeTab = 'dashboard-epargne';
    },
    handleTabChange(tab) {
      if (tab === 'epargne-pep-simple') {
        // Si on clique sur l'onglet principal, on affiche tout (epargne-pep-simple)
        this.activeTab = 'epargne-pep-simple';
      } else {
        this.activeTab = tab;
      }
    },
    handleSubTabChange(subTab) {
      this.activeTab = subTab;
    }
  }
}
</script>

<style scoped>
.encours-section {
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

.encours-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0;
  background: #f9fafb;
  padding: 8px;
  border-radius: 8px 8px 0 0;
  flex-wrap: wrap;
  align-items: flex-start;
}

.encours-tab-group {
  position: relative;
  display: flex;
  flex-direction: column;
}

.encours-tab {
  padding: 12px 20px;
  font-size: 13px;
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
  white-space: nowrap;
}

.encours-tab:hover {
  color: #1A4D3A;
  background-color: #f0fdf4;
  border-color: #1A4D3A;
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(26, 77, 58, 0.15);
}

.encours-tab.active {
  color: #ffffff;
  font-weight: 600;
  background-color: #1A4D3A;
  border-color: #1A4D3A;
  box-shadow: 0 2px 8px rgba(26, 77, 58, 0.3);
  z-index: 1;
}

.encours-tab.active:hover {
  background-color: #153d2a;
}

.dashboard-epargne-tab {
  background: linear-gradient(135deg, #1A4D3A 0%, #2d6a4f 100%);
  color: white;
  font-weight: 600;
}

.dashboard-epargne-tab:hover {
  background: linear-gradient(135deg, #153d2a 0%, #1A4D3A 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(26, 77, 58, 0.4);
}

.sub-tabs {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  padding-left: 8px;
  flex-wrap: wrap;
}

.sub-tab {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.sub-tab:hover {
  color: #1A4D3A;
  background-color: #f0fdf4;
  border-color: #1A4D3A;
}

.sub-tab.active {
  color: #ffffff;
  font-weight: 600;
  background-color: #1A4D3A;
  border-color: #1A4D3A;
}

.sub-tab.active:hover {
  background-color: #153d2a;
}

.section-placeholder {
  padding: 40px;
  text-align: center;
  background: #f9fafb;
  border-radius: 8px;
  margin-top: 20px;
}

.section-placeholder h3 {
  color: #1A4D3A;
  margin-bottom: 10px;
  font-size: 20px;
}

.section-placeholder p {
  color: #6b7280;
  font-size: 16px;
}
</style>
