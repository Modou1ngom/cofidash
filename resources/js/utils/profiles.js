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
  VIEW_DASHBOARD: 'VIEW_DASHBOARD',
  VIEW_CLIENT: 'VIEW_CLIENT',
  VIEW_VUE360: 'VIEW_VUE360',
  VIEW_ZONES: 'VIEW_ZONES',
  VIEW_AGENCIES: 'VIEW_AGENCIES',
  EDIT_OBJECTIVES: 'EDIT_OBJECTIVES',
  MODIFY_OBJECTIVES: 'MODIFY_OBJECTIVES',
  CREATE_ZONE_OBJECTIVES: 'CREATE_ZONE_OBJECTIVES',
  VALIDATE_ZONE_OBJECTIVES: 'VALIDATE_ZONE_OBJECTIVES',
  CREATE_AGENCY_OBJECTIVES: 'CREATE_AGENCY_OBJECTIVES',
  VALIDATE_AGENCY_OBJECTIVES: 'VALIDATE_AGENCY_OBJECTIVES',
  CREATE_CAF_OBJECTIVES: 'CREATE_CAF_OBJECTIVES',
  VALIDATE_DGA_OBJECTIVES: 'VALIDATE_DGA_OBJECTIVES',
  MANAGE_FINANCIAL: 'MANAGE_FINANCIAL',
  VIEW_FINANCIAL: 'VIEW_FINANCIAL',
  ADMIN_ACCESS: 'ADMIN_ACCESS',
  MANAGE_USERS: 'MANAGE_USERS',
  MANAGE_SETTINGS: 'MANAGE_SETTINGS',
  MENU_CLIENTS: 'MENU_CLIENTS',
  MENU_CAF_OVERVIEW: 'MENU_CAF_OVERVIEW',
  MENU_COMPTES_OUVERTS: 'MENU_COMPTES_OUVERTS',
  MENU_COLLECTE_EPARGNE: 'MENU_COLLECTE_EPARGNE',
  MENU_PORTEFEUILLE_RISQUE: 'MENU_PORTEFEUILLE_RISQUE',
  MENU_NEW_DEAL: 'MENU_NEW_DEAL',
  MENU_TRANSFERTS: 'MENU_TRANSFERTS',
  MENU_OBJECTIFS_VIEW: 'MENU_OBJECTIFS_VIEW',
  MENU_OBJECTIFS_ADD: 'MENU_OBJECTIFS_ADD',
  MENU_OBJECTIFS_VALIDATE: 'MENU_OBJECTIFS_VALIDATE',
  MENU_GESTION_DONNEES: 'MENU_GESTION_DONNEES',
  MENU_GESTION_ENVIRONNEMENTS: 'MENU_GESTION_ENVIRONNEMENTS'
};

