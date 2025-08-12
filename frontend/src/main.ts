import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

// 引入Vant组件库
import Vant from 'vant'
import 'vant/lib/index.css'

// 在桌面端使用时，可以引入桌面端适配
import '@vant/touch-emulator'

// 创建Vue应用实例
const app = createApp(App)

// 使用Vant组件库
app.use(Vant)

// 使用路由
app.use(router)

// 挂载应用
app.mount('#app')
