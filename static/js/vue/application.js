import { login_page, register_page } from "./components/auth.js"
import { common_components } from "./components/common.js"
import { dashboard } from "./components/dashboard.js"
import { tracker_logs } from "./components/view_logs.js"
import { add_tracker } from "./components/add_tracker.js"
import { add_logs } from "./components/add_logs.js"

/* ========================== APP Settings ========================== */
const routes = [
    {  
      path: '/', 
      component: common_components,
      children: [
          {name: 'home', path: '', component: dashboard},
          {name: 'add_tracker', path: 'tracker/add', component: add_tracker},
          {name: 'edit_tracker', path: 'tracker/:id/edit', component: add_tracker},
          {name: 'tracker', path: 'tracker/:id', component: tracker_logs},

          {name: 'edit_log', path: 'logs/edit/:tid/:lid', component: add_logs},
          {name: 'add_log', path: 'logs/add/:tid', component: add_logs},
      ]
  
  },
  { name: 'login', path: '/login', component: login_page },
  { name: 'register', path: '/register', component: register_page },
  { name: 'relogin', path: '/relogin', component: login_page },
  { name: 'logout', path: '/logout', component: login_page },
  //{ path: '/home', component: Bar }
]

const router = new VueRouter({
  routes, // short for `routes: routes`
  linkActiveClass: "active",
  linkExactActiveClass: "exact-active",
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = (sessionStorage.getItem("token") === null) ? false : true;
  if (!isAuthenticated) {
    if (to.name !== 'login' && to.name !== 'register'){ 
      next({ name: 'login' })
    } else next()
  }
  else next()
})

const app = new Vue({
  delimiters: ['${', '}'],
  data : {
      "message": "my first app"
  },
  router
}).$mount('#vapp')


$(window).resize(function() {
    if(window.chart == null){}
    else {
      window.chart.redraw();
    }
});