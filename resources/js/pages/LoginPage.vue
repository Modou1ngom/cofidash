<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import InputError from '@/components/InputError.vue';
import TextLink from '@/components/TextLink.vue';
import Button from '@/components/ui/button.vue';
import Checkbox from '@/components/ui/checkbox.vue';
import Input from '@/components/ui/input.vue';
import Label from '@/components/ui/label.vue';
import { store } from '@/routes/login';
import { ProfileManager } from '@/utils/profiles.js';
import { request } from '@/routes/password';
import LoaderCircle from '@/components/icons/LoaderCircle.vue';
import LogIn from '@/components/icons/LogIn.vue';
import axios from 'axios';

const props = withDefaults(defineProps<{
  status?: string;
  canResetPassword?: boolean;
  canRegister?: boolean;
}>(), {
  canResetPassword: true,
  canRegister: false
});

const router = useRouter();
const form = reactive(store.form());
const errors = ref<Record<string, string>>({});
const processing = ref(false);

const handleSubmit = async (e: Event) => {
  e.preventDefault();
  processing.value = true;
  errors.value = {};

  try {
    const response = await axios.post('/api/login', {
      email: form.email,
      password: form.password,
      remember: form.remember
    });

    localStorage.setItem('user', JSON.stringify(response.data.user));
    localStorage.setItem('token', response.data.token);
    if (response.data.user.profile) {
      localStorage.setItem('userProfile', response.data.user.profile.code);
    }

    router.push(ProfileManager.getHomeRoute());
  } catch (error: any) {
    if (error.response?.status === 422) {
      errors.value = error.response.data.errors || {};
    } else {
      errors.value = {
        email: error.response?.data?.message || 'Erreur de connexion. Vérifiez vos identifiants.'
      };
    }
  } finally {
    processing.value = false;
  }
};
</script>

<template>
  <div class="login-page">
    <aside class="login-brand" aria-label="Cofina">
      <img
        src="/logo-vue-360.jpeg"
        alt="Cofina — Compagnie Financière Africaine"
        class="brand-media"
      />
    </aside>

    <main class="login-main">
      <div class="login-form-shell">
        <header class="login-form-header">
          <img
            src="/logo.png"
            alt="Cofina"
            class="form-logo"
          />
          <h1>Connexion</h1>
          <p>Saisissez vos identifiants pour accéder à l’application.</p>
        </header>

        <div v-if="status" class="status-banner" role="status">
          {{ status }}
        </div>

        <form class="login-form" @submit.prevent="handleSubmit">
          <div class="field">
            <Label for="email">Adresse e-mail</Label>
            <Input
              id="email"
              type="email"
              name="email"
              required
              autofocus
              :tabindex="1"
              autocomplete="email"
              placeholder="prenom.nom@cofina.sn"
              v-model="form.email"
              className="login-input"
            />
            <InputError :message="errors.email" />
          </div>

          <div class="field">
            <div class="field-label-row">
              <Label for="password">Mot de passe</Label>
              <TextLink
                v-if="canResetPassword"
                :href="request()"
                className="forgot-link"
                :tabindex="5"
              >
                Mot de passe oublié ?
              </TextLink>
            </div>
            <Input
              id="password"
              type="password"
              name="password"
              required
              :tabindex="2"
              autocomplete="current-password"
              placeholder="••••••••"
              v-model="form.password"
              className="login-input"
            />
            <InputError :message="errors.password" />
          </div>

          <Label for="remember" class="remember-row">
            <Checkbox id="remember" name="remember" :tabindex="3" v-model="form.remember" />
            <span>Se souvenir de moi</span>
          </Label>

          <Button
            type="submit"
            className="login-submit"
            :tabindex="4"
            :disabled="processing"
            data-test="login-button"
          >
            <LoaderCircle v-if="processing" class="submit-icon animate-spin" />
            <LogIn v-else class="submit-icon" />
            {{ processing ? 'Connexion en cours…' : 'Se connecter' }}
          </Button>
        </form>

        <p class="login-footer">Accès réservé aux collaborateurs autorisés.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-page {
  --brand: #1A4D3A;
  --brand-deep: #12382b;
  --accent: #c41e3a;
  --text: #111827;
  --muted: #6b7280;
  --border: #e5e7eb;

  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  width: 100%;
  background: #fff;
  color: var(--text);
}

.login-brand {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  background: #c41e3a;
}

.brand-media {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
}

.login-main {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  background: #fff;
}

.login-form-shell {
  width: 100%;
  max-width: 400px;
}

.login-form-header {
  margin-bottom: 32px;
}

.form-logo {
  display: block;
  height: 48px;
  width: auto;
  object-fit: contain;
  margin-bottom: 28px;
}

.login-form-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text);
}

.login-form-header p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}

.status-banner {
  margin-bottom: 18px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #a7f3d0;
  background: #ecfdf5;
  color: #065f46;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: grid;
  gap: 8px;
}

.field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.login-form :deep(label) {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.forgot-link {
  font-size: 12px !important;
  font-weight: 600 !important;
  color: var(--accent) !important;
  text-decoration: none !important;
}

.forgot-link:hover {
  text-decoration: underline !important;
}

.login-form :deep(.login-input) {
  height: 44px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: none;
  font-size: 14px;
}

.login-form :deep(.login-input:focus),
.login-form :deep(.login-input:focus-visible) {
  border-color: #8fb3a1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.12);
}

.remember-row {
  display: inline-flex !important;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: var(--muted) !important;
  font-weight: 500 !important;
  font-size: 13px !important;
}

.login-form :deep(.login-submit) {
  margin-top: 4px;
  width: 100%;
  height: 46px;
  border-radius: 8px;
  background: var(--brand);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  box-shadow: none;
}

.login-form :deep(.login-submit:hover:not(:disabled)) {
  background: var(--brand-deep);
}

.submit-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
}

.login-footer {
  margin: 28px 0 0;
  font-size: 12px;
  color: #9ca3af;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .login-brand {
    min-height: 220px;
  }

  .login-main {
    padding: 32px 20px 48px;
    align-items: flex-start;
  }
}
</style>