export const PERMISSION_GROUPS = [
  {
    id: 'consultation',
    label: 'Consultation',
    permissions: [
      { value: PERMISSIONS.VIEW_DASHBOARD, label: 'Voir le tableau de bord' },
      { value: PERMISSIONS.VIEW_CLIENT, label: 'Voir les clients' },
      { value: PERMISSIONS.VIEW_VUE360, label: 'Voir Client Vue 360°' },
      { value: PERMISSIONS.VIEW_ZONES, label: 'Voir les zones' },
      { value: PERMISSIONS.VIEW_AGENCIES, label: 'Voir les agences' },
      { value: PERMISSIONS.VIEW_FINANCIAL, label: 'Voir les finances' }
    ]
  },
  {
    id: 'menus',
    label: 'Menus',
    permissions: [
      { value: PERMISSIONS.MENU_CLIENTS, label: 'Clients' },
      { value: PERMISSIONS.MENU_CAF_OVERVIEW, label: 'Vue d’ensemble CAF' },
      { value: PERMISSIONS.MENU_COMPTES_OUVERTS, label: 'Comptes ouverts' },
      { value: PERMISSIONS.MENU_COLLECTE_EPARGNE, label: 'Collecte d’épargne à vue' },
      { value: PERMISSIONS.MENU_PORTEFEUILLE_RISQUE, label: 'Portefeuille à risque' },
      { value: PERMISSIONS.MENU_NEW_DEAL, label: 'New Deal' },
      { value: PERMISSIONS.MENU_TRANSFERTS, label: 'Transferts' },
      { value: PERMISSIONS.MENU_OBJECTIFS_VIEW, label: 'Mes objectifs' },
      { value: PERMISSIONS.MENU_OBJECTIFS_ADD, label: 'Ajouter des objectifs' },
      { value: PERMISSIONS.MENU_OBJECTIFS_VALIDATE, label: 'Valider des objectifs' },
      { value: PERMISSIONS.MENU_GESTION_DONNEES, label: 'Gestion — Données' },
      { value: PERMISSIONS.MENU_GESTION_ENVIRONNEMENTS, label: 'Gestion — Environnements' }
    ]
  },
  {
    id: 'objectifs',
    label: 'Objectifs',
    permissions: [
      { value: PERMISSIONS.EDIT_OBJECTIVES, label: 'Éditer les objectifs' },
      { value: PERMISSIONS.MODIFY_OBJECTIVES, label: 'Modifier les objectifs' },
      { value: PERMISSIONS.CREATE_ZONE_OBJECTIVES, label: 'Créer les objectifs de zone' },
      { value: PERMISSIONS.VALIDATE_ZONE_OBJECTIVES, label: 'Valider les objectifs de zone' },
      { value: PERMISSIONS.CREATE_AGENCY_OBJECTIVES, label: 'Créer les objectifs d’agence' },
      { value: PERMISSIONS.VALIDATE_AGENCY_OBJECTIVES, label: 'Valider les objectifs d’agence' },
      { value: PERMISSIONS.CREATE_CAF_OBJECTIVES, label: 'Créer les objectifs CAF' },
      { value: PERMISSIONS.VALIDATE_DGA_OBJECTIVES, label: 'Valider les objectifs DGA' }
    ]
  },
  {
    id: 'administration',
    label: 'Administration',
    permissions: [
      { value: PERMISSIONS.MANAGE_FINANCIAL, label: 'Gérer les finances' },
      { value: PERMISSIONS.ADMIN_ACCESS, label: 'Accès administrateur' },
      { value: PERMISSIONS.MANAGE_USERS, label: 'Gérer les utilisateurs' },
      { value: PERMISSIONS.MANAGE_SETTINGS, label: 'Gérer les paramètres' }
    ]
  }
];

export const AVAILABLE_PERMISSIONS = PERMISSION_GROUPS.flatMap((group) => group.permissions);

const KNOWN_PERMISSIONS = new Set(Object.values(PERMISSIONS));

const PERMISSION_ALIASES = {
  view_dashboard: PERMISSIONS.VIEW_DASHBOARD,
  view_client: PERMISSIONS.VIEW_CLIENT,
  view_vue360: PERMISSIONS.VIEW_VUE360,
  view_zones: PERMISSIONS.VIEW_ZONES,
  view_agencies: PERMISSIONS.VIEW_AGENCIES,
  view_financial: PERMISSIONS.VIEW_FINANCIAL,
  edit_objectives: PERMISSIONS.EDIT_OBJECTIVES,
  modify_objectives: PERMISSIONS.MODIFY_OBJECTIVES,
  manage_users: PERMISSIONS.MANAGE_USERS,
  manage_settings: PERMISSIONS.MANAGE_SETTINGS,
  manage_financial: PERMISSIONS.MANAGE_FINANCIAL,
  admin_access: PERMISSIONS.ADMIN_ACCESS,
  menu_clients: PERMISSIONS.MENU_CLIENTS,
  menu_caf_overview: PERMISSIONS.MENU_CAF_OVERVIEW,
  menu_comptes_ouverts: PERMISSIONS.MENU_COMPTES_OUVERTS,
  menu_collecte_epargne: PERMISSIONS.MENU_COLLECTE_EPARGNE,
  menu_portefeuille_risque: PERMISSIONS.MENU_PORTEFEUILLE_RISQUE,
  menu_new_deal: PERMISSIONS.MENU_NEW_DEAL,
  menu_transferts: PERMISSIONS.MENU_TRANSFERTS,
  menu_objectifs_view: PERMISSIONS.MENU_OBJECTIFS_VIEW,
  menu_objectifs_add: PERMISSIONS.MENU_OBJECTIFS_ADD,
  menu_objectifs_validate: PERMISSIONS.MENU_OBJECTIFS_VALIDATE,
  menu_gestion_donnees: PERMISSIONS.MENU_GESTION_DONNEES,
  menu_gestion_environnements: PERMISSIONS.MENU_GESTION_ENVIRONNEMENTS
};

