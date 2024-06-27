// import Vue from 'vue';
// import Vuetify from 'vuetify/lib/framework';
import '@mdi/font/css/materialdesignicons.css'
import * as components from 'vuetify/components'
import * as labsComponents from 'vuetify/labs/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'


// Vue.use(Vuetify);
const vuetify = createVuetify({
	components: {
		...components,
		...labsComponents,
	},
	directives: directives
})
export default vuetify;
