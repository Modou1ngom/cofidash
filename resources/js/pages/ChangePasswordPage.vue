<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import InputError from '@/components/InputError.vue';
import Button from '@/components/ui/button.vue';
import Input from '@/components/ui/input.vue';
import Label from '@/components/ui/label.vue';
import { ProfileManager } from '@/utils/profiles.js';
import LoaderCircle from '@/components/icons/LoaderCircle.vue';
import axios from 'axios';

const router = useRouter();
const form = reactive({
  current_password: '',
  password: '',
  password_confirmation: '',
});
const errors = ref<Record<string, string>>({});
const processing = ref(false);
const isForced = ref(false);

onMounted(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    isForced.value = !!user.must_change_password;
  } catch {
    isForced.value = false;
  }

  if (!localStorage.getItem('token')) {
    router.replace('/');
  }
});

const handleSubmit = async (e: Event) => {
  e.preventDefault();
  processing.value = true;
  errors.value = {};

  try {
    const response = await axios.post('/api/change-password', {
      current_password: form.current_password,
      password: form.password,
      password_confirmation: form.password_confirmation,
    });

    localStorage.setItem('user', JSON.stringify(response.data.user));
    if (response.data.user.profile) {
      localStorage.setItem('userProfile', response.data.user.profile.code);
    }

    router.push(ProfileManager.getHomeRoute());
  } catch (error: any) {
    if (error.response?.status === 422) {
      const raw = error.response.data.errors || {};
      const normalized: Record<string, string> = {};
      for (const [key, value] of Object.entries(raw)) {
        normalized[key] = Array.isArray(value) ? (value[0] as string) : String(value);
      }
      errors.value = normalized;
    } else {
      errors.value = {
        password: error.response?.data?.message || 'Impossible de modifier le mot de passe.',
      };
    }
  } finally {
    processing.value = false;
  }
};

const handleLogout = async () => {
  try {
    await axios.post('/api/logout');
  } catch {
    // ignore
  }
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('userProfile');
  router.replace('/');
};
</script>

<template>
  <div class="change-password-page">
    <aside class="brand-panel" aria-label="Cofina">
      <img
        src="/logo-vue-360.jpeg"
        alt="Cofina — Compagnie Financière Africaine"
        class="brand-media"
      />
    </aside>

    <main class="form-panel">
      <div class="form-shell">
        <header class="form-header">
          <img src="/logo.png" alt="Cofina" class="form-logo" />
          <h1>{{ isForced ? 'Première connexion' : 'Changer le mot de passe' }}</h1>
          <p v-if="isForced">
            Pour des raisons de sécurité, vous devez définir un nouveau mot de passe avant d’accéder à l’application.
          </p>
          <p v-else>
            Saisissez votre mot de passe actuel, puis choisissez un nouveau mot de passe.
          </p>
        </header>

        <form class="password-form" @submit.prevent="handleSubmit">
          <div class="field">
            <Label for="current_password">Mot de passe actuel</Label>
            <Input
              id="current_password"
              type="password"
              required
              autofocus
              autocomplete="current-password"
              placeholder="••••••••"
              v-model="form.current_password"
              className="form-input"
            />
            <InputError :message="errors.current_password" />
          </div>

          <div class="field">
            <Label for="password">Nouveau mot de passe</Label>
            <Input
              id="password"
              type="password"
              required
              autocomplete="new-password"
              placeholder="Au moins 8 caractères"
              v-model="form.password"
              className="form-input"
            />
            <InputError :message="errors.password" />
          </div>

          <div class="field">
            <Label for="password_confirmation">Confirmer le mot de passe</Label>
            <Input
              id="password_confirmation"
              type="password"
              required
              autocomplete="new-password"
              placeholder="••••••••"
              v-model="form.password_confirmation"
              className="form-input"
            />
            <InputError :message="errors.password_confirmation" />
          </div>

          <Button
            type="submit"
            className="submit-btn"
            :disabled="processing"
          >
            <LoaderCircle v-if="processing" class="submit-icon animate-spin" />
            {{ processing ? 'Enregistrement…' : 'Enregistrer le mot de passe' }}
          </Button>
        </form>

        <button type="button" class="logout-link" @click="handleLogout">
          Se déconnecter
        </button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.change-password-page {
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

.brand-panel {
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

.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  background: #fff;
}

.form-shell {
  width: 100%;
  max-width: 400px;
}

.form-header {
  margin-bottom: 32px;
}

.form-logo {
  display: block;
  height: 48px;
  width: auto;
  object-fit: contain;
  margin-bottom: 28px;
}

.form-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text);
}

.form-header p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field {
  display: grid;
  gap: 8px;
}

.password-form :deep(label) {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.password-form :deep(.form-input) {
  height: 44px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: none;
  font-size: 14px;
}

.password-form :deep(.form-input:focus),
.password-form :deep(.form-input:focus-visible) {
  border-color: #8fb3a1;
  outline: none;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.12);
}

.password-form :deep(.submit-btn) {
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

.password-form :deep(.submit-btn:hover:not(:disabled)) {
  background: var(--brand-deep);
}

.submit-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
}

.logout-link {
  display: block;
  margin: 24px auto 0;
  padding: 0;
  border: none;
  background: none;
  color: var(--muted);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.logout-link:hover {
  color: var(--accent);
}

@media (max-width: 900px) {
  .change-password-page {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    min-height: 220px;
  }

  .form-panel {
    padding: 32px 20px 48px;
    align-items: flex-start;
  }
}
</style>
