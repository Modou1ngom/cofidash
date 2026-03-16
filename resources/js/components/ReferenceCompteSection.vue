<template>
  <div class="reference-compte-section">
    <div class="section-header with-buttons">
      <h2 class="section-title">Référence compte</h2>
      <div class="view-buttons">
        <button
          type="button"
          class="view-btn"
          :class="{ active: currentView === 'ajout' }"
          @click="currentView = 'ajout'"
        >
          Ajouter
        </button>
        <button
          type="button"
          class="view-btn"
          :class="{ active: currentView === 'liste' }"
          @click="currentView = 'liste'"
        >
          Liste
        </button>
      </div>
    </div>

    <ReferenceCompteForm v-show="currentView === 'ajout'" @saved="onFormSaved" />
    <ReferenceCompteList ref="listRef" v-show="currentView === 'liste'" />
  </div>
</template>

<script>
import ReferenceCompteForm from './ReferenceCompteForm.vue';
import ReferenceCompteList from './ReferenceCompteList.vue';

export default {
  name: 'ReferenceCompteSection',
  components: {
    ReferenceCompteForm,
    ReferenceCompteList
  },
  data() {
    return {
      currentView: 'ajout'
    };
  },
  watch: {
    currentView(val) {
      if (val === 'liste') this.$refs.listRef?.load();
    }
  },
  methods: {
    onFormSaved() {
      this.$refs.listRef?.load();
    }
  }
};
</script>

<style scoped>
.reference-compte-section {
  padding: 0;
  width: 100%;
}

.section-header.with-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.35rem;
  color: #1A4D3A;
  margin: 0;
  font-weight: 600;
}

.view-buttons {
  display: flex;
  gap: 8px;
}

.view-btn {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
}

.view-btn:hover {
  background: #f3f4f6;
  border-color: #1A4D3A;
  color: #1A4D3A;
}

.view-btn.active {
  background: #1A4D3A;
  border-color: #1A4D3A;
  color: #fff;
}

.view-btn.active:hover {
  background: #153d2a;
  border-color: #153d2a;
  color: #fff;
}
</style>
