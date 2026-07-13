<template>
  <div class="dashboard">
    <div class="top-grey-bar"></div>
    <div class="dashboard-top">
      <DashboardHeader />
    </div>
    <div class="dashboard-body">
      <Sidebar
        :selected-zone="selectedZone"
        :active-section="activeSection"
        :active-sub-section="activeSubSection"
        @zone-selected="selectedZone = $event"
        @section-selected="handleSectionSelected"
        @sub-section-selected="activeSubSection = $event"
      />
      <div class="main-content">
        <router-view v-slot="{ Component, route }">
          <keep-alive include="CafVueEnsemblePage,Vue360Page">
            <component
              :is="Component"
              v-if="route.meta.keepAlive"
              :key="route.name"
            />
          </keep-alive>
          <component
            :is="Component"
            v-if="!route.meta.keepAlive"
            :key="route.fullPath"
          />
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import DashboardHeader from '../components/DashboardHeader.vue';
import Sidebar from '../components/Sidebar.vue';

export default {
  name: 'DashboardLayout',
  components: { DashboardHeader, Sidebar },
  data() {
    return {
      selectedZone: null,
      activeSubSection: null,
    };
  },
  computed: {
    activeSection() {
      if (this.$route.path.startsWith('/vue360/caf')) {
        return 'caf-overview';
      }
      if (this.$route.path.startsWith('/vue360/recherche') || this.$route.path.startsWith('/vue360/clients')) {
        return 'vue360';
      }
      return 'vue360';
    },
  },
  methods: {
    handleSectionSelected(section) {
      if (section === 'caf-overview') {
        if (!this.$route.path.startsWith('/vue360/caf')) {
          this.$router.push('/vue360/caf');
        }
        return;
      }
      if (section === 'vue360') {
        if (!this.$route.path.startsWith('/vue360/recherche') && !this.$route.path.startsWith('/vue360/clients')) {
          this.$router.push('/vue360/recherche');
        }
        return;
      }
      sessionStorage.setItem('dashboardSection', section);
      this.$router.push('/dashboard');
    },
  },
};
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-grey-bar {
  width: 100%;
  height: 4px;
  background: #2a2a2a;
  flex-shrink: 0;
}

.dashboard-top {
  width: 100%;
  flex-shrink: 0;
}

.dashboard-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #fff;
  display: flex;
}

.main-content {
  flex: 1;
  min-width: 0;
  background: #eef1f4;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
}

@media (max-width: 768px) {
  .dashboard-body {
    flex-direction: column;
  }

  .dashboard-body :deep(.sidebar) {
    max-height: 45vh;
  }
}
</style>
