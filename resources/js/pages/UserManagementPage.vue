<template>
  <div class="user-management page-adapt">
    <div class="page-header">
      <h1>Gestion des Utilisateurs</h1>
      <button @click="showCreateModal = true" class="btn-primary">
        + Créer un utilisateur
      </button>
    </div>

    <div class="users-table">
      <table>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Email</th>
            <th>Profil</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span class="profile-badge" v-if="user.profile">
                {{ user.profile.name }}
              </span>
              <span v-else class="no-profile">Aucun profil</span>
            </td>
            <td>
              <button @click="editUser(user)" class="btn-edit">Modifier</button>
              <button @click="deleteUser(user)" class="btn-delete">Supprimer</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de création/édition -->
    <div v-if="showCreateModal || editingUser" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ editingUser ? 'Modifier l\'utilisateur' : 'Créer un utilisateur' }}</h2>
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label>Nom *</label>
            <input v-model="form.name" required placeholder="Nom complet" />
          </div>
          <div class="form-group">
            <label>Email *</label>
            <input v-model="form.email" type="email" required placeholder="email@cofina.sn" />
          </div>
          <div class="form-group">
            <label>Mot de passe {{ editingUser ? '(laisser vide pour ne pas changer)' : '*' }}</label>
            <input 
              v-model="form.password" 
              type="password" 
              :required="!editingUser"
              placeholder="••••••••" 
            />
          </div>
          <div class="form-group">
            <label>Profil *</label>
            <select v-model="form.profile_id" required>
              <option value="">Sélectionnez un profil</option>
              <option
                v-for="profile in profiles"
                :key="profile.id"
                :value="profile.id"
              >
                {{ profile.name }} - {{ profile.description }}
              </option>
            </select>
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

export default {
  name: 'UserManagementPage',
  data() {
    return {
      users: [],
      profiles: [],
      showCreateModal: false,
      editingUser: null,
      form: {
        name: '',
        email: '',
        password: '',
        profile_id: ''
      }
    }
  },
  async mounted() {
    await Promise.all([
      this.loadUsers(),
      this.loadProfiles()
    ]);
  },
  methods: {
    async loadUsers() {
      try {
        const response = await axios.get('/api/admin/users');
        this.users = response.data;
      } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du chargement des utilisateurs');
      }
    },
    async loadProfiles() {
      try {
        const response = await axios.get('/api/profiles');
        this.profiles = response.data.filter(p => p.is_active);
      } catch (error) {
        console.error('Erreur:', error);
      }
    },
    editUser(user) {
      this.editingUser = user;
      this.form = {
        name: user.name,
        email: user.email,
        password: '',
        profile_id: user.profile_id
      };
    },
    async saveUser() {
      try {
        const formData = { ...this.form };
        if (this.editingUser && !formData.password) {
          delete formData.password;
        }

        if (this.editingUser) {
          await axios.put(`/api/admin/users/${this.editingUser.id}`, formData);
        } else {
          await axios.post('/api/admin/users', formData);
        }
        await this.loadUsers();
        this.closeModal();
      } catch (error) {
        alert(error.response?.data?.message || 'Erreur lors de la sauvegarde');
      }
    },
    async deleteUser(user) {
      if (!confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${user.name}" ?`)) {
        return;
      }
      try {
        await axios.delete(`/api/admin/users/${user.id}`);
        await this.loadUsers();
      } catch (error) {
        alert(error.response?.data?.message || 'Erreur lors de la suppression');
      }
    },
    closeModal() {
      this.showCreateModal = false;
      this.editingUser = null;
      this.form = {
        name: '',
        email: '',
        password: '',
        profile_id: ''
      };
    }
  }
}
</script>

<style scoped>
.user-management {
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

.users-table {
  background: white;
  border: 1px solid #DDD;
  border-radius: 8px;
  overflow-x: auto;
  overflow-y: visible;
}

.users-table table {
  width: 100%;
  min-width: 600px;
  border-collapse: collapse;
}

.users-table th {
  background: #F5F5F5;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #DDD;
}

.users-table td {
  padding: 12px;
  border-bottom: 1px solid #EEE;
}

.users-table tbody tr:hover {
  background: #F9F9F9;
}

.profile-badge {
  background: #D1FAE5;
  color: #065F46;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.no-profile {
  color: #999;
  font-style: italic;
}

.btn-edit, .btn-delete {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-right: 8px;
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
  padding: 24px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  margin: 16px;
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
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #DDD;
  border-radius: 4px;
  box-sizing: border-box;
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
  .user-management {
    padding: 16px;
  }

  .page-header h1 {
    font-size: 22px;
  }

  .users-table table {
    min-width: 500px;
  }
}

@media (max-width: 480px) {
  .user-management {
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

