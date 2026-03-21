<template>
 <div class="layout">
 <AppSidebar />
 <div class="main">
 <AppHeader />
 <div class="content">
 <slot />
 </div>
 </div>
 </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppHeader from '@/components/common/AppHeader.vue'
import { useNotificationsStore } from '@/stores/notifications'
import { onMounted } from 'vue'

const notif = useNotificationsStore()
onMounted(() => notif.fetchUnreadCount())
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.content { flex: 1; padding: 24px; overflow-y: auto; }
</style>