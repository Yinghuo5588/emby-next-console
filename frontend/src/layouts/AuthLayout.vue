<template>
  <div class="auth-layout">
    <div class="auth-background">
      <div class="gradient-circle gradient-1"></div>
      <div class="gradient-circle gradient-2"></div>
      <div class="gradient-circle gradient-3"></div>
    </div>
    <div class="auth-container">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg);
}

.auth-background {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.gradient-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.15;
}

.gradient-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, var(--brand), #8b5cf6);
  top: -200px;
  right: -100px;
}

.gradient-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #3b82f6, var(--brand));
  bottom: -150px;
  left: -100px;
}

.gradient-3 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #10b981, #3b82f6);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.auth-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 2rem;
}
</style>
