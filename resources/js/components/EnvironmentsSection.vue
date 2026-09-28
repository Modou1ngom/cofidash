<template>
  <div class="environments-section">
    <div class="section-header">
      <h2 class="section-title">Environnements</h2>
    </div>
    
    <!-- Barre de recherche et boutons d'action -->
    <div class="search-and-actions">
      <div class="search-container">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Rechercher un environement" 
          class="search-input"
          @input="handleSearch"
        />
      </div>
      <div class="action-buttons">
        <button class="btn-new" @click="handleNew">
          <span class="icon">+</span>
          Nouveau
        </button>
        <button class="btn-refresh" @click="handleRefresh">
          Actualiser
        </button>
      </div>
    </div>

    <!-- Tableau des environnements -->
    <div class="table-container">
      <table class="environments-table">
        <thead>
          <tr>
            <th class="col-name">NOM</th>
            <th class="col-actions">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="environment in paginatedEnvironments" :key="environment.id">
            <td class="col-name">{{ environment.name }}</td>
            <td class="col-actions">
              <div class="action-buttons-row">
                <button 
                  class="action-btn btn-view" 
                  @click="handleAction(environment, 'view-agencies')"
                >
                  Voir les agences
                </button>
                <button 
                  class="action-btn btn-edit" 
                  @click="handleAction(environment, 'edit')"
                >
                  Modifier
                </button>
                <button 
                  class="action-btn btn-delete" 
                  @click="handleAction(environment, 'delete')"
                >
                  Supprimer
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="filteredEnvironments.length === 0">
            <td colspan="2" class="no-data">
              Aucun environnement trouvé
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <div class="pagination-info">
        Entrée {{ startEntry }} à {{ endEntry }} sur {{ totalEntries }} Entrées
      </div>
      <div class="pagination-controls">
        <button 
          class="pagination-btn" 
          @click="previousPage"
          :disabled="currentPage === 1"
        >
          ← Précedent
        </button>
        <button 
          v-for="page in totalPages" 
          :key="page"
          class="pagination-btn page-number"
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        <button 
          class="pagination-btn" 
          @click="nextPage"
          :disabled="currentPage === totalPages"
        >
          Suivant →
        </button>
      </div>
    </div>

    <p v-if="notice" class="env-notice" :class="{ error: noticeError }" role="status">{{ notice }}</p>

    <div v-if="showForm" class="env-overlay" @click.self="closeForm">
      <div class="env-modal" role="dialog" aria-modal="true">
        <h3>{{ editing ? 'Modifier l’environnement' : 'Nouvel environnement' }}</h3>
        <form @submit.prevent="saveEnvironment">
          <label for="env-name">Nom</label>
          <input id="env-name" v-model="formName" type="text" required maxlength="120" placeholder="SENEGAL" />
          <p v-if="formError" class="form-error">{{ formError }}</p>
          <div class="env-modal-actions">
            <button type="button" class="btn-refresh" @click="closeForm">Annuler</button>
            <button type="submit" class="btn-new" :disabled="saving">{{ saving ? 'Enregistrement…' : 'Enregistrer' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="agenciesEnv" class="env-overlay" @click.self="agenciesEnv = null">
      <div class="env-modal env-modal--wide" role="dialog" aria-modal="true">
        <h3>Agences — {{ agenciesEnv.name }}</h3>
        <p v-if="agenciesLoading" class="env-muted">Chargement…</p>
        <p v-else-if="agenciesError" class="form-error">{{ agenciesError }}</p>
        <p v-else-if="!agencies.length" class="env-muted">Aucune agence rattachée à cet environnement.</p>
        <ul v-else class="agency-list">
          <li v-for="agency in agencies" :key="agency.id">
            <code>{{ agency.code }}</code>
            <span>{{ agency.name }}</span>
            <em v-if="agency.territory">{{ agency.territory.name }}</em>
          </li>
        </ul>
        <div class="env-modal-actions">
          <button type="button" class="btn-new" @click="agenciesEnv = null">Fermer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EnvironmentsSection',
  data() {
    return {
      searchQuery: '',
      environments: [],
      currentPage: 1,
      itemsPerPage: 8,
      notice: '',
      noticeError: false,
      showForm: false,
      editing: null,
      formName: '',
      formError: '',
      saving: false,
      agenciesEnv: null,
      agencies: [],
      agenciesLoading: false,
      agenciesError: '',
    }
  },
  mounted() {
    this.loadEnvironments();
  },
  computed: {
    filteredEnvironments() {
      if (!this.searchQuery.trim()) {
        return this.environments;
      }
      const query = this.searchQuery.toLowerCase();
      return this.environments.filter(env => 
        env.name.toLowerCase().includes(query)
      );
    },
    totalEntries() {
      return this.filteredEnvironments.length;
    },
    totalPages() {
      return Math.ceil(this.totalEntries / this.itemsPerPage);
    },
    startEntry() {
      return this.totalEntries === 0 ? 0 : (this.currentPage - 1) * this.itemsPerPage + 1;
    },
    endEntry() {
      const end = this.currentPage * this.itemsPerPage;
      return end > this.totalEntries ? this.totalEntries : end;
    },
    paginatedEnvironments() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.filteredEnvironments.slice(start, end);
    }
  },
  methods: {
    handleSearch() {
      // Réinitialiser à la première page lors de la recherche
      this.currentPage = 1;
    },
    async loadEnvironments() {
      this.notice = '';
      this.noticeError = false;
      try {
        const response = await axios.get('/api/environments');
        const payload = response.data?.data || response.data || [];
        this.environments = Array.isArray(payload) ? payload : [];
      } catch (error) {
        this.noticeError = true;
        this.notice = error.response?.data?.message || 'Impossible de charger les environnements.';
      }
    },
    handleNew() {
      this.editing = null;
      this.formName = '';
      this.formError = '';
      this.showForm = true;
    },
    handleRefresh() {
      this.loadEnvironments();
    },
    closeForm() {
      if (this.saving) return;
      this.showForm = false;
      this.editing = null;
      this.formError = '';
    },
    async saveEnvironment() {
      const name = this.formName.trim();
      if (!name) {
        this.formError = 'Le nom est obligatoire.';
        return;
      }
      this.saving = true;
      this.formError = '';
      try {
        if (this.editing) {
          await axios.put(`/api/environments/${this.editing.id}`, { name });
        } else {
          await axios.post('/api/environments', { name });
        }
        this.showForm = false;
        this.editing = null;
        await this.loadEnvironments();
      } catch (error) {
        const errors = error.response?.data?.errors;
        this.formError = errors?.name?.[0]
          || error.response?.data?.message
          || 'Enregistrement impossible.';
      } finally {
        this.saving = false;
      }
    },
    async handleAction(environment, action) {
      if (action === 'view-agencies') {
        this.agenciesEnv = environment;
        this.agencies = [];
        this.agenciesError = '';
        this.agenciesLoading = true;
        try {
          const response = await axios.get(`/api/environments/${environment.id}/agencies`);
          const payload = response.data?.data || response.data || [];
          this.agencies = Array.isArray(payload) ? payload : [];
        } catch (error) {
          this.agenciesError = error.response?.data?.message || 'Impossible de charger les agences.';
        } finally {
          this.agenciesLoading = false;
        }
        return;
      }
      if (action === 'edit') {
        this.editing = environment;
        this.formName = environment.name;
        this.formError = '';
        this.showForm = true;
        return;
      }
      if (action === 'delete') {
        if (!confirm(`Supprimer l’environnement ${environment.name} ?`)) return;
        try {
          await axios.delete(`/api/environments/${environment.id}`);
          await this.loadEnvironments();
        } catch (error) {
          this.noticeError = true;
          this.notice = error.response?.data?.message || 'Suppression impossible.';
        }
      }
    },
    previousPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    goToPage(page) {
      this.currentPage = page;
    }
  }
}
</script>

