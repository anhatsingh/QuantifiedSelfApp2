export const login_page = {
    data: () => ({
        email: null,
        password: null,
        isLoading: false,
        isError: false,
        errorMsg: null
      }),
    
    mounted: function(){
        if(this.$router.currentRoute.name == "logout"){
            sessionStorage.clear();
            this.$router.push({name: "login"})
        }else if(this.$router.currentRoute.name == "relogin"){
            sessionStorage.clear();
        }
    },

    methods: {
        authenticate: function() {
            fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({"email": this.email, "password": this.password})
            })
            .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
            .then(({response, data}) => {
                if(!response.ok){                    
                    throw new Error(`Error ${response.status}: ${data.msg}`)
                } else {
                    toastr.success('Authentication Successful', 'Login')
                    sessionStorage.setItem("username", data.name)
                    sessionStorage.setItem("token", data.token)
                    this.$router.push({name:"home"})
                }
            })
            .catch(error => {
                toastr.error(error.message, 'Error')
            })
        }
    },

    template: `
    <div id="login_page">
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
            <div class="container-fluid">
                <router-link class="navbar-brand" :to="{name: 'home'}">Quantified Self App v2</router-link>
            </div>
        </nav>
        <div class="container">      
            <div class="row overflow-auto">      
                <div class="col col-1"></div>
                <div class="col col-11">
                    <div class="col col-11 page-top-box">
                        <div class="row justify-content-md-center">
                            <div class="col-md-6 login-form">
                                <div class="row justify-content-md-center">
                                    <div class="col-md-auto">                    
                                        <h2 class="page-head">
                                            Login - Quantified Self App v2<hr>
                                        </h2>
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label for="email">Email Address</label>
                                    <input class="form-control" v-model="email" placeholder="test@test.com" id="email" name="email" required type="text">
                                </div>
                                <div class="form-group">
                                    <label for="password">Password</label>
                                    <input class="form-control" placeholder="*****" id="password" v-model="password" required type="password">
                                </div>

                                <div class="form-group">
                                    <button class="form-control" v-on:click="authenticate">Submit</button>
                                </div>
                                <div>
                                    Don't have an account? <router-link :to="{name:'register'}">Register Here</router-link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>    
                <div class="row">
                    <div class="col-12" style="min-height:100px;"></div>
                </div>
            </div>
        </div>
        <footer class="footer mt-auto py-3 bg-light fixed-bottom">
            <div class="container">
            <span class="text-muted">Designed by Anhat Singh</span>
            </div>
        </footer>
    </div>`
}





export const register_page = {
    data: () => ({
        name: null,
        email: null,
        password: null
      }),
    
    mounted: function(){
        if(sessionStorage.getItem('token') != null){
            //this.$router.push({name:"home"})
        }
    },

    methods: {
    registerUser: async function() {
        await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({"name": this.name, "email": this.email, "password": this.password})
        })
        .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
        .then(({response, data}) => {
            if(!response.ok){                    
                throw new Error(`Error ${response.status}: ${data.msg}`)
            } else {
                toastr.success(data.msg, "Register")
                this.$router.push({name:"login"})
            }
        })
        .catch(error => {
            toastr.error(error.message, 'Error')
        })
    }
    },

    template: `
    <div id="register_page">
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
            <div class="container-fluid">
                <router-link class="navbar-brand" :to="{name: 'home'}">Quantified Self App v2</router-link>
            </div>
        </nav>
        <div class="container">      
            <div class="row overflow-auto">      
                <div class="col col-1"></div>
                <div class="col col-11">
                    <div class="col col-11 page-top-box">
                        <div class="row justify-content-md-center">
                            <div class="col-md-6 login-form">
                                <div class="row justify-content-md-center">
                                    <div class="col-md-auto">                    
                                        <h2 class="page-head">
                                            Sign Up!<hr>
                                        </h2>
                                    </div>
                                </div>

                                <div class="form-group">
                                    <label for="name">Full Name</label>
                                    <input class="form-control" placeholder="Anhat Singh" id="name" v-model="name" required type="text">
                                </div>
                                <div class="form-group">
                                    <label for="email">Email Address</label>
                                    <input class="form-control" placeholder="test@test.com" id="email" v-model="email" required type="text">
                                </div>

                                <div class="form-group">
                                    <label for="password">Password</label>
                                    <input class="form-control" placeholder="*********" id="password" v-model="password" required type="password">
                                </div>

                                <div class="form-group">
                                    <button class="form-control" v-on:click="registerUser">Sign-Up</button>
                                </div>
                                <div>
                                    Already Registered? <router-link :to="{name:'login'}">Login Now!</router-link>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>    
                <div class="row">
                    <div class="col-12" style="min-height:100px;"></div>
                </div>
            </div>
        </div>
        <footer class="footer mt-auto py-3 bg-light fixed-bottom">
            <div class="container">
            <span class="text-muted">Designed by Anhat Singh</span>
            </div>
        </footer>
    </div>`
}