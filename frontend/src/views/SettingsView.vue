<template>
  <div class="settings-view">
    <header class="settings-header">
      <router-link to="/" class="back-link">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        <span>Back to Chat</span>
      </router-link>
      <h1>Settings</h1>
    </header>

    <div class="settings-content">
      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <div class="section-title">
            <h2>API Keys</h2>
            <p>Manage your API keys for accessing the MLX Chat backend.</p>
          </div>
        </div>
        <ApiKeyList />
      </section>

      <section class="settings-section">
        <div class="section-header">
          <div class="section-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          </div>
          <div class="section-title">
            <h2>Appearance</h2>
            <p>Customize how MLX Chat looks on your device.</p>
          </div>
        </div>
        <div class="appearance-options">
          <div class="option-item">
            <span>Theme</span>
            <select v-model="theme" class="settings-select">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import ApiKeyList from '@/components/ApiKeyList.vue'

const theme = ref(localStorage.getItem('theme') || 'dark')

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
})

watch(theme, (newTheme) => {
  localStorage.setItem('theme', newTheme)
  document.documentElement.setAttribute('data-theme', newTheme)
})
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.settings-header {
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem 1.5rem 2rem;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--accent);
}

.settings-header h1 {
  font-size: 2rem;
  font-weight: 700;
}

.settings-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 1.5rem 4rem;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  gap: 1rem;
}

.section-icon {
  width: 40px;
  height: 40px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}

.section-title h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.section-title p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.appearance-options {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
}

.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-select {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
}

.settings-select:focus {
  border-color: var(--accent);
}
</style>
