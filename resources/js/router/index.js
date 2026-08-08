import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../pages/LoginPage.vue';
import { ProfileManager } from '../utils/profiles.js';

function resolveHomeRoute() {
  return ProfileManager.getHomeRoute();
}

function mustChangePassword() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return !!user.must_change_password;
  } catch {
    return false;
  }
}

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginPage
  },
  {
    path: '/login',
    name: 'login-alt',
    component: LoginPage
  },
  {
    path: '/change-password',
    name: 'change-password',
    component: () => import('../pages/ChangePasswordPage.vue'),
    meta: { requiresAuth: true, allowPasswordChange: true }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('../pages/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/vue360',
    component: () => import('../layouts/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: () => (
          ProfileManager.isCAF()
            ? { name: 'vue360-caf-overview' }
            : { name: 'vue360' }
        ),
      },
      {
        path: 'recherche',
        name: 'vue360',
        component: () => import('../pages/Vue360Page.vue'),
        meta: { keepAlive: true },
      },
      {
        path: 'clients/:id',
        name: 'vue360-client',
        component: () => import('../pages/Vue360ClientPage.vue'),
        meta: { keepAlive: false },
      },
      {
        path: 'caf',
        name: 'vue360-caf-overview',
        component: () => import('../pages/CafVueEnsemblePage.vue'),
        meta: { keepAlive: true },
      },
      {
        path: 'objectifs',
        name: 'vue360-caf-objectifs',
        component: () => import('../components/CafObjectivesSection.vue'),
        meta: { keepAlive: false },
      },
    ],
  },
  {
    path: '/admin/profiles',
    name: 'profile-management',
    component: () => import('../pages/ProfileManagementPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'user-management',
    component: () => import('../pages/UserManagementPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/objectives/add',
    name: 'add-objective',
    component: () => import('../pages/AddObjectivePage.vue'),
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Garde de navigation
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  const isAuthenticated = !!token;
  const needsPasswordChange = isAuthenticated && mustChangePassword();

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/');
    return;
  }

  if (needsPasswordChange && !to.meta.allowPasswordChange) {
    next({ name: 'change-password' });
    return;
  }

  if ((to.path === '/' || to.path === '/login') && isAuthenticated) {
    next(needsPasswordChange ? { name: 'change-password' } : resolveHomeRoute());
    return;
  }

  if (to.path === '/dashboard' && isAuthenticated && ProfileManager.isCAF()) {
    // Le CAF peut ouvrir Objectifs depuis le dashboard ; le reste redirige vers sa vue
    const section = sessionStorage.getItem('dashboardSection');
    if (section === 'objectives') {
      next('/vue360/objectifs');
    } else {
      next('/vue360/caf');
    }
    return;
  }

  if (to.path === '/dashboard' && isAuthenticated && ProfileManager.isCC()) {
    next('/vue360/recherche');
    return;
  }

  if (isAuthenticated && ProfileManager.isCAF() && to.path === '/vue360') {
    next('/vue360/caf');
    return;
  }

  if (isAuthenticated && ProfileManager.isCC() && to.path === '/vue360/caf') {
    next('/vue360/recherche');
    return;
  }

  next();
});

export default router;
