<template>
  <div class="settings-view">
    <h1>设置</h1>
    <div class="section">
      <h2>API Keys</h2>
      <ApiKeyList />
    </div>
  </div>
</template>

<script setup lang="ts">
import ApiKeyList from '@/components/ApiKeyList.vue'
</script>

<style scoped>
.settings-view {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.section {
  margin-top: 2rem;
}
</style>