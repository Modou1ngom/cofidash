// Système de gestion des profils et permissions

export const PROFILES = {
  MD: 'MD',
  ADMIN: 'ADMIN',
  DGA: 'DGA',
  RESPONSABLE_ZONE: 'RESPONSABLE_ZONE',
  CHEF_AGENCE: 'CHEF_AGENCE',
  CAF: 'CAF',
  CC: 'CC',
  FINANCES: 'FINANCES',
  EXPLOITATIONS: 'EXPLOITATIONS'
};

export const PROFILE_LABELS = {
  [PROFILES.MD]: 'Directeur Général',
  [PROFILES.ADMIN]: 'Administrateur',
  [PROFILES.DGA]: 'Directeur Général Adjoint',
  [PROFILES.RESPONSABLE_ZONE]: 'Responsable Zone',
  [PROFILES.CHEF_AGENCE]: 'Chef d\'Agence',
  [PROFILES.CAF]: 'CAF',
  [PROFILES.CC]: 'Conseiller Client',
  [PROFILES.FINANCES]: 'Finances',
  [PROFILES.EXPLOITATIONS]: 'Exploitations'
};

export const PROFILE_DESCRIPTIONS = {
  [PROFILES.MD]: 'Valide les objectifs fixés par le DGA',
  [PROFILES.ADMIN]: 'Accès complet - Peut tout faire',
  [PROFILES.DGA]: 'Fixe les objectifs pour les zones - Doit être validé par le MD',
  [PROFILES.RESPONSABLE_ZONE]: 'Fixe les objectifs pour les agences - Doit être validé par le DGA',
  [PROFILES.CHEF_AGENCE]: 'Fixe les objectifs pour ses CAF - Doit être validé par le Responsable Zone',
  [PROFILES.CAF]: 'Consultation uniquement - Pas de droits d\'ajout d\'objectifs',
  [PROFILES.CC]: 'Accès à la consultation Client Vue 360°',
  [PROFILES.FINANCES]: 'Gérer la gestion financière',
  [PROFILES.EXPLOITATIONS]: 'Consultation simple'
};

// Permissions par profil
export const PERMISSIONS = {
  // Permissions générales
  VIEW_DASHBOARD: 'VIEW_DASHBOARD',
  VIEW_CLIENT: 'VIEW_CLIENT',
  VIEW_VUE360: 'VIEW_VUE360',
  VIEW_ZONES: 'VIEW_ZONES',
  VIEW_AGENCIES: 'VIEW_AGENCIES',
  
  // Permissions d'édition
  EDIT_OBJECTIVES: 'EDIT_OBJECTIVES',
  MODIFY_OBJECTIVES: 'MODIFY_OBJECTIVES',
  
  // Permissions financières
  MANAGE_FINANCIAL: 'MANAGE_FINANCIAL',
  VIEW_FINANCIAL: 'VIEW_FINANCIAL',
  
  // Permissions d'administration
  ADMIN_ACCESS: 'ADMIN_ACCESS',
  MANAGE_USERS: 'MANAGE_USERS',
  MANAGE_SETTINGS: 'MANAGE_SETTINGS'
};

// Configuration des permissions par profil
export const PROFILE_PERMISSIONS = {
  [PROFILES.ADMIN]: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.EDIT_OBJECTIVES,
    PERMISSIONS.MODIFY_OBJECTIVES,
    PERMISSIONS.MANAGE_FINANCIAL,
    PERMISSIONS.VIEW_FINANCIAL,
    PERMISSIONS.ADMIN_ACCESS,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.MANAGE_SETTINGS
  ],
  [PROFILES.DGA]: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.EDIT_OBJECTIVES,
    PERMISSIONS.MODIFY_OBJECTIVES,
    PERMISSIONS.VIEW_FINANCIAL
  ],
  [PROFILES.FINANCES]: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.MANAGE_FINANCIAL,
    PERMISSIONS.VIEW_FINANCIAL
  ],
  [PROFILES.EXPLOITATIONS]: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES
  ],
  [PROFILES.CC]: [
    PERMISSIONS.VIEW_VUE360,
    PERMISSIONS.VIEW_CLIENT
  ]
};

// Vérifier si un profil a une permission
export function hasPermission(profile, permission) {
  if (!profile || !PROFILE_PERMISSIONS[profile]) {
    return false;
  }
  return PROFILE_PERMISSIONS[profile].includes(permission);
}

// Obtenir toutes les permissions d'un profil
export function getProfilePermissions(profile) {
  return PROFILE_PERMISSIONS[profile] || [];
}

// Gestion du profil utilisateur actuel (depuis localStorage ou API)
export const ProfileManager = {
  getCurrentProfile() {
    // Récupérer depuis localStorage (défini lors de la connexion)
    const stored = localStorage.getItem('userProfile');
    return stored || null;
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getCurrentProfileData() {
    const user = this.getCurrentUser();
    return user?.profile || null;
  },

  hasPermission(permission) {
    const profileData = this.getCurrentProfileData();
    if (!profileData || !profileData.permissions) {
      return false;
    }
    return profileData.permissions.includes(permission);
  },

  canEditObjectives() {
    return this.hasPermission(PERMISSIONS.EDIT_OBJECTIVES) || 
           this.hasPermission(PERMISSIONS.MODIFY_OBJECTIVES);
  },

  canCreateZoneObjectives() {
    const profileCode = this.getCurrentProfileData()?.code;
    return profileCode === PROFILES.DGA || profileCode === PROFILES.ADMIN || profileCode === PROFILES.MD;
  },

  canCreateAgencyObjectives() {
    const profileCode = this.getCurrentProfileData()?.code;
    return profileCode === PROFILES.RESPONSABLE_ZONE || profileCode === PROFILES.ADMIN || profileCode === PROFILES.MD;
  },

  canCreateCAFObjectives() {
    const profileCode = this.getCurrentProfileData()?.code;
    return profileCode === PROFILES.CHEF_AGENCE || profileCode === PROFILES.ADMIN || profileCode === PROFILES.MD;
  },

  canValidateObjectives() {
    const profileCode = this.getCurrentProfileData()?.code;
    return [PROFILES.MD, PROFILES.DGA, PROFILES.RESPONSABLE_ZONE, PROFILES.ADMIN].includes(profileCode);
  },

  getProfileCode() {
    return this.getCurrentProfileData()?.code;
  },

  canManageFinancial() {
    return this.hasPermission(PERMISSIONS.MANAGE_FINANCIAL);
  },

  isAdmin() {
    const profileData = this.getCurrentProfileData();
    return profileData?.code === PROFILES.ADMIN || 
           this.hasPermission(PERMISSIONS.ADMIN_ACCESS);
  },

  isCAF() {
    const code = String(this.getProfileCode() || this.getCurrentProfile() || '').toUpperCase();
    return code === PROFILES.CAF;
  },

  isCC() {
    const code = String(this.getProfileCode() || this.getCurrentProfile() || '').toUpperCase();
    return code === PROFILES.CC;
  },

  canViewVue360() {
    return this.isCC() || this.hasPermission(PERMISSIONS.VIEW_VUE360);
  },

  /** Page d'accueil après connexion selon le profil. */
  getHomeRoute() {
    if (this.isCAF()) {
      return '/vue360/caf';
    }
    if (this.isCC()) {
      return '/vue360/recherche';
    }
    return '/dashboard';
  },

  // Charger les profils depuis l'API
  async loadProfilesFromAPI() {
    try {
      const response = await fetch('/api/profiles');
      return await response.json();
    } catch (error) {
      console.error('Erreur lors du chargement des profils:', error);
      return [];
    }
  }
};

