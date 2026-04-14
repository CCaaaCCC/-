import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './styles/theme.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { initTheme } from './composables/useTheme'
import { installRuntimeGuards } from './utils/runtimeGuards'

initTheme()
installRuntimeGuards()

const app = createApp(App)

app.config.errorHandler = (error, _instance, info) => {
  console.error('[vue:error]', info, error)
}

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app')
