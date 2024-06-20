import { createApp } from 'vue'
import { createStore } from 'vuex'

const store = createStore({
  state: {
    status: '',
    token: localStorage.getItem('token') || '',
    user : {}
  },
  mutations: {

  },
  actions: {

  },
  getters : {

  }
})

export default store;