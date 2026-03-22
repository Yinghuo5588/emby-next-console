import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import router from './router'
import App from './App.vue'
import { useUiStore } from './stores/ui'
import './styles/global.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(naive)
app.use(router)

// 初始化 UI（主题 + 移动端检测）
const uiStore = useUiStore()
uiStore.init()

app.mount('#app')
