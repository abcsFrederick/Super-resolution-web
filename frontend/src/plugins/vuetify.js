// import Vue from 'vue';
// import Vuetify from 'vuetify/lib/framework';
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'


// Vue.use(Vuetify);
const vuetify = createVuetify({
	components
})
export default vuetify;
