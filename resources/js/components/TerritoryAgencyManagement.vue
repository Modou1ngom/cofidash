<template>
  <div class="tam">
    <header class="tam-page-header">
      <div>
        <h1>Gestion organisationnelle</h1>
        <p>Territoires, agences, utilisateurs et profils d’accès.</p>
      </div>
      <button type="button" class="btn btn-secondary" @click="syncAgencies" :disabled="syncing">
        <span v-if="syncing" class="spinner" aria-hidden="true"></span>
        <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
        {{ syncing ? 'Synchronisation…' : 'Synchroniser les agences' }}
      </button>
    </header>

    <div v-if="syncMessage" class="tam-alert" :class="syncMessageType" role="status">
      {{ syncMessage }}
    </div>

    <section class="tam-panel">
      <div class="tam-tabs" role="tablist">
        <button type="button" role="tab" class="tam-tab" :class="{ active: activeTab === 'territories' }" :aria-selected="activeTab === 'territories'" @click="setTab('territories')">
          Territoires <span class="count">{{ territories.length }}</span>
        </button>
        <button type="button" role="tab" class="tam-tab" :class="{ active: activeTab === 'agencies' }" :aria-selected="activeTab === 'agencies'" @click="setTab('agencies')">
          Agences <span class="count">{{ agencies.length }}</span>
        </button>
        <button type="button" role="tab" class="tam-tab" :class="{ active: activeTab === 'users' }" :aria-selected="activeTab === 'users'" @click="setTab('users')">
          Utilisateurs <span class="count">{{ users.length }}</span>
        </button>
        <button type="button" role="tab" class="tam-tab" :class="{ active: activeTab === 'profiles' }" :aria-selected="activeTab === 'profiles'" @click="setTab('profiles')">
          Profils <span class="count">{{ profiles.length }}</span>
        </button>
      </div>

      <div class="tam-toolbar">
        <div class="search-wrap">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5" stroke-linecap="round"/></svg>
          <input v-model="searchQuery" type="search" class="search-input" :placeholder="searchPlaceholder" />
        </div>
        <div class="toolbar-meta">
          <span class="result-count">{{ currentResultCount }} résultat{{ currentResultCount > 1 ? 's' : '' }}</span>
          <button v-if="activeTab === 'territories'" type="button" class="btn btn-primary" @click="openCreateTerritoryModal">Nouveau territoire</button>
          <button v-if="activeTab === 'agencies'" type="button" class="btn btn-primary" @click="openCreateAgencyModal">Nouvelle agence</button>
          <button v-if="activeTab === 'users'" type="button" class="btn btn-primary" @click="openCreateUserModal">Nouvel utilisateur</button>
          <button v-if="activeTab === 'profiles'" type="button" class="btn btn-primary" @click="openCreateProfileModal">Nouveau profil</button>
        </div>
      </div>

      <!-- Territoires -->
      <div v-if="activeTab === 'territories'" class="tam-body" role="tabpanel">
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Nom</th>
                <th>Description</th>
                <th>Responsable de zone</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredTerritories.length === 0">
                <td colspan="5" class="empty-cell">Aucun territoire trouvé</td>
              </tr>
              <tr v-for="territory in paginatedTerritories" :key="territory.id">
                <td><code class="mono">{{ territory.code || '—' }}</code></td>
                <td class="strong">{{ territory.name || '—' }}</td>
                <td class="muted">{{ territory.description || '—' }}</td>
                <td>
                  <div v-if="territory.responsible" class="person">
                    <span class="avatar">{{ initials(territory.responsible.name) }}</span>
                    <span>
                      <span class="person-name">{{ territory.responsible.name }}</span>
                      <span class="person-sub">{{ territory.responsible.email }}</span>
                    </span>
                  </div>
                  <span v-else class="tag tag-warn">Non assigné</span>
                </td>
                <td class="col-actions">
                  <button type="button" class="btn-link" @click="openEditTerritoryModal(territory)">Modifier</button>
                  <button type="button" class="btn-link" @click="openAssignResponsibleModal(territory)">
                    {{ territory.responsible ? 'Responsable' : 'Assigner' }}
                  </button>
                  <button type="button" class="btn-link danger" @click="confirmDeleteTerritory(territory)">Supprimer</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Agences -->
      <div v-else-if="activeTab === 'agencies'" class="tam-body" role="tabpanel">
        <div v-if="agencies.length === 0" class="info-banner">
          <strong>Aucune agence synchronisée.</strong>
          Utilisez « Synchroniser les agences » pour importer les codes depuis Flexcube (<code>STTM_BRANCH</code> / <code>BRANCH_CODE</code>).
          Pour purger les anciennes lignes : <code>php artisan agencies:sync-from-oracle --prune</code>.
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Nom</th>
                <th>Territoire</th>
                <th>Chef d’agence</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredAgencies.length === 0">
                <td colspan="5" class="empty-cell">Aucune agence à afficher</td>
              </tr>
              <tr v-for="agency in paginatedAgencies" :key="agency.id">
                <td><code class="mono">{{ agency.code }}</code></td>
                <td class="strong">{{ agency.name }}</td>
                <td>
                  <span v-if="agency.territory" class="tag tag-neutral">{{ agency.territory.name }}</span>
                  <span v-else class="muted">—</span>
                </td>
                <td>
                  <div v-if="agency.chefAgence || agency.chef_agence" class="person">
                    <span class="avatar">{{ initials((agency.chefAgence || agency.chef_agence)?.name) }}</span>
                    <span>
                      <span class="person-name">{{ (agency.chefAgence || agency.chef_agence)?.name }}</span>
                      <span class="person-sub">{{ (agency.chefAgence || agency.chef_agence)?.email }}</span>
                    </span>
                  </div>
                  <span v-else class="tag tag-warn">Non assigné</span>
                </td>
                <td class="col-actions">
                  <button type="button" class="btn-link" @click="openEditAgencyModal(agency)">Modifier</button>
                  <button type="button" class="btn-link" @click="openAssignChefAgenceModal(agency)">
                    {{ (agency.chefAgence || agency.chef_agence) ? 'Chef' : 'Assigner' }}
                  </button>
                  <button type="button" class="btn-link danger" @click="confirmDeleteAgency(agency)">Supprimer</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Utilisateurs -->
      <div v-else-if="activeTab === 'users'" class="tam-body" role="tabpanel">
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Profil</th>
                <th>Territoire</th>
                <th>Agence</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredUsers.length === 0">
                <td colspan="6" class="empty-cell">Aucun utilisateur trouvé</td>
              </tr>
              <tr v-for="user in paginatedUsers" :key="user.id">
                <td>
                  <div class="person">
                    <span class="avatar">{{ initials(user.name) }}</span>
                    <span class="person-name">{{ user.name }}</span>
                  </div>
                </td>
                <td class="muted">{{ user.email }}</td>
                <td><span class="tag tag-green">{{ user.profile?.name || '—' }}</span></td>
                <td>
                  <span v-if="user.territory" class="tag tag-neutral">{{ user.territory.name }}</span>
                  <span v-else class="muted">—</span>
                </td>
                <td>
                  <span v-if="user.agency" class="tag tag-neutral">{{ user.agency.name }}</span>
                  <span v-else class="muted">—</span>
                </td>
                <td class="col-actions">
                  <button type="button" class="btn-link" @click="openEditUserModal(user)">Modifier</button>
                  <button type="button" class="btn-link danger" @click="confirmDeleteUser(user)">Supprimer</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Profils -->
      <div v-else class="tam-body" role="tabpanel">
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Nom</th>
                <th>Description</th>
                <th>Permissions</th>
                <th>Statut</th>
                <th class="col-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="filteredProfiles.length === 0">
                <td colspan="6" class="empty-cell">Aucun profil trouvé</td>
              </tr>
              <tr v-for="profile in paginatedProfiles" :key="profile.id">
                <td><code class="mono">{{ profile.code }}</code></td>
                <td class="strong">{{ profile.name }}</td>
                <td class="muted">{{ profile.description || '—' }}</td>
                <td>
                  <span v-if="profile.permissions && profile.permissions.length" class="tag tag-neutral">
                    {{ profile.permissions.length }} permission{{ profile.permissions.length > 1 ? 's' : '' }}
                  </span>
                  <span v-else class="muted">Aucune</span>
                </td>
                <td>
                  <span class="status-dot" :class="profile.is_active ? 'on' : 'off'">
                    {{ profile.is_active ? 'Actif' : 'Inactif' }}
                  </span>
                </td>
                <td class="col-actions">
                  <button type="button" class="btn-link" @click="openEditProfileModal(profile)">Modifier</button>
                  <button type="button" class="btn-link danger" @click="confirmDeleteProfile(profile)">Supprimer</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="currentResultCount > 0" class="tam-pagination">
        <div class="pagination-info">
          {{ pageStart }}–{{ pageEnd }} sur {{ currentResultCount }}
        </div>
        <div class="pagination-size">
          <label for="page-size">Par page</label>
          <select id="page-size" v-model.number="pageSize" class="page-size-select">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
        <div class="pagination-controls">
          <button type="button" class="pagination-btn" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">
            Précédent
          </button>
          <button
            v-for="(page, idx) in visiblePages"
            :key="'p-' + idx + '-' + page"
            type="button"
            class="pagination-btn"
            :class="{ active: page === currentPage, ellipsis: page === '…' }"
            :disabled="page === '…'"
            @click="page !== '…' && goToPage(page)"
          >
            {{ page }}
          </button>
          <button type="button" class="pagination-btn" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">
            Suivant
          </button>
        </div>
      </div>
    </section>

    <!-- Modal territoire -->
    <div v-if="showTerritoryModal" class="modal-overlay" @click="closeTerritoryModal">
      <div class="modal" @click.stop>
        <div class="modal-head">
          <h2>{{ editingTerritory ? 'Modifier le territoire' : 'Nouveau territoire' }}</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeTerritoryModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label for="territory-code">Code *</label>
              <input id="territory-code" v-model="territoryForm.code" type="text" class="control" required placeholder="DAKAR_VILLE…" />
            </div>
            <div class="field">
              <label for="territory-name">Nom *</label>
              <input id="territory-name" v-model="territoryForm.name" type="text" class="control" required />
            </div>
            <div class="field full">
              <label for="territory-description">Description</label>
              <textarea id="territory-description" v-model="territoryForm.description" class="control" rows="3"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeTerritoryModal">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="savingTerritory" @click="saveTerritory">
            {{ savingTerritory ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal agence -->
    <div v-if="showAgencyModal" class="modal-overlay" @click="closeAgencyModal">
      <div class="modal" @click.stop>
        <div class="modal-head">
          <h2>{{ editingAgency ? 'Modifier l’agence' : 'Nouvelle agence' }}</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeAgencyModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label for="agency-code">Code *</label>
              <input id="agency-code" v-model="agencyForm.code" type="text" class="control" required placeholder="501…" />
            </div>
            <div class="field">
              <label for="agency-name">Nom *</label>
              <input id="agency-name" v-model="agencyForm.name" type="text" class="control" required />
            </div>
            <div class="field full">
              <label for="agency-territory">Territoire</label>
              <select id="agency-territory" v-model="agencyForm.territory_id" class="control">
                <option value="">Aucun</option>
                <option v-for="territory in territories" :key="territory.id" :value="territory.id">
                  {{ territory.name }} ({{ territory.code }})
                </option>
              </select>
            </div>
            <div class="field full">
              <label for="agency-description">Description</label>
              <textarea id="agency-description" v-model="agencyForm.description" class="control" rows="3"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeAgencyModal">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="savingAgency" @click="saveAgency">
            {{ savingAgency ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal utilisateur -->
    <div v-if="showUserModal" class="modal-overlay" @click="closeUserModal">
      <div class="modal" @click.stop>
        <div class="modal-head">
          <h2>{{ editingUser ? 'Modifier l’utilisateur' : 'Nouvel utilisateur' }}</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeUserModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label for="user-name">Nom *</label>
              <input id="user-name" v-model="userForm.name" type="text" class="control" required />
            </div>
            <div class="field">
              <label for="user-email">Email *</label>
              <input id="user-email" v-model="userForm.email" type="email" class="control" required />
            </div>
            <div class="field full">
              <label for="user-password">Mot de passe {{ editingUser ? '(optionnel)' : '*' }}</label>
              <input id="user-password" v-model="userForm.password" type="password" class="control" :required="!editingUser" />
            </div>
            <div class="field">
              <label for="user-profile">Profil *</label>
              <select id="user-profile" v-model="userForm.profile_id" class="control" required>
                <option value="">Sélectionner…</option>
                <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                  {{ profile.name }} ({{ profile.code }})
                </option>
              </select>
            </div>
            <div class="field">
              <label for="user-territory">Territoire</label>
              <select id="user-territory" v-model="userForm.territory_id" class="control">
                <option value="">Aucun</option>
                <option v-for="territory in territories" :key="territory.id" :value="territory.id">
                  {{ territory.name }} ({{ territory.code }})
                </option>
              </select>
            </div>
            <div class="field full">
              <label for="user-agency">Agence</label>
              <select id="user-agency" v-model="userForm.agency_id" class="control">
                <option value="">Aucune</option>
                <option v-for="agency in agencies" :key="agency.id" :value="agency.id">
                  {{ agency.name }} ({{ agency.code }})
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeUserModal">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="savingUser" @click="saveUser">
            {{ savingUser ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal profil -->
    <div v-if="showProfileModal" class="modal-overlay" @click="closeProfileModal">
      <div class="modal modal-lg" @click.stop>
        <div class="modal-head">
          <h2>{{ editingProfile ? 'Modifier le profil' : 'Nouveau profil' }}</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeProfileModal">×</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label for="profile-code">Code *</label>
            <input id="profile-code" v-model="profileForm.code" type="text" class="control" :disabled="!!editingProfile" required placeholder="ADMIN, DGA…" />
            <p class="hint">Unique, en majuscules</p>
          </div>
          <div class="field">
            <label for="profile-name">Nom *</label>
            <input id="profile-name" v-model="profileForm.name" type="text" class="control" required />
          </div>
          <div class="field">
            <label for="profile-description">Description</label>
            <textarea id="profile-description" v-model="profileForm.description" class="control" rows="3"></textarea>
          </div>
          <div class="field">
            <label>Permissions</label>
            <div class="perm-grid">
              <label v-for="permission in availablePermissions" :key="permission" class="perm-item">
                <input type="checkbox" :value="permission" :checked="profileForm.permissions.includes(permission)" @change="togglePermission(permission)" />
                <span>{{ permission }}</span>
              </label>
            </div>
          </div>
          <label class="check-row">
            <input type="checkbox" v-model="profileForm.is_active" />
            <span>Profil actif</span>
          </label>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeProfileModal">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="savingProfile" @click="saveProfile">
            {{ savingProfile ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal responsable -->
    <div v-if="showAssignResponsibleModal" class="modal-overlay" @click="closeModals">
      <div class="modal" @click.stop>
        <div class="modal-head">
          <h2>Assigner un responsable de zone</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeModals">×</button>
        </div>
        <div class="modal-body">
          <div class="entity-box">
            <code class="mono">{{ selectedTerritory?.code }}</code>
            <span>{{ selectedTerritory?.name }}</span>
          </div>
          <div class="field">
            <label for="responsible-select">Responsable *</label>
            <select id="responsible-select" v-model="selectedResponsibleId" class="control">
              <option value="">Sélectionner…</option>
              <option v-for="user in responsablesZone" :key="user.id" :value="user.id">
                {{ user.name }} ({{ user.email }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeModals">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="!selectedResponsibleId || assigning" @click="assignResponsible">
            {{ assigning ? 'Enregistrement…' : 'Enregistrer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal chef agence -->
    <div v-if="showAssignChefAgenceModal" class="modal-overlay" @click="closeModals">
      <div class="modal" @click.stop>
        <div class="modal-head">
          <h2>Assigner un chef d’agence</h2>
          <button type="button" class="icon-btn" aria-label="Fermer" @click="closeModals">×</button>
        </div>
        <div class="modal-body">
          <div class="entity-box">
            <code class="mono">{{ selectedAgency?.code }}</code>
            <span>{{ selectedAgency?.name }}</span>
          </div>
          <div class="field">
            <label for="chef-agence-select">Chef d’agence *</label>
            <select id="chef-agence-select" v-model="selectedChefAgenceId" class="control">
              <option value="">Sélectionner…</option>
              <option v-for="user in chefsAgence" :key="user.id" :value="user.id">
                {{ user.name }} ({{ user.email }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-foot">
          <button type="button" class="btn btn-ghost" @click="closeModals">Annuler</button>
          <button type="button" class="btn btn-primary" :disabled="!selectedChefAgenceId || assigning" @click="assignChefAgence">
            {{ assigning ? 'Enregistrement…' : 'Enregistrer' }}
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
      showTerritoryModal: false,
      editingTerritory: null,
      territoryForm: {
        code: '',
        name: '',
        description: ''
      },
      savingTerritory: false,
      showAgencyModal: false,
      editingAgency: null,
      agencyForm: {
        code: '',
        name: '',
        description: '',
        territory_id: ''
      },
      savingAgency: false,
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
      availablePermissions: [],
      searchQuery: '',
      currentPage: 1,
      pageSize: 10
    }
  },
  computed: {
    searchNormalized() {
      return (this.searchQuery || '').trim().toLowerCase();
    },
    filteredTerritories() {
      const q = this.searchNormalized;
      if (!q) return this.territories;
      return this.territories.filter((t) => this.matchesSearch(q, [
        t.code, t.name, t.description, t.responsible?.name, t.responsible?.email
      ]));
    },
    filteredAgencies() {
      const q = this.searchNormalized;
      if (!q) return this.agencies;
      return this.agencies.filter((a) => {
        const chef = a.chefAgence || a.chef_agence;
        return this.matchesSearch(q, [
          a.code, a.name, a.territory?.name, chef?.name, chef?.email
        ]);
      });
    },
    filteredUsers() {
      const q = this.searchNormalized;
      if (!q) return this.users;
      return this.users.filter((u) => this.matchesSearch(q, [
        u.name, u.email, u.profile?.name, u.profile?.code, u.territory?.name, u.agency?.name
      ]));
    },
    filteredProfiles() {
      const q = this.searchNormalized;
      if (!q) return this.profiles;
      return this.profiles.filter((p) => this.matchesSearch(q, [
        p.code, p.name, p.description
      ]));
    },
    currentResultCount() {
      if (this.activeTab === 'territories') return this.filteredTerritories.length;
      if (this.activeTab === 'agencies') return this.filteredAgencies.length;
      if (this.activeTab === 'users') return this.filteredUsers.length;
      return this.filteredProfiles.length;
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.currentResultCount / this.pageSize));
    },
    pageStart() {
      if (this.currentResultCount === 0) return 0;
      return (this.currentPage - 1) * this.pageSize + 1;
    },
    pageEnd() {
      return Math.min(this.currentPage * this.pageSize, this.currentResultCount);
    },
    paginatedTerritories() {
      return this.slicePage(this.filteredTerritories);
    },
    paginatedAgencies() {
      return this.slicePage(this.filteredAgencies);
    },
    paginatedUsers() {
      return this.slicePage(this.filteredUsers);
    },
    paginatedProfiles() {
      return this.slicePage(this.filteredProfiles);
    },
    visiblePages() {
      const total = this.totalPages;
      const current = this.currentPage;
      if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1);
      }
      const pages = new Set([1, total, current, current - 1, current + 1]);
      if (current <= 3) {
        pages.add(2);
        pages.add(3);
        pages.add(4);
      }
      if (current >= total - 2) {
        pages.add(total - 1);
        pages.add(total - 2);
        pages.add(total - 3);
      }
      const sorted = [...pages].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b);
      const withEllipsis = [];
      let prev = 0;
      for (const p of sorted) {
        if (prev && p - prev > 1) withEllipsis.push('…');
        withEllipsis.push(p);
        prev = p;
      }
      return withEllipsis;
    },
    searchPlaceholder() {
      const map = {
        territories: 'Rechercher un territoire…',
        agencies: 'Rechercher une agence…',
        users: 'Rechercher un utilisateur…',
        profiles: 'Rechercher un profil…'
      };
      return map[this.activeTab] || 'Rechercher…';
    }
  },
  watch: {
    activeTab() {
      this.searchQuery = '';
      this.currentPage = 1;
    },
    searchQuery() {
      this.currentPage = 1;
    },
    pageSize() {
      this.currentPage = 1;
    },
    currentResultCount() {
      if (this.currentPage > this.totalPages) {
        this.currentPage = this.totalPages;
      }
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    setTab(tab) {
      this.activeTab = tab;
    },
    slicePage(list) {
      const start = (this.currentPage - 1) * this.pageSize;
      return list.slice(start, start + this.pageSize);
    },
    goToPage(page) {
      const p = Number(page);
      if (!Number.isFinite(p) || p < 1 || p > this.totalPages) return;
      this.currentPage = p;
    },
    matchesSearch(q, values) {
      return values.some((v) => String(v || '').toLowerCase().includes(q));
    },
    initials(name) {
      if (!name || typeof name !== 'string') return '?';
      const parts = name.trim().split(/\s+/).filter(Boolean);
      if (parts.length === 0) return '?';
      if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    },
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
          const count = response.data.count;
          this.syncMessage = response.data.message || `Synchronisation terminée (${count ?? this.agencies.length} agence(s)).`;
          this.syncMessageType = 'success';
          await Promise.all([this.loadAgencies(), this.loadTerritories()]);
        } else {
          const detail = response.data.output ? ` — ${String(response.data.output).trim().split('\n').pop()}` : '';
          this.syncMessage = (response.data.message || 'Erreur lors de la synchronisation') + detail;
          this.syncMessageType = 'error';
          console.error('Sync agences échouée:', response.data);
        }
      } catch (error) {
        const data = error.response?.data;
        const detail = data?.output ? ` — ${String(data.output).trim().split('\n').pop()}` : '';
        this.syncMessage = (data?.message || error.message) + detail;
        this.syncMessageType = 'error';
        console.error('Erreur lors de la synchronisation:', error);
      } finally {
        this.syncing = false;
        setTimeout(() => {
          this.syncMessage = '';
        }, 12000);
      }
    },
    openCreateTerritoryModal() {
      this.editingTerritory = null;
      this.territoryForm = { code: '', name: '', description: '' };
      this.showTerritoryModal = true;
    },
    openEditTerritoryModal(territory) {
      this.editingTerritory = territory;
      this.territoryForm = {
        code: territory.code || '',
        name: territory.name || '',
        description: territory.description || ''
      };
      this.showTerritoryModal = true;
    },
    closeTerritoryModal() {
      this.showTerritoryModal = false;
      this.editingTerritory = null;
      this.territoryForm = { code: '', name: '', description: '' };
    },
    async saveTerritory() {
      if (!this.territoryForm.code?.trim() || !this.territoryForm.name?.trim()) {
        alert('Veuillez renseigner le code et le nom du territoire.');
        return;
      }

      this.savingTerritory = true;
      try {
        const token = localStorage.getItem('token');
        const payload = {
          code: this.territoryForm.code.trim().toUpperCase().replace(/\s+/g, '_'),
          name: this.territoryForm.name.trim(),
          description: this.territoryForm.description?.trim() || null
        };

        if (this.editingTerritory) {
          await axios.put(
            `/api/territories/${this.editingTerritory.id}`,
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
          );
        } else {
          await axios.post(
            '/api/territories',
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
          );
        }

        await this.loadTerritories();
        const wasEdit = !!this.editingTerritory;
        this.closeTerritoryModal();
        alert(wasEdit ? '✅ Territoire modifié avec succès!' : '✅ Territoire créé avec succès!');
      } catch (error) {
        const errors = error.response?.data?.errors;
        const errorMsg = errors
          ? Object.values(errors).flat().join('\n')
          : (error.response?.data?.message || error.message);
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur sauvegarde territoire:', error);
      } finally {
        this.savingTerritory = false;
      }
    },
    confirmDeleteTerritory(territory) {
      if (confirm(`Supprimer le territoire « ${territory.name} » ?`)) {
        this.deleteTerritory(territory);
      }
    },
    async deleteTerritory(territory) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`/api/territories/${territory.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        await Promise.all([this.loadTerritories(), this.loadAgencies()]);
        alert('✅ Territoire supprimé avec succès!');
      } catch (error) {
        alert('❌ Erreur: ' + (error.response?.data?.message || error.message));
        console.error('Erreur suppression territoire:', error);
      }
    },
    openCreateAgencyModal() {
      this.editingAgency = null;
      this.agencyForm = { code: '', name: '', description: '', territory_id: '' };
      this.showAgencyModal = true;
    },
    openEditAgencyModal(agency) {
      this.editingAgency = agency;
      this.agencyForm = {
        code: agency.code || '',
        name: agency.name || '',
        description: agency.description || '',
        territory_id: agency.territory_id || agency.territory?.id || ''
      };
      this.showAgencyModal = true;
    },
    closeAgencyModal() {
      this.showAgencyModal = false;
      this.editingAgency = null;
      this.agencyForm = { code: '', name: '', description: '', territory_id: '' };
    },
    async saveAgency() {
      if (!this.agencyForm.code?.trim() || !this.agencyForm.name?.trim()) {
        alert('Veuillez renseigner le code et le nom de l’agence.');
        return;
      }

      this.savingAgency = true;
      try {
        const token = localStorage.getItem('token');
        const payload = {
          code: this.agencyForm.code.trim().toUpperCase(),
          name: this.agencyForm.name.trim(),
          description: this.agencyForm.description?.trim() || null,
          territory_id: this.agencyForm.territory_id || null
        };

        if (this.editingAgency) {
          await axios.put(
            `/api/agencies/${this.editingAgency.id}`,
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
          );
        } else {
          await axios.post(
            '/api/agencies',
            payload,
            { headers: { Authorization: `Bearer ${token}` } }
          );
        }

        await this.loadAgencies();
        const wasEdit = !!this.editingAgency;
        this.closeAgencyModal();
        alert(wasEdit ? '✅ Agence modifiée avec succès!' : '✅ Agence créée avec succès!');
      } catch (error) {
        const errors = error.response?.data?.errors;
        const errorMsg = errors
          ? Object.values(errors).flat().join('\n')
          : (error.response?.data?.message || error.message);
        alert('❌ Erreur: ' + errorMsg);
        console.error('Erreur sauvegarde agence:', error);
      } finally {
        this.savingAgency = false;
      }
    },
    confirmDeleteAgency(agency) {
      if (confirm(`Supprimer l’agence « ${agency.name} » (${agency.code}) ?`)) {
        this.deleteAgency(agency);
      }
    },
    async deleteAgency(agency) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`/api/agencies/${agency.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        await this.loadAgencies();
        alert('✅ Agence supprimée avec succès!');
      } catch (error) {
        alert('❌ Erreur: ' + (error.response?.data?.message || error.message));
        console.error('Erreur suppression agence:', error);
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
.tam {
  --brand: #1A4D3A;
  --brand-hover: #163f30;
  --text: #1c2430;
  --muted: #6b7280;
  --border: #e5e7eb;
  --bg: #f8faf9;
  --surface: #ffffff;
  --warn-bg: #fff7ed;
  --warn-text: #9a3412;
  --danger: #b91c1c;

  width: 100%;
  min-height: 100%;
  padding: 24px 28px 40px;
  background: var(--bg);
  color: var(--text);
  box-sizing: border-box;
}

.tam-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.tam-page-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--text);
}

.tam-page-header p {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--muted);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--brand);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--brand-hover);
}

.btn-secondary {
  background: var(--surface);
  color: var(--brand);
  border-color: #c9d8d0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f0f6f3;
  border-color: var(--brand);
}

.btn-ghost {
  background: transparent;
  color: var(--text);
  border-color: var(--border);
}

.btn-ghost:hover {
  background: #f3f4f6;
}

.btn-link {
  background: none;
  border: none;
  padding: 0;
  margin-right: 12px;
  color: var(--brand);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.btn-link:hover {
  text-decoration: underline;
}

.btn-link.danger {
  color: var(--danger);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #c9d8d0;
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.tam-alert {
  margin-bottom: 16px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid transparent;
}

.tam-alert.success {
  background: #ecfdf5;
  color: #065f46;
  border-color: #a7f3d0;
}

.tam-alert.error {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}

.tam-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
}

.tam-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  padding: 0 8px;
  overflow-x: auto;
  background: #fcfcfc;
}

.tam-tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 46px;
  padding: 0 14px;
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.tam-tab:hover {
  color: var(--text);
}

.tam-tab.active {
  color: var(--brand);
}

.tam-tab.active::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  bottom: -1px;
  height: 2px;
  background: var(--brand);
}

.tam-tab .count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: #eef2f0;
  color: #4b5563;
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.tam-tab.active .count {
  background: #e2efe8;
  color: var(--brand);
}

.tam-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.search-wrap {
  position: relative;
  flex: 1;
  min-width: 220px;
  max-width: 360px;
}

.search-icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 34px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #8fb3a1;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.toolbar-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-count {
  font-size: 12px;
  color: var(--muted);
}

