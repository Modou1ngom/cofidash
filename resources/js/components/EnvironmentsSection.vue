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
          <span class="icon">🔄</span>
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
              <div class="action-icons">
                <button 
                  class="action-icon" 
                  title="Document"
                  @click="handleAction(environment, 'document')"
                >
                  📄
                </button>
                <button 
                  class="action-icon" 
                  title="Paramètres"
                  @click="handleAction(environment, 'settings')"
                >
                  ⚙️
                </button>
                <button 
                  class="action-icon" 
                  title="Voir"
                  @click="handleAction(environment, 'view')"
                >
                  🔍
                </button>
                <button 
                  class="action-icon" 
                  title="Historique"
                  @click="handleAction(environment, 'history')"
                >
                  🕐
                </button>
                <button 
                  class="action-icon" 
                  title="Package"
                  @click="handleAction(environment, 'package')"
                >
                  📦
                </button>
                <button 
                  class="action-icon" 
                  title="Modifier"
                  @click="handleAction(environment, 'edit')"
                >
                  ✏️
                </button>
                <button 
                  class="action-icon delete" 
                  title="Supprimer"
                  @click="handleAction(environment, 'delete')"
                >
                  🗑️
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
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EnvironmentsSection',
  data() {
    return {
      searchQuery: '',
      environments: [
        { id: 1, name: 'SENEGAL(MAR)[FLEX]' },
        { id: 2, name: 'FINELLE[FLEX]' },
        { id: 3, name: 'SENEGAL[NAFA]' },
        { id: 4, name: 'TOGO[REPORT]' },
        { id: 5, name: 'TOGO' },
        { id: 6, name: 'SENEGAL[FLEX]' },
        { id: 7, name: "COTE D'IVOIRE" },
        { id: 8, name: 'BURKINA' },
        { id: 9, name: 'MALI[FLEX]' },
        { id: 10, name: 'NIGER[REPORT]' },
        { id: 11, name: 'BENIN' },
        { id: 12, name: 'GUINEE' },
        { id: 13, name: 'CAMEROUN[FLEX]' },
        { id: 14, name: 'GABON' },
        { id: 15, name: 'CONGO' },
        { id: 16, name: 'TCHAD' }
      ],
      currentPage: 1,
      itemsPerPage: 8
    }
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
    handleNew() {
      // TODO: Implémenter la création d'un nouvel environnement
      console.log('Créer un nouvel environnement');
      alert('Fonctionnalité de création d\'environnement à implémenter');
    },
    async handleRefresh() {
      // TODO: Implémenter le rafraîchissement depuis l'API
      try {
        // const response = await axios.get('/api/environments');
        // this.environments = response.data;
        console.log('Actualisation des environnements');
        // Pour l'instant, on simule juste un rafraîchissement
        alert('Environnements actualisés');
      } catch (error) {
        console.error('Erreur lors de l\'actualisation:', error);
        alert('Erreur lors de l\'actualisation des environnements');
      }
    },
    handleAction(environment, action) {
      console.log(`Action ${action} sur l'environnement:`, environment);
      switch (action) {
        case 'document':
          alert(`Ouvrir le document pour ${environment.name}`);
          break;
        case 'settings':
          alert(`Ouvrir les paramètres pour ${environment.name}`);
          break;
        case 'view':
          alert(`Voir les détails de ${environment.name}`);
          break;
        case 'history':
          alert(`Voir l'historique de ${environment.name}`);
          break;
        case 'package':
          alert(`Gérer le package pour ${environment.name}`);
          break;
        case 'edit':
          alert(`Modifier ${environment.name}`);
          break;
        case 'delete':
          if (confirm(`Êtes-vous sûr de vouloir supprimer ${environment.name} ?`)) {
            this.deleteEnvironment(environment.id);
          }
          break;
        default:
          console.log('Action non reconnue:', action);
      }
    },
    deleteEnvironment(id) {
      // TODO: Implémenter la suppression via l'API
      this.environments = this.environments.filter(env => env.id !== id);
      console.log('Environnement supprimé:', id);
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
  padding: 20px;
  background: #ffffff;
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
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #9333ea;
  color: white;
}

.btn-new:hover,
.btn-refresh:hover {
  background: #7e22ce;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(147, 51, 234, 0.3);
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

.action-icons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px 6px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon:hover {
  background: #f3f4f6;
  transform: scale(1.1);
}

.action-icon.delete:hover {
  background: #fee2e2;
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
  background: #9333ea;
  color: white;
  border-color: #9333ea;
  font-weight: 600;
}

.pagination-btn.page-number.active:hover {
  background: #7e22ce;
}
</style>