export function normalizePermission(permission) {
  if (!permission || typeof permission !== 'string') {
    return null;
  }
  const raw = permission.trim();
  if (!raw) {
    return null;
  }
  const alias = PERMISSION_ALIASES[raw.toLowerCase()];
  if (alias) {
    return alias;
  }
  const upper = raw.toUpperCase();
  return KNOWN_PERMISSIONS.has(upper) ? upper : upper;
}

export function normalizePermissions(list) {
  const out = [];
  for (const item of list || []) {
    const normalized = normalizePermission(item);
    if (normalized && !out.includes(normalized)) {
      out.push(normalized);
    }
  }
  return out;
}

export function permissionLabel(permission) {
  return AVAILABLE_PERMISSIONS.find((item) => item.value === permission)?.label || permission;
}

export const SECTION_PERMISSIONS = {
  client: PERMISSIONS.MENU_CLIENTS,
  'caf-overview': PERMISSIONS.MENU_CAF_OVERVIEW,
  'comptes-ouverts': PERMISSIONS.MENU_COMPTES_OUVERTS,
  'collecte-epargne-a-vue': PERMISSIONS.MENU_COLLECTE_EPARGNE,
  'portefeuille-risque': PERMISSIONS.MENU_PORTEFEUILLE_RISQUE,
  'new-deal': PERMISSIONS.MENU_NEW_DEAL,
  'money-transfers': PERMISSIONS.MENU_TRANSFERTS,
  management: PERMISSIONS.MENU_GESTION_DONNEES,
  environments: PERMISSIONS.MENU_GESTION_ENVIRONNEMENTS
};

export const OBJECTIVE_SUB_PERMISSIONS = {
  mine: PERMISSIONS.MENU_OBJECTIFS_VIEW,
  add: PERMISSIONS.MENU_OBJECTIFS_ADD,
  validation: PERMISSIONS.MENU_OBJECTIFS_VALIDATE
};

const MENUS_OPERATIONAL = [
  PERMISSIONS.MENU_CLIENTS,
  PERMISSIONS.MENU_CAF_OVERVIEW,
  PERMISSIONS.MENU_COMPTES_OUVERTS,
  PERMISSIONS.MENU_COLLECTE_EPARGNE,
  PERMISSIONS.MENU_PORTEFEUILLE_RISQUE,
  PERMISSIONS.MENU_NEW_DEAL,
  PERMISSIONS.MENU_TRANSFERTS,
  PERMISSIONS.MENU_OBJECTIFS_ADD,
  PERMISSIONS.MENU_OBJECTIFS_VALIDATE
];

const MENUS_CAF = [
  PERMISSIONS.MENU_CAF_OVERVIEW,
  PERMISSIONS.MENU_COMPTES_OUVERTS,
  PERMISSIONS.MENU_COLLECTE_EPARGNE,
  PERMISSIONS.MENU_PORTEFEUILLE_RISQUE,
  PERMISSIONS.MENU_NEW_DEAL,
  PERMISSIONS.MENU_TRANSFERTS,
  PERMISSIONS.MENU_OBJECTIFS_VIEW
];

const MENUS_MD = [
  PERMISSIONS.MENU_CLIENTS,
  PERMISSIONS.MENU_CAF_OVERVIEW,
  PERMISSIONS.MENU_COMPTES_OUVERTS,
  PERMISSIONS.MENU_COLLECTE_EPARGNE,
  PERMISSIONS.MENU_PORTEFEUILLE_RISQUE,
  PERMISSIONS.MENU_NEW_DEAL,
  PERMISSIONS.MENU_TRANSFERTS,
  PERMISSIONS.MENU_OBJECTIFS_VALIDATE
];

const MENUS_ADMIN = [
  ...MENUS_OPERATIONAL,
  PERMISSIONS.MENU_CAF_OVERVIEW,
  PERMISSIONS.MENU_OBJECTIFS_VIEW,
  PERMISSIONS.MENU_GESTION_DONNEES,
  PERMISSIONS.MENU_GESTION_ENVIRONNEMENTS
];

function uniquePermissions(list) {
  return [...new Set(list)];
}

