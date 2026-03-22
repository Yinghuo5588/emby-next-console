<template>
  <div>
    <LoadingState v-if="loading" compact />
    <ErrorState v-else-if="error" :message="error" @retry="$emit('retry')" />
    <n-empty v-else-if="!items || items.length === 0" description="系统正常运行中" />
    <div v-else>
      <NotificationCard v-for="n in items" :key="n.notification_id" :notification="n" @mark-read="(id) => $emit('markRead', id)" />
      <div v-if="hasMore" style="text-align:center;padding:12px">
        <n-button text :loading="loadingMore" @click="$emit('loadMore')">加载更多</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NEmpty, NButton } from 'naive-ui'
import NotificationCard from './NotificationCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'

defineProps<{ items: any[]; loading: boolean; error?: string | null; markingId: number | null; hasMore: boolean; loadingMore: boolean }>()
defineEmits<{ retry: []; markRead: [id: string]; loadMore: [] }>()
</script>
