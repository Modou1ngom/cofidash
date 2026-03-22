<template>
  <div class="profile-management page-adapt">
    <div class="page-header">
      <h1>Gestion des Profils</h1>
      <button @click="showCreateModal = true" class="btn-primary">
        + Créer un profil
      </button>
    </div>

    <div class="profiles-grid">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="profile-card"
      >
        <div class="profile-card-header">
          <h3>{{ profile.name }}</h3>
          <span class="profile-code">{{ profile.code }}</span>
        </div>
        <p class="profile-description">{{ profile.description }}</p>
        <div class="profile-status">
          <span :class="['status-badge', profile.is_active ? 'active' : 'inactive']">
            {{ profile.is_active ? 'Actif' : 'Inactif' }}
          </span>
        </div>
        <div class="profile-actions">
          <button @click="editProfile(profile)" class="btn-edit">Modifier</button>
          <button @click="deleteProfile(profile)" class="btn-delete">Supprimer</button>
        </div>
      </div>
    </div>

    <!-- Modal de création/édition -->
    <div v-if="showCreateModal || editingProfile" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ editingProfile ? 'Modifier le profil' : 'Créer un profil' }}</h2>
        <form @submit.prevent="saveProfile">
          <div class="form-group">
            <label>Code *</label>
            <input v-model="form.code" required placeholder="ADMIN" />
          </div>
          <div class="form-group">
            <label>Nom *</label>
            <input v-model="form.name" required placeholder="Administrateur" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="3" placeholder="Description du profil"></textarea>
          </div>
          <div class="form-group">
            <label>Permissions</label>
            <div class="permissions-list">
              <label v-for="perm in availablePermissions" :key="perm.value" class="permission-item">
                <input
                  type="checkbox"
                  :value="perm.value"
                  v-model="form.permissions"
                />
                <span>{{ perm.label }}</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.is_active" />
              Profil actif
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal" class="btn-cancel">Annuler</button>
            <button type="submit" class="btn-save">Enregistrer</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const AVAILABLE_PERMISSIONS = [
  { value: 'VIEW_DASHBOARD', label: 'Voir le tableau de bord' },
  { value: 'VIEW_CLIENT', label: 'Voir les clients' },
  { value: 'VIEW_ZONES', label: 'Voir les zones' },
  { value: 'VIEW_AGENCIES', label: 'Voir les agences' },
  { value: 'EDIT_OBJECTIVES', label: 'Éditer les objectifs' },
  { value: 'MODIFY_OBJECTIVES', label: 'Modifier les objectifs' },
  { value: 'MANAGE_FINANCIAL', label: 'Gérer les finances' },
  { value: 'VIEW_FINANCIAL', label: 'Voir les finances' },
  { value: 'ADMIN_ACCESS', label: 'Accès administrateur' },
  { value: 'MANAGE_USERS', label: 'Gérer les utilisateurs' },
  { value: 'MANAGE_SETTINGS', label: 'Gérer les paramètres' }
];

export default {
  name: 'ProfileManagementPage',
  data() {
    return {
      profiles: [],
      showCreateModal: false,
      editingProfile: null,
      form: {
        code: '',
        name: '',
        description: '',
        permissions: [],
        is_active: true
      },
      availablePermissions: AVAILABLE_PERMISSIONS
    }
  },
  async mounted() {
    await this.loadProfiles();
  },
  methods: {
    async loadProfiles() {
      try {
        const response = await axios.get('/api/admin/profiles');
        this.profiles = response.data;
      } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du chargement des profils');
      }
    },
    editProfile(profile) {
      this.editingProfile = profile;
      this.form = {
        code: profile.code,
        name: profile.name,
        description: profile.description || '',
        permissions: profile.permissions || [],
        is_active: profile.is_active
      };
    },
    async saveProfile() {
      try {
        if (this.editingProfile) {
          await axios.put(`/api/admin/profiles/${this.editingProfile.id}`, this.form);
        } else {
          await axios.post('/api/admin/profiles', this.form);
        }
        await this.loadProfiles();
        this.closeModal();
      } catch (error) {
        alert(error.response?.data?.message || 'Erreur lors de la sauvegarde');
      }
    },
    async deleteProfile(profile) {
      if (!confirm(`Êtes-vous sûr de vouloir supprimer le profil "${profile.name}" ?`)) {
        return;
      }
      try {
        await axios.delete(`/api/admin/profiles/${profile.id}`);
        await this.loadProfiles();
      } catch (error) {
        alert(error.response?.data?.message || 'Erreur lors de la suppression');
      }
    },
    closeModal() {
      this.showCreateModal = false;
      this.editingProfile = null;
      this.form = {
        code: '',
        name: '',
        description: '',
        permissions: [],
        is_active: true
      };
    }
  }
}
</script>

<style scoped>
.profile-management {
  width: 100%;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  color: #333;
}

.btn-primary {
  padding: 12px 24px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.profile-card {
  background: white;
  border: 1px solid #DDD;
  border-radius: 8px;
  padding: 20px;
}

.profile-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.profile-card-header h3 {
  margin: 0;
  color: #333;
}

.profile-code {
  font-size: 12px;
  color: #666;
  background: #F5F5F5;
  padding: 4px 8px;
  border-radius: 4px;
}

.profile-description {
  color: #666;
  margin-bottom: 12px;
  min-height: 40px;
}

.profile-status {
  margin-bottom: 16px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #D1FAE5;
  color: #065F46;
}

.status-badge.inactive {
  background: #FEE2E2;
  color: #991B1B;
}

.profile-actions {
  display: flex;
  gap: 8px;
}

.btn-edit, .btn-delete {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-edit {
  background: #3B82F6;
  color: white;
}

.btn-delete {
  background: #EF4444;
  color: white;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  padding: 30px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h2 {
  margin-top: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #DDD;
  border-radius: 4px;
}

.permissions-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #DDD;
  border-radius: 4px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-cancel, .btn-save {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel {
  background: #F3F4F6;
  color: #333;
}

.btn-save {
  background: #1A4D3A;
  color: white;
}

@media (max-width: 768px) {
  .profile-management {
    padding: 16px;
  }

  .page-header h1 {
    font-size: 22px;
  }

  .profiles-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .permissions-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .profile-management {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header h1 {
    font-size: 20px;
  }
}
</style>

