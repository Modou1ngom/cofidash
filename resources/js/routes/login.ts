import axios from 'axios';

export const store = {
  form: () => ({
    email: '',
    password: '',
    remember: false,
    processing: false,
    errors: {} as Record<string, string>,
    
    async submit() {
      this.processing = true;
      this.errors = {};
      
      try {
        const response = await axios.post('/api/login', {
          email: this.email,
          password: this.password,
          remember: this.remember
        });
        
        // Stocker les informations utilisateur
        localStorage.setItem('user', JSON.stringify(response.data.user));
        localStorage.setItem('token', response.data.token);
        if (response.data.user.profile) {
          localStorage.setItem('userProfile', response.data.user.profile.code);
        }
        
        // Rediriger vers le dashboard
        window.location.href = '/dashboard';
      } catch (error: any) {
        if (error.response?.status === 422) {
          this.errors = error.response.data.errors || {};
        } else {
          this.errors = {
            email: error.response?.data?.message || 'Erreur de connexion. Vérifiez vos identifiants.'
          };
        }
      } finally {
        this.processing = false;
      }
    }
  })
};