.tam-body {
  padding: 0;
}

.info-banner {
  margin: 16px 16px 0;
  padding: 12px 14px;
  background: var(--warn-bg);
  color: var(--warn-text);
  border: 1px solid #fed7aa;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
}

.info-banner code {
  font-size: 12px;
  background: rgba(0,0,0,0.05);
  padding: 1px 5px;
  border-radius: 3px;
}

.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.data-table th {
  text-align: left;
  padding: 11px 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7280;
  background: #f9fafb;
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 13px 16px;
  font-size: 13px;
  border-bottom: 1px solid #f1f3f5;
  vertical-align: middle;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #fafbfc;
}

.col-actions {
  width: 1%;
  white-space: nowrap;
  text-align: left;
}

.data-table th.col-actions,
.data-table td.col-actions {
  text-align: left;
  padding-right: 20px;
}

.data-table td.col-actions .btn-link:last-child {
  margin-right: 0;
}

.tam-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  background: #fafbfc;
}

.pagination-info {
  font-size: 12px;
  color: var(--muted);
  min-width: 110px;
}

.pagination-size {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}

.page-size-select {
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  color: #374151;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.pagination-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
  color: #374151;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.pagination-btn:hover:not(:disabled):not(.ellipsis) {
  border-color: #8fb3a1;
  color: var(--brand);
}

