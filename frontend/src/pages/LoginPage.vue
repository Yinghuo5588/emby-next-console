<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <svg width="48" height="48" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="8" fill="var(--brand)"/>
            <path d="M12 10L20 16L12 22V10Z" fill="white"/>
          </svg>
          <h1>Emby Next</h1>
        </div>
        <p class="subtitle">Admin Console</p>
      </div>
      
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="Enter username"
            required
            :disabled="loading"
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="Enter password"
            required
            :disabled="loading"
          />
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="loading">Logging in...</span>
          <span v-else>Login</span>
        </button>
      </form>
      
      <div class="login-footer">
        <p>© 2024 Emby Next Console. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    error.value = 'Please enter username and password'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await authStore.login(form.value.username, form.value.password)
    router.push('/')
  } catch (err: any) {
    error.value = err.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: var(--bg);
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: var(--surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2rem;
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.logo h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.subtitle {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text);
}

.form-group input {
  width: 100%;
}

.error-message {
  background: var(--danger-light);
  color: var(--danger);
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  text-align: center;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
}

.login-footer p {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin: 0;
}

@media (max-width: 768px) {
  .login-container {
    padding: 1.5rem;
  }
  
  .logo {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .logo h1 {
    font-size: 1.5rem;
  }
}
</style>