import App from './App'

// #ifndef VUE3
import Vue from 'vue'
import './uni.promisify.adaptor'
Vue.config.productionTip = false
App.mpType = 'app'
const app = new Vue({
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
import { createSSRApp } from 'vue'
import Vant from 'vant';
import 'vant/lib/index.css';
import { themeMixin } from './pages/store/theme';
import { authMixin } from './utils/navigate';

export function createApp() {
  const app = createSSRApp(App)
  app.use(Vant);
  app.mixin(themeMixin);
  app.mixin(authMixin);
  return {
    app
  }
}
// #endif