.pagination-btn.active {
  background: var(--brand);
  border-color: var(--brand);
  color: #fff;
}

.pagination-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.pagination-btn.ellipsis {
  border: none;
  background: transparent;
  cursor: default;
  min-width: 20px;
  padding: 0 2px;
}

.empty-cell {
  text-align: center !important;
  color: var(--muted);
  padding: 40px 16px !important;
}

.strong { font-weight: 600; }
.muted { color: var(--muted); }

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  background: #f3f4f6;
  padding: 2px 7px;
  border-radius: 4px;
}

.person {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e8eee9;
  color: var(--brand);
  font-size: 10px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.person-name {
  display: block;
  font-weight: 600;
  font-size: 13px;
  line-height: 1.2;
}

.person-sub {
  display: block;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.3;
}

.tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.tag-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.tag-green {
  background: #ecfdf5;
  color: #065f46;
}

.tag-warn {
  background: #fff7ed;
  color: #9a3412;
}

.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
}

.status-dot::before {
  content: '';
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #9ca3af;
}

.status-dot.on {
  color: #065f46;
}

.status-dot.on::before {
  background: #10b981;
}

.status-dot.off {
  color: #6b7280;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: auto;
  background: #fff;
  border-radius: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.16);
}

.modal-lg {
  max-width: 620px;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border);
}

