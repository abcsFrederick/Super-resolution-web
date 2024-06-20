import { createApp } from 'vue'
import App from './App.vue'
import router from './router';
import store from './store';
import vuetify from './plugins/vuetify';
import api from './api'
// import * as Sentry from "@sentry/vue";
// import { BrowserTracing } from "@sentry/tracing";

const app = createApp(App)

app.config.productionTip = false
app.config.globalProperties.$api = api;

// Sentry.init({
//   Vue,
//   dsn: "https://be42f95d309045bdb7838e97bb4c081c@o1215375.ingest.sentry.io/6356417",
//   integrations: [
//     new BrowserTracing({
//       routingInstrumentation: Sentry.vueRouterInstrumentation(router),
//       tracingOrigins: ["localhost", "my-site-url.com", /^\//],
//     }),
//   ],
//   // Set tracesSampleRate to 1.0 to capture 100%
//   // of transactions for performance monitoring.
//   // We recommend adjusting this value in production
//   tracesSampleRate: 1.0,
// });

app.use(router)
app.use(vuetify)
app.use(store)
app.mount('#app')