// Configuration des permissions par profil
export const PROFILE_PERMISSIONS = {
  [PROFILES.MD]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.VALIDATE_DGA_OBJECTIVES,
    PERMISSIONS.VIEW_FINANCIAL,
    ...MENUS_MD
  ]),
  [PROFILES.ADMIN]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_VUE360,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.EDIT_OBJECTIVES,
    PERMISSIONS.MODIFY_OBJECTIVES,
    PERMISSIONS.VALIDATE_DGA_OBJECTIVES,
    PERMISSIONS.VALIDATE_ZONE_OBJECTIVES,
    PERMISSIONS.VALIDATE_AGENCY_OBJECTIVES,
    PERMISSIONS.MANAGE_FINANCIAL,
    PERMISSIONS.VIEW_FINANCIAL,
    PERMISSIONS.ADMIN_ACCESS,
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.MANAGE_SETTINGS,
    ...MENUS_ADMIN
  ]),
  [PROFILES.DGA]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.CREATE_ZONE_OBJECTIVES,
    PERMISSIONS.VALIDATE_ZONE_OBJECTIVES,
    PERMISSIONS.VIEW_FINANCIAL,
    ...MENUS_OPERATIONAL
  ]),
  [PROFILES.RESPONSABLE_ZONE]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.CREATE_AGENCY_OBJECTIVES,
    PERMISSIONS.VALIDATE_AGENCY_OBJECTIVES,
    PERMISSIONS.VIEW_FINANCIAL,
    ...MENUS_OPERATIONAL
  ]),
  [PROFILES.CHEF_AGENCE]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.CREATE_CAF_OBJECTIVES,
    PERMISSIONS.VIEW_FINANCIAL,
    ...MENUS_OPERATIONAL
  ]),
  [PROFILES.CAF]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_VUE360,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    ...MENUS_CAF
  ]),
  [PROFILES.FINANCES]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    PERMISSIONS.MANAGE_FINANCIAL,
    PERMISSIONS.VIEW_FINANCIAL,
    ...MENUS_OPERATIONAL
  ]),
  [PROFILES.EXPLOITATIONS]: uniquePermissions([
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_CLIENT,
    PERMISSIONS.VIEW_ZONES,
    PERMISSIONS.VIEW_AGENCIES,
    ...MENUS_OPERATIONAL
  ]),
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
  const normalized = normalizePermission(permission);
  return PROFILE_PERMISSIONS[profile].includes(normalized);
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
    const wanted = normalizePermission(permission);
    return normalizePermissions(profileData.permissions).includes(wanted);
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
    return this.hasPermission(PERMISSIONS.VIEW_VUE360);
  },

  canAccessMenu(permission) {
    return this.hasPermission(permission);
  },

  canAccessSection(section, subSection = null) {
    if (section === 'objectives') {
      if (subSection) {
        const perm = OBJECTIVE_SUB_PERMISSIONS[subSection];
        return perm ? this.hasPermission(perm) : false;
      }
      return this.hasPermission(PERMISSIONS.MENU_OBJECTIFS_VIEW)
        || this.hasPermission(PERMISSIONS.MENU_OBJECTIFS_ADD)
        || this.hasPermission(PERMISSIONS.MENU_OBJECTIFS_VALIDATE);
    }
    const perm = SECTION_PERMISSIONS[section];
    return perm ? this.hasPermission(perm) : false;
  },

  canAccessAny(permissions) {
    return permissions.some((permission) => this.hasPermission(permission));
  },

  dashboardSectionOrder() {
    return [
      'client',
      'comptes-ouverts',
      'collecte-epargne-a-vue',
      'portefeuille-risque',
      'new-deal',
      'money-transfers',
      'objectives',
      'management',
      'environments'
    ];
  },

  firstAllowedDashboardSection() {
    return this.dashboardSectionOrder().find((section) => this.canAccessSection(section)) || 'client';
  },

  hasDashboardMenuAccess() {
    return this.dashboardSectionOrder().some((section) => this.canAccessSection(section));
  },

  async refreshCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) {
      return null;
    }
    try {
      const axios = (await import('axios')).default;
      const response = await axios.get('/api/user');
      const user = response.data;
      localStorage.setItem('user', JSON.stringify(user));
      if (user?.profile?.code) {
        localStorage.setItem('userProfile', user.profile.code);
      }
      return user;
    } catch (error) {
      console.error('Impossible de rafraîchir le profil utilisateur:', error);
      return null;
    }
  },

  /** Page d'accueil après connexion : selon les menus cochés, pas le code profil. */
  getHomeRoute() {
    if (this.hasDashboardMenuAccess() || this.hasPermission(PERMISSIONS.VIEW_DASHBOARD)) {
      return '/dashboard';
    }
    if (this.canAccessSection('caf-overview')) {
      return '/vue360/caf';
    }
    if (this.canViewVue360()) {
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

