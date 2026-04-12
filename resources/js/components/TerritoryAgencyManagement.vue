<template>
  <div class="territory-agency-management">
    <div class="management-header">
      <h2>Gestion des Territoires, Agences, Utilisateurs et Profils</h2>
      <div class="header-actions">
        <button @click="syncAgencies" :disabled="syncing" class="btn-sync">
          {{ syncing ? '⏳ Synchronisation...' : '🔄 Synchroniser les agences depuis Oracle' }}
        </button>
      </div>
    </div>

    <div v-if="syncMessage" class="sync-message" :class="syncMessageType">
      {{ syncMessage }}
    </div>

    <div class="management-tabs">
      <button 
        @click="activeTab = 'territories'" 
        :class="['tab-button', { active: activeTab === 'territories' }]"
      >
        📍 Territoires ({{ territories.length }})
      </button>
      <button 
        @click="activeTab = 'agencies'" 
        :class="['tab-button', { active: activeTab === 'agencies' }]"
      >
        🏢 Agences ({{ agencies.length }})
      </button>
      <button 
        @click="activeTab = 'users'" 
        :class="['tab-button', { active: activeTab === 'users' }]"
      >
        👥 Utilisateurs ({{ users.length }})
      </button>
      <button 
        @click="activeTab = 'profiles'" 
        :class="['tab-button', { active: activeTab === 'profiles' }]"
      >
        🔐 Profils ({{ profiles.length }})
      </button>
    </div>

    <!-- Tab Territoires -->
    <div v-if="activeTab === 'territories'" class="tab-content">
      <div class="table-container">
        <table class="management-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Description</th>
              <th>Responsable de Zone</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="territory in territories" :key="territory.id">
              <td><strong>{{ territory.code || '—' }}</strong></td>
              <td>{{ territory.name || '—' }}</td>
              <td>{{ territory.description || '-' }}</td>
              <td>
                <span v-if="territory.responsible" class="assigned-user">
                  👤 {{ territory.responsible.name }} ({{ territory.responsible.email }})
                </span>
                <span v-else class="no-assignment">❌ Non assigné</span>
              </td>
              <td>
                <button 
                  @click="openAssignResponsibleModal(territory)" 
                  class="btn-assign"
                >
                  {{ territory.responsible ? '✏️ Modifier' : '➕ Assigner' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab Agences -->
    <div v-if="activeTab === 'agencies'" class="tab-content">
      <div v-if="agencies.length === 0" class="empty-state-banner">
        <p><strong>Aucune agence en base.</strong> Les utilisateurs ne pourront pas être rattachés à une agence tant que la liste n’est pas remplie.</p>
        <p>Utilisez <strong>Synchroniser les agences depuis Oracle</strong> : les codes affichés viennent de la table <code>DASH_RELATION</code> (<code>CODE_BUREAU</code>). Pour retirer d’anciennes lignes, <code>php artisan agencies:sync-from-oracle --prune</code>.</p>
      </div>
      <div class="table-container">
        <table class="management-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Territoire</th>
              <th>Chef d'Agence</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="agencies.length === 0">
              <td colspan="5" class="empty-table-cell">—</td>
            </tr>
            <tr v-for="agency in agencies" :key="agency.id">
              <td><strong>{{ agency.code }}</strong></td>
              <td>{{ agency.name }}</td>
              <td>
                <span v-if="agency.territory" class="territory-badge">
                  {{ agency.territory.name }}
                </span>
                <span v-else class="no-territory">-</span>
              </td>
              <td>
                <span v-if="agency.chefAgence || agency.chef_agence" class="assigned-user">
                  👤 {{ (agency.chefAgence || agency.chef_agence)?.name }} ({{ (agency.chefAgence || agency.chef_agence)?.email }})
                </span>
                <span v-else class="no-assignment">❌ Non assigné</span>
              </td>
              <td>
                <button 
                  @click="openAssignChefAgenceModal(agency)" 
                  class="btn-assign"
                >
                  {{ (agency.chefAgence || agency.chef_agence) ? '✏️ Modifier' : '➕ Assigner' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab Utilisateurs -->
    <div v-if="activeTab === 'users'" class="tab-content">
      <div class="table-header">
        <button @click="openCreateUserModal" class="btn-create">
          ➕ Créer un utilisateur
        </button>
      </div>
      <div class="table-container">
        <table class="management-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Email</th>
              <th>Profil</th>
              <th>Territoire</th>
              <th>Agence</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="users.length === 0">
              <td colspan="6" style="text-align: center; padding: 20px; color: #999;">
                Aucun utilisateur trouvé
              </td>
            </tr>
            <tr v-for="user in users" :key="user.id">
              <td><strong>{{ user.name }}</strong></td>
              <td>{{ user.email }}</td>
              <td>
                <span class="profile-badge" :class="'profile-' + (user.profile?.code || '').toLowerCase()">
                  {{ user.profile?.name || '-' }}
                </span>
              </td>
              <td>
                <span v-if="user.territory" class="territory-badge">
                  {{ user.territory.name }}
                </span>
                <span v-else class="no-assignment">-</span>
              </td>
              <td>
                <span v-if="user.agency" class="agency-badge">
                  {{ user.agency.name }}
                </span>
                <span v-else class="no-assignment">-</span>
              </td>
              <td>
                <button @click="openEditUserModal(user)" class="btn-edit">✏️ Modifier</button>
                <button @click="confirmDeleteUser(user)" class="btn-delete">🗑️ Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Créer/Modifier Utilisateur -->
    <div v-if="showUserModal" class="modal-overlay" @click="closeUserModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editingUser ? 'Modifier l\'utilisateur' : 'Créer un utilisateur' }}</h3>
          <button @click="closeUserModal" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="user-name">Nom *</label>
            <input 
              id="user-name" 
              v-model="userForm.name" 
              type="text" 
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <label for="user-email">Email *</label>
            <input 
              id="user-email" 
              v-model="userForm.email" 
              type="email" 
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <label for="user-password">Mot de passe {{ editingUser ? '(laisser vide pour ne pas changer)' : '*' }}</label>
            <input 
              id="user-password" 
              v-model="userForm.password" 
              type="password" 
              class="form-input"
              :required="!editingUser"
            />
          </div>
          <div class="form-group">
            <label for="user-profile">Profil *</label>
            <select 
              id="user-profile" 
              v-model="userForm.profile_id" 
              class="form-select"
              required
            >
              <option value="">Sélectionner un profil...</option>
              <option 
                v-for="profile in profiles" 
                :key="profile.id" 
                :value="profile.id"
              >
                {{ profile.name }} ({{ profile.code }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="user-territory">Territoire</label>
            <select 
              id="user-territory" 
              v-model="userForm.territory_id" 
              class="form-select"
            >
              <option value="">Aucun territoire</option>
              <option 
                v-for="territory in territories" 
                :key="territory.id" 
                :value="territory.id"
              >
                {{ territory.name }} ({{ territory.code }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="user-agency">Agence</label>
            <select 
              id="user-agency" 
              v-model="userForm.agency_id" 
              class="form-select"
            >
              <option value="">Aucune agence</option>
              <option 
                v-for="agency in agencies" 
                :key="agency.id" 
                :value="agency.id"
              >
                {{ agency.name }} ({{ agency.code }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeUserModal" class="btn-cancel">Annuler</button>
          <button @click="saveUser" :disabled="savingUser" class="btn-save">
            {{ savingUser ? '⏳ Enregistrement...' : '💾 Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Tab Profils -->
    <div v-if="activeTab === 'profiles'" class="tab-content">
      <div class="table-header">
        <button @click="openCreateProfileModal" class="btn-create">
          ➕ Créer un profil
        </button>
      </div>
      <div class="table-container">
        <table class="management-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Nom</th>
              <th>Description</th>
              <th>Permissions</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="profiles.length === 0">
              <td colspan="6" style="text-align: center; padding: 20px; color: #999;">
                Aucun profil trouvé
              </td>
            </tr>
            <tr v-for="profile in profiles" :key="profile.id">
              <td><strong>{{ profile.code }}</strong></td>
              <td>{{ profile.name }}</td>
              <td>{{ profile.description || '-' }}</td>
              <td>
                <span v-if="profile.permissions && profile.permissions.length > 0" class="permissions-badge">
                  {{ profile.permissions.length }} permission(s)
                </span>
                <span v-else class="no-assignment">Aucune</span>
              </td>
              <td>
                <span :class="profile.is_active ? 'status-active' : 'status-inactive'">
                  {{ profile.is_active ? '✅ Actif' : '❌ Inactif' }}
                </span>
              </td>
              <td>
                <button @click="openEditProfileModal(profile)" class="btn-edit">✏️ Modifier</button>
                <button @click="confirmDeleteProfile(profile)" class="btn-delete">🗑️ Supprimer</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Créer/Modifier Profil -->
    <div v-if="showProfileModal" class="modal-overlay" @click="closeProfileModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editingProfile ? 'Modifier le profil' : 'Créer un profil' }}</h3>
          <button @click="closeProfileModal" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="profile-code">Code *</label>
            <input 
              id="profile-code" 
              v-model="profileForm.code" 
              type="text" 
              class="form-input"
              :disabled="!!editingProfile"
              required
              placeholder="Ex: ADMIN, DGA, RESPONSABLE_ZONE"
            />
            <small style="color: #666; font-size: 12px;">Le code doit être unique et en majuscules</small>
          </div>
          <div class="form-group">
            <label for="profile-name">Nom *</label>
            <input 
              id="profile-name" 
              v-model="profileForm.name" 
              type="text" 
              class="form-input"
              required
              placeholder="Ex: Administrateur, Directeur Général"
            />
          </div>
          <div class="form-group">
            <label for="profile-description">Description</label>
            <textarea 
              id="profile-description" 
              v-model="profileForm.description" 
              class="form-input"
              rows="3"
              placeholder="Description du profil..."
            ></textarea>
          </div>
          <div class="form-group">
            <label>Permissions</label>
            <div class="permissions-list">
              <label 
                v-for="permission in availablePermissions" 
                :key="permission"
                class="permission-checkbox"
              >
                <input 
                  type="checkbox" 
                  :value="permission"
                  :checked="profileForm.permissions.includes(permission)"
                  @change="togglePermission(permission)"
                />
                <span>{{ permission }}</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="profileForm.is_active"
              />
              <span>Profil actif</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeProfileModal" class="btn-cancel">Annuler</button>
          <button @click="saveProfile" :disabled="savingProfile" class="btn-save">
            {{ savingProfile ? '⏳ Enregistrement...' : '💾 Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Assigner Responsable -->
    <div v-if="showAssignResponsibleModal" class="modal-overlay" @click="closeModals">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Assigner un Responsable de Zone</h3>
          <button @click="closeModals" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Territoire:</label>
            <div class="territory-info">
              <strong>{{ selectedTerritory?.code }}</strong> - {{ selectedTerritory?.name }}
            </div>
          </div>
          <div class="form-group">
            <label for="responsible-select">Responsable de Zone *</label>
            <select 
              id="responsible-select" 
              v-model="selectedResponsibleId" 
              class="form-select"
            >
              <option value="">Sélectionner un responsable...</option>
              <option 
                v-for="user in responsablesZone" 
                :key="user.id" 
                :value="user.id"
              >
                {{ user.name }} ({{ user.email }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeModals" class="btn-cancel">Annuler</button>
          <button @click="assignResponsible" :disabled="!selectedResponsibleId || assigning" class="btn-save">
            {{ assigning ? '⏳ Enregistrement...' : '💾 Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Assigner Chef d'Agence -->
    <div v-if="showAssignChefAgenceModal" class="modal-overlay" @click="closeModals">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Assigner un Chef d'Agence</h3>
          <button @click="closeModals" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Agence:</label>
            <div class="agency-info">
              <strong>{{ selectedAgency?.code }}</strong> - {{ selectedAgency?.name }}
            </div>
          </div>
          <div class="form-group">
            <label for="chef-agence-select">Chef d'Agence *</label>
            <select 
              id="chef-agence-select" 
              v-model="selectedChefAgenceId" 
              class="form-select"
            >
              <option value="">Sélectionner un chef d'agence...</option>
              <option 
                v-for="user in chefsAgence" 
                :key="user.id" 
                :value="user.id"
              >
                {{ user.name }} ({{ user.email }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeModals" class="btn-cancel">Annuler</button>
          <button @click="assignChefAgence" :disabled="!selectedChefAgenceId || assigning" class="btn-save">
            {{ assigning ? '⏳ Enregistrement...' : '💾 Enregistrer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'TerritoryAgencyManagement',
  data() {
    return {
      activeTab: 'territories',
      territories: [],
      agencies: [],
      responsablesZone: [],
      chefsAgence: [],
      loading: false,
      syncing: false,
      syncMessage: '',
      syncMessageType: 'success',
      showAssignResponsibleModal: false,
      showAssignChefAgenceModal: false,
      selectedTerritory: null,
      selectedAgency: null,
      selectedResponsibleId: '',
      selectedChefAgenceId: '',
      assigning: false,
      users: [],
      profiles: [],
      showUserModal: false,
      editingUser: null,
      userForm: {
        name: '',
        email: '',
        password: '',
        profile_id: '',
        territory_id: '',
        agency_id: ''
      },
      savingUser: false,
      showProfileModal: false,
      editingProfile: null,
      profileForm: {
        code: '',
        name: '',
        description: '',
        permissions: [],
        is_active: true
      },
      savingProfile: false,
      availablePermissions: []
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    /** Réponse JSON tableau brute ou pagination Laravel { data: [...] } */
    normalizeListResponse(raw) {
      if (Array.isArray(raw)) {
        return raw;
      }
      if (raw && Array.isArray(raw.data)) {
        return raw.data;
      }
      return [];
    },
    async loadData() {
      this.loading = true;
      try {
        await Promise.all([
          this.loadTerritories(),
          this.loadAgencies(),
          this.loadResponsablesZone(),
          this.loadChefsAgence(),
          this.loadUsers(),
          this.loadProfiles(),
          this.loadAvailablePermissions()
        ]);
      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
      } finally {
        this.loading = false;
      }
    },
    async loadTerritories() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/territories', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.territories = this.normalizeListResponse(response.data);
      } catch (error) {
        console.error('Erreur lors du chargement des territoires:', error);
      }
    },
    async loadAgencies() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/agencies', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.agencies = this.normalizeListResponse(response.data);
      } catch (error) {
        console.error('Erreur lors du chargement des agences:', error);
      }
    },
    async loadResponsablesZone() {
      try {
        const token = localStorage.getItem('token');
        // Charger tous les utilisateurs, pas seulement ceux avec le profil RESPONSABLE_ZONE
        const response = await axios.get('/api/users', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.responsablesZone = this.normalizeListResponse(response.data);
        console.log('Responsables de zone chargés:', this.responsablesZone.length);
      } catch (error) {
        console.error('Erreur lors du chargement des responsables de zone:', error);
        this.responsablesZone = [];
      }
    },
    async loadChefsAgence() {
      try {
        const token = localStorage.getItem('token');
        // Charger tous les utilisateurs, pas seulement ceux avec le profil CHEF_AGENCE
        const response = await axios.get('/api/users', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.chefsAgence = this.normalizeListResponse(response.data);
        console.log('Chefs d\'agence chargés:', this.chefsAgence.length);
      } catch (error) {
        console.error('Erreur lors du chargement des chefs d\'agence:', error);
        this.chefsAgence = [];
      }
    },
    async syncAgencies() {
      this.syncing = true;
      this.syncMessage = '';
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post('/api/agencies/sync-from-oracle', {}, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.data.success) {
          this.syncMessage = '✅ ' + response.data.message;
          this.syncMessageType = 'success';
          await Promise.all([this.loadAgencies(), this.loadTerritories()]);
        } else {
          this.syncMessage = '❌ ' + (response.data.message || 'Erreur lors de la synchronisation');
          this.syncMessageType = 'error';
        }
      } catch (error) {
        this.syncMessage = '❌ Erreur: ' + (error.response?.data?.message || error.message);
        this.syncMessageType = 'error';
        console.error('Erreur lors de la synchronisation:', error);
      } finally {
        this.syncing = false;
        setTimeout(() => {
          this.syncMessage = '';
        }, 5000);
      }
    },
    openAssignResponsibleModal(territory) {
      this.selectedTerritory = territory;
      this.selectedResponsibleId = territory.responsible?.id || '';
      this.showAssignResponsibleModal = true;
    },
    openAssignChefAgenceModal(agency) {
      this.selectedAgency = agency;
      this.selectedChefAgenceId = (agency.chefAgence || agency.chef_agence)?.id || '';
      this.showAssignChefAgenceModal = true;
    },
    closeModals() {
      this.showAssignResponsibleModal = false;
      this.showAssignChefAgenceModal = false;
      this.selectedTerritory = null;
      this.selectedAgency = null;
      this.selectedResponsibleId = '';
      this.selectedChefAgenceId = '';
    },
    async assignResponsible() {
      if (!this.selectedResponsibleId || !this.selectedTerritory) return;
      
      this.assigning = true;
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post(
          `/api/territories/${this.selectedTerritory.id}/assign-responsible`,
          { user_id: this.selectedResponsibleId },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        if (response.data) {
          await this.loadTerritories();
          this.closeModals();
          const warning = response.headers['x-warning'];
          if (warning) {
            alert('⚠️ ' + warning + '\n\n✅ Responsable assigné avec succès!');
          } else {
            alert('✅ Responsable assigné avec succès!');
          }
        }
      } catch (error) {
        alert('❌ Erreur: ' + (error.response?.data?.message || error.message));
        console.error('Erreur lors de l\'assignation:', error);
      } finally {
        this.assigning = false;
      }
    },
    async assignChefAgence() {
      if (!this.selectedChefAgenceId || !this.selectedAgency) return;
      
      this.assigning = true;
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post(
          `/api/agencies/${this.selectedAgency.id}/assign-chef-agence`,
          { user_id: this.selectedChefAgenceId },
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        if (response.data) {
          await this.loadAgencies();
          this.closeModals();
          const warning = response.headers['x-warning'];
          if (warning) {
            alert('⚠️ ' + warning + '\n\n✅ Chef d\'agence assigné avec succès!');
          } else {
            alert('✅ Chef d\'agence assigné avec succès!');
          }
        }
      } catch (error) {
        alert('❌ Erreur: ' + (error.response?.data?.message || error.message));
        console.error('Erreur lors de l\'assignation:', error);
      } finally {
        this.assigning = false;
      }
    },
    async loadUsers() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/users', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.users = this.normalizeListResponse(response.data);
        console.log('Nombre d\'utilisateurs:', this.users.length);
      } catch (error) {
        console.error('Erreur lors du chargement des utilisateurs:', error);
        console.error('Détails de l\'erreur:', error.response?.data);
        this.users = [];
      }
    },
    async loadProfiles() {
      try {
        const token = localStorage.getItem('token');
        // Charger depuis la route admin pour avoir tous les profils (actifs et inactifs)
        const response = await axios.get('/api/admin/profiles', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        this.profiles = this.normalizeListResponse(response.data);
        console.log('Profils chargés:', this.profiles.length);
      } catch (error) {
        console.error('Erreur lors du chargement des profils:', error);
        // En cas d'erreur, essayer la route publique
        try {
          const response = await axios.get('/api/profiles');
          this.profiles = this.normalizeListResponse(response.data);
        } catch (err) {
          console.error('Erreur lors du chargement des profils (route publique):', err);
          this.profiles = [];
        }
      }
    },
    openCreateUserModal() {
      this.editingUser = null;
      this.userForm = {
        name: '',
        email: '',
        password: '',
        profile_id: '',
        territory_id: '',
        agency_id: ''
      };
      this.showUserModal = true;
    },
    openEditUserModal(user) {
      this.editingUser = user;
      this.userForm = {
        name: user.name,
        email: user.email,
        password: '',
        profile_id: user.profile_id,
        territory_id: user.territory_id || '',
        agency_id: user.agency_id || ''
      };
      this.showUserModal = true;
    },
    closeUserModal() {
      this.showUserModal = false;
      this.editingUser = null;
      this.userForm = {
        name: '',
        email: '',
        password: '',
        profile_id: '',
        territory_id: '',
        agency_id: ''
      };
    },
    async saveUser() {
      if (!this.userForm.name || !this.userForm.email || !this.userForm.profile_id) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
      }

      if (!this.editingUser && !this.userForm.password) {
        alert('Veuillez saisir un mot de passe.');
        return;
      }

      this.savingUser = true;
      try {
        const token = localStorage.getItem('token');
        const payload = { ...this.userForm };
        
        // Si on modifie et qu'il n'y a pas de nouveau mot de passe, ne pas l'envoyer
        if (this.editingUser && !payload.password) {
          delete payload.password;
        }

        let response;
        if (this.editingUser) {
          response = await axios.put(
            `/api/admin/users/${this.editingUser.id}`,
            payload,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
        } else {
          response = await axios.post(
            '/api/admin/users',
            payload,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
        }

        if (response.data) {
          await this.loadUsers();
          this.closeUserModal();
          alert(this.editingUser ? '✅ Utilisateur modifié avec succès!' : '✅ Utilisateur créé avec succès!');
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message;
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur lors de la sauvegarde:', error);
      } finally {
        this.savingUser = false;
      }
    },
    confirmDeleteUser(user) {
      if (confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${user.name}" ?`)) {
        this.deleteUser(user);
      }
    },
    async deleteUser(user) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `/api/admin/users/${user.id}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        await this.loadUsers();
        alert('✅ Utilisateur supprimé avec succès!');
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message;
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur lors de la suppression:', error);
      }
    },
    async loadAvailablePermissions() {
      // Liste des permissions disponibles dans le système
      this.availablePermissions = [
        'view_dashboard',
        'edit_objectives',
        'validate_objectives',
        'manage_users',
        'manage_profiles',
        'manage_territories',
        'manage_agencies',
        'view_reports',
        'export_data'
      ];
    },
    openCreateProfileModal() {
      this.editingProfile = null;
      this.profileForm = {
        code: '',
        name: '',
        description: '',
        permissions: [],
        is_active: true
      };
      this.showProfileModal = true;
    },
    openEditProfileModal(profile) {
      this.editingProfile = profile;
      this.profileForm = {
        code: profile.code,
        name: profile.name,
        description: profile.description || '',
        permissions: Array.isArray(profile.permissions) ? [...profile.permissions] : [],
        is_active: profile.is_active !== undefined ? profile.is_active : true
      };
      this.showProfileModal = true;
    },
    closeProfileModal() {
      this.showProfileModal = false;
      this.editingProfile = null;
      this.profileForm = {
        code: '',
        name: '',
        description: '',
        permissions: [],
        is_active: true
      };
    },
    togglePermission(permission) {
      const index = this.profileForm.permissions.indexOf(permission);
      if (index > -1) {
        this.profileForm.permissions.splice(index, 1);
      } else {
        this.profileForm.permissions.push(permission);
      }
    },
    async saveProfile() {
      if (!this.profileForm.code || !this.profileForm.name) {
        alert('Veuillez remplir tous les champs obligatoires.');
        return;
      }

      this.savingProfile = true;
      try {
        const token = localStorage.getItem('token');
        let response;
        
        if (this.editingProfile) {
          response = await axios.put(
            `/api/admin/profiles/${this.editingProfile.id}`,
            this.profileForm,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
        } else {
          response = await axios.post(
            '/api/admin/profiles',
            this.profileForm,
            { headers: { 'Authorization': `Bearer ${token}` } }
          );
        }

        if (response.data) {
          await this.loadProfiles();
          this.closeProfileModal();
          alert(this.editingProfile ? '✅ Profil modifié avec succès!' : '✅ Profil créé avec succès!');
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message;
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur lors de la sauvegarde:', error);
      } finally {
        this.savingProfile = false;
      }
    },
    confirmDeleteProfile(profile) {
      if (confirm(`Êtes-vous sûr de vouloir supprimer le profil "${profile.name}" ?`)) {
        this.deleteProfile(profile);
      }
    },
    async deleteProfile(profile) {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.delete(
          `/api/admin/profiles/${profile.id}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        if (response.status === 200 || response.status === 204) {
          await this.loadProfiles();
          alert('✅ Profil supprimé avec succès!');
        }
      } catch (error) {
        const errorMsg = error.response?.data?.message || error.message;
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur lors de la suppression:', error);
      }
    }
  }
}
</script>

<style scoped>
.territory-agency-management {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.management-header h2 {
  margin: 0;
  color: #1A4D3A;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-sync {
  padding: 10px 20px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.btn-sync:hover:not(:disabled) {
  background: #2d6b4f;
}

.btn-sync:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.sync-message {
  padding: 12px 20px;
  margin-bottom: 20px;
  border-radius: 4px;
  font-weight: 500;
}

.sync-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.empty-state-banner {
  margin-bottom: 16px;
  padding: 14px 18px;
  background: #fff8e6;
  border: 1px solid #e6d9a3;
  border-radius: 8px;
  color: #4a3f1c;
  font-size: 14px;
  line-height: 1.5;
}

.empty-state-banner p {
  margin: 0 0 8px 0;
}

.empty-state-banner p:last-child {
  margin-bottom: 0;
}

.empty-state-banner code {
  font-size: 12px;
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}

.empty-table-cell {
  text-align: center;
  color: #999;
  padding: 24px !important;
}

.sync-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.management-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tab-button {
  padding: 12px 24px;
  background: white;
  border: 2px solid #ddd;
  border-radius: 4px 4px 0 0;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  transition: all 0.3s;
}

.tab-button:hover {
  background: #f0f0f0;
}

.tab-button.active {
  background: #1A4D3A;
  color: white;
  border-color: #1A4D3A;
}

.tab-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 20px;
}

.table-container {
  overflow-x: auto;
}

.management-table {
  width: 100%;
  border-collapse: collapse;
}

.management-table thead {
  background: #1A4D3A;
  color: white;
}

.management-table th {
  padding: 12px;
  text-align: left;
  font-weight: 600;
}

.management-table td {
  padding: 12px;
  border-bottom: 1px solid #ddd;
}

.management-table tbody tr:hover {
  background: #f9f9f9;
}

.assigned-user {
  color: #155724;
  font-weight: 500;
}

.no-assignment {
  color: #721c24;
  font-style: italic;
}

.territory-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.no-territory {
  color: #999;
  font-style: italic;
}

.btn-assign {
  padding: 6px 12px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s;
}

.btn-assign:hover {
  background: #2d6b4f;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ddd;
}

.modal-header h3 {
  margin: 0;
  color: #1A4D3A;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.territory-info,
.agency-info {
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 10px;
}

.form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #ddd;
}

.btn-cancel {
  padding: 10px 20px;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-save {
  padding: 10px 20px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-save:hover:not(:disabled) {
  background: #2d6b4f;
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.table-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

.btn-create {
  padding: 10px 20px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.btn-create:hover {
  background: #2d6b4f;
}

.btn-edit {
  padding: 6px 12px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 5px;
  transition: background 0.3s;
}

.btn-edit:hover {
  background: #2d6b4f;
}

.btn-delete {
  padding: 6px 12px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s;
}

.btn-delete:hover {
  background: #c82333;
}

.profile-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #e3f2fd;
  color: #1976d2;
}

.agency-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #f3e5f5;
  color: #7b1fa2;
}

.large-modal {
  max-width: 600px;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

textarea.form-input {
  resize: vertical;
  min-height: 80px;
}

.permissions-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: #e8f5e9;
  color: #2e7d32;
}

.status-active {
  color: #2e7d32;
  font-weight: 500;
}

.status-inactive {
  color: #c62828;
  font-weight: 500;
}

.permissions-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.permission-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.permission-checkbox:hover {
  background: #f0f0f0;
}

.permission-checkbox input[type="checkbox"] {
  cursor: pointer;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}
</style>
