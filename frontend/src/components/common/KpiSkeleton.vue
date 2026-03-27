<template>
  <div class="kpi-grid">
    <div v-for="i in 4" :key="i" class="kpi-skel">
      <div class="skel-icon" />
      <div class="skel-body">
        <div class="skel-value" />
        <div class="skel-label" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.kpi-skel {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--surface);
  border-radius: 16px;
  padding: 1.1rem;
  border: 1px solid var(--border);
}
.skel-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  flex-shrink: 0;
}
.skel-body { flex: 1; }
.skel-value {
  height: 22px;
  width: 60%;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  margin-bottom: 6px;
}
.skel-label {
  height: 12px;
  width: 40%;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@media (max-width: 767px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
