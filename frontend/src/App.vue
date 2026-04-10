<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  // 从 localStorage 获取主题，默认为 dark
  const savedTheme = localStorage.getItem('theme') || 'dark'
  document.documentElement.setAttribute('data-theme', savedTheme)
})
</script>

<style>
/* 全局样式确保高度撑满 */
html, body {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