<style scoped>
.environments-section {
  width: 100%;
  padding: 0;
  background: transparent;
  color: #1c2430;
}

.section-header {
  margin-bottom: 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #1A4D3A;
  margin: 0;
}

.search-and-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.search-container {
  flex: 1;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-new,
.btn-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  background: #1a4d3a;
  color: white;
}

.btn-refresh {
  background: #fff;
  color: #1a4d3a;
  border-color: #c9d8d0;
}

.btn-new:hover {
  background: #163f30;
}

.btn-refresh:hover {
  background: #f0f6f3;
  border-color: #1a4d3a;
}

.btn-new:active,
.btn-refresh:active {
  transform: translateY(0);
}

.btn-new .icon,
.btn-refresh .icon {
  font-size: 16px;
  font-weight: bold;
}

.table-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.environments-table {
  width: 100%;
  border-collapse: collapse;
}

.environments-table thead {
  background: #f9fafb;
}

.environments-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.environments-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  color: #1f2937;
}

.environments-table tbody tr:hover {
  background: #f9fafb;
}

.environments-table tbody tr:last-child td {
  border-bottom: none;
}

.col-name {
  width: 60%;
}

.col-actions {
  width: 40%;
}

.action-buttons-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  color: #374151;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn.btn-view {
  color: #1A4D3A;
  border-color: #1A4D3A;
}

.action-btn.btn-view:hover {
  background: #1A4D3A;
  color: white;
}

.action-btn.btn-edit {
  color: #1a4d3a;
  border-color: #c9d8d0;
}

.action-btn.btn-edit:hover {
  background: #f0f6f3;
  border-color: #1a4d3a;
  color: #1a4d3a;
}

.action-btn.btn-delete {
  color: #dc2626;
  border-color: #dc2626;
}

.action-btn.btn-delete:hover {
  background: #dc2626;
  color: white;
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.pagination-info {
  font-size: 14px;
  color: #6b7280;
}

.pagination-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pagination-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: #374151;
}

.pagination-btn:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #1A4D3A;
  color: #1A4D3A;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn.page-number {
  min-width: 40px;
}

.pagination-btn.page-number.active {
  background: #1a4d3a;
  color: white;
  border-color: #1a4d3a;
  font-weight: 600;
}

.pagination-btn.page-number.active:hover {
  background: #163f30;
}

.env-notice {
  margin-top: 12px;
  color: #065f46;
  font-size: 13px;
}

.env-notice.error,
.form-error {
  color: #b91c1c;
  font-size: 13px;
}

.env-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.env-modal {
  width: min(440px, 100%);
  background: #fff;
  border-radius: 12px;
  padding: 22px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.16);
}

.env-modal--wide {
  width: min(640px, 100%);
}

.env-modal h3 {
  margin: 0 0 14px;
  font-size: 18px;
}

.env-modal label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 650;
}

.env-modal input {
  width: 100%;
  height: 38px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0 12px;
  box-sizing: border-box;
}

.env-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.env-muted {
  margin: 0;
  color: #64748b;
}

.agency-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 360px;
  overflow: auto;
  border: 1px solid #e6ece8;
  border-radius: 8px;
}

.agency-list li {
  display: grid;
  grid-template-columns: 88px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f3f5;
  font-size: 13px;
}

.agency-list li:last-child {
  border-bottom: none;
}

.agency-list code {
  color: #1a4d3a;
  background: #eef5f1;
  border-radius: 6px;
  padding: 2px 6px;
  font-size: 12px;
}

.agency-list em {
  font-style: normal;
  color: #64748b;
  font-size: 12px;
}
</style>