.modal-head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
  color: var(--text);
}

.icon-btn {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 6px;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.icon-btn:hover {
  background: #e5e7eb;
  color: #111827;
}

.modal-body {
  padding: 18px;
}

.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 18px;
  border-top: 1px solid var(--border);
  background: #fafafa;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.field {
  margin-bottom: 14px;
}

.form-grid .field {
  margin-bottom: 0;
}

.field.full {
  grid-column: 1 / -1;
}

.field label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.control {
  width: 100%;
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
  color: var(--text);
  box-sizing: border-box;
}

textarea.control {
  height: auto;
  padding: 10px 11px;
  resize: vertical;
  min-height: 84px;
}

.control:focus {
  outline: none;
  border-color: #8fb3a1;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.control:disabled {
  background: #f9fafb;
  color: #9ca3af;
}

.entity-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 14px;
  background: #f9fafb;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
}

.perm-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  max-height: 200px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fafafa;
}

.perm-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 5px;
  font-size: 12px;
  cursor: pointer;
}

.perm-item input,
.check-row input {
  accent-color: var(--brand);
}

.check-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

@media (max-width: 860px) {
  .tam {
    padding: 16px;
  }

  .tam-page-header {
    flex-direction: column;
  }

  .form-grid,
  .perm-grid {
    grid-template-columns: 1fr;
  }
}
</style>
