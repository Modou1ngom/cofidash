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

    // Stocker les informations utilisateur
    localStorage.setItem('user', JSON.stringify(response.data.user));
    localStorage.setItem('token', response.data.token);
    if (response.data.user.profile) {
      localStorage.setItem('userProfile', response.data.user.profile.code);
    }

    // Rediriger vers le dashboard
    router.push('/dashboard');
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
  <div class="login-page relative min-h-screen w-full overflow-hidden" style="background-image: url('/im1.png'); background-size: cover; background-position: center; background-repeat: no-repeat;"> 
    <div class="login-panel-left absolute left-0 top-0 h-full w-1/3 min-w-[120px] rounded-br-[120px] overflow-hidden" style="background-image: url('/im2.png'); background-size: cover; background-position: center; background-repeat: no-repeat;"></div>

    <div class="relative z-20 flex min-h-screen min-w-0 w-full items-center justify-center p-4 sm:p-6 perspective-1000">
      <div class="login-card w-full max-w-3xl rounded-3xl bg-white/95 backdrop-blur-sm p-6 sm:p-10 card-3d transform-gpu transition-all duration-500 hover:scale-[1.02] hover:rotate-y-2">
        <div class="mb-6 flex flex-col items-start gap-4">
          <img src="/logo_Cofina.png" alt="Cofina" class="h-16 object-contain" onerror="this.src='/logo.png'" />
          <div>
            <h1 class="text-3xl font-semibold text-gray-900">Connectez-vous</h1>
            <p class="text-sm text-gray-500">
              Entrez votre email et votre mot de passe pour accéder à l'application.
            </p>
          </div>
        </div>

        <div
          v-if="status"
          class="mb-6 rounded-lg border border-green-200 bg-green-50/50 p-4 text-center text-sm font-medium text-green-700"
        >
          {{ status }}
        </div>

        <form @submit.prevent="handleSubmit" class="flex flex-col gap-6">
          <div class="grid gap-5">
            <div class="grid gap-2">
              <Label for="email" class="text-sm font-medium text-gray-700">Email</Label>
              <Input
                id="email"
                type="email"
                name="email"
                required
                autofocus
                :tabindex="1"
                autocomplete="email"
                placeholder="Entrer email"
                v-model="form.email"
                class="h-11 border-gray-200 input-3d transition-all duration-300 hover:shadow-lg hover:scale-[1.01] focus:scale-[1.02] focus:shadow-xl"
              />
              <InputError :message="errors.email" />
            </div>

            <div class="grid gap-2">
              <div class="flex items-center justify-between">
                <Label for="password" class="text-sm font-medium text-gray-700">Mot de passe</Label>
                <TextLink
                  v-if="canResetPassword"
                  :href="request()"
                  class="text-xs text-red-600 hover:text-red-700"
                  :tabindex="5"
                >
                  Mot de passe oublié?
                </TextLink>
              </div>
              <Input
                id="password"
                type="password"
                name="password"
                required
                :tabindex="2"
                autocomplete="current-password"
                placeholder="Password"
                v-model="form.password"
                class="h-11 border-gray-200 input-3d transition-all duration-300 hover:shadow-lg hover:scale-[1.01] focus:scale-[1.02] focus:shadow-xl"
              />
              <InputError :message="errors.password" />
            </div>

            <div class="flex items-center justify-between pt-1">
              <Label for="remember" class="flex cursor-pointer items-center space-x-2.5 text-sm text-gray-500">
                <Checkbox id="remember" name="remember" :tabindex="3" v-model="form.remember" />
                <span>Se souvenir de moi</span>
              </Label>
            </div>

            <div class="flex justify-end">
              <Button
                type="submit"
                class="h-10 rounded-md bg-red-600 px-6 text-white hover:bg-red-700 button-3d transform-gpu transition-all duration-300 hover:scale-105 hover:shadow-2xl active:scale-95"
                :tabindex="4"
                :disabled="processing"
                data-test="login-button"
              >
                <template v-if="!processing">
                  <LogIn class="mr-2 h-4 w-4" />
                </template>
                <LoaderCircle v-else class="mr-2 h-4 w-4 animate-spin" />
                {{ processing ? 'Connexion...' : 'Connexion' }}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.perspective-1000 {
  perspective: 1000px;
}

.card-3d {
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.6),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  transform-style: preserve-3d;
  animation: float 6s ease-in-out infinite;
}

.card-3d::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(0, 0, 0, 0.1));
  border-radius: 3xl;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s;
}

.card-3d:hover::before {
  opacity: 1;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotateX(0deg);
  }
  50% {
    transform: translateY(-10px) rotateX(2deg);
  }
}

.hover\:rotate-y-2:hover {
  transform: rotateY(2deg) translateY(-5px);
}

.transform-gpu {
  transform: translate3d(0, 0, 0);
  will-change: transform;
}

.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

.duration-500 {
  transition-duration: 500ms;
}

.hover\:scale-\[1\.02\]:hover {
  transform: scale(1.02);
}

.input-3d {
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-3d:focus {
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 0 0 3px rgba(220, 38, 38, 0.1),
    inset 0 1px 2px rgba(255, 255, 255, 0.9);
  transform: translateY(-2px) scale(1.02);
}

.input-3d:hover {
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.12),
    inset 0 1px 2px rgba(255, 255, 255, 0.85);
}

.button-3d {
  box-shadow: 
    0 4px 14px rgba(220, 38, 38, 0.4),
    0 2px 4px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.button-3d::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.button-3d:hover::before {
  left: 100%;
}

.button-3d:hover {
  box-shadow: 
    0 8px 20px rgba(220, 38, 38, 0.5),
    0 4px 8px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.button-3d:active {
  box-shadow: 
    0 2px 8px rgba(220, 38, 38, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
  .login-panel-left {
    width: 0;
    min-width: 0;
    display: none;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 16px;
  }
}
</style>
