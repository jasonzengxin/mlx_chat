<template>
  <div class="usage-stats">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ summary.total_requests }}</div>
        <div class="stat-label">Total Requests</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(summary.total_input_tokens) }}</div>
        <div class="stat-label">Input Tokens</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(summary.total_output_tokens) }}</div>
        <div class="stat-label">Output Tokens</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatDuration(summary.total_time_ms) }}</div>
        <div class="stat-label">Total Time</div>
      </div>
    </div>

    <div class="period-control">
      <label>Period</label>
      <select v-model="period" class="settings-select" @change="loadUsage">
        <option :value="null">All Time</option>
        <option v-for="p in recentMonths" :key="p" :value="p">{{ formatPeriod(p) }}</option>
      </select>
    </div>

    <div v-if="loading" class="loading-text">Loading...</div>
    <div v-if="error" class="error-msg">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsage, type UsageSummary } from '@/api/settings'

const loading = ref(false)
const error = ref('')
const period = ref<string | null>(null)

const summary = ref<UsageSummary>({
  api_key_id: '',
  period: 'all',
  total_requests: 0,
  total_input_tokens: 0,
  total_output_tokens: 0,
  total_time_ms: 0,
})

function recentMonths(): string[] {
  const months: string[] = []
  const now = new Date()
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}

function formatPeriod(p: string): string {
  const [y, m] = p.split('-')
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${names[parseInt(m) - 1]} ${y}`
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function formatDuration(ms: number): string {
  if (ms >= 3_600_000) return `${(ms / 3_600_000).toFixed(1)}h`
  if (ms >= 60_000) return `${(ms / 60_000).toFixed(1)}m`
  if (ms >= 1_000) return `${(ms / 1_000).toFixed(1)}s`
  return `${ms}ms`
}

async function loadUsage() {
  loading.value = true
  error.value = ''
  try {
    summary.value = await getUsage(period.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load usage'
  } finally {
    loading.value = false
  }
}

onMounted(loadUsage)
</script>

<style scoped>
.usage-stats {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.stat-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.period-control {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.period-control label {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.settings-select {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-primary);
  padding: 0.4rem 0.6rem;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  outline: none;
  cursor: pointer;
}

.loading-text,
.error-msg {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.error-msg {
  color: var(--error);
}
</style>
