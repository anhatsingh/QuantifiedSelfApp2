export const common_components = {
    template: `
    <div id="body">
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
            <div class="container-fluid">
                <router-link class="navbar-brand" :to="{name: 'home'}">Quantified Self App v2</router-link>
                <!--For mobile navigation-->
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbarSupportedContent">
                    <div class="col-9"></div>
                    <ul class="navbar-nav">
                        <li class="nav-item" v-for="button in navbuttons" v-bind:key="button.link">
                            <router-link class="nav-link" aria-current="page" :to="button.link">{{button.name}}</router-link>
                        </li>
                    </ul>

                </div>
            </div>
        </nav>


        <div id="page">
            <div class="container">      
                <div class="row overflow-auto">      
                    <div class="col col-1"></div>
                    <div class="col col-11">
                        <router-view></router-view>
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
    </div>`,
    data: function() {
            return {
                navbuttons: [
                    {name: "Home", link: "/"},
                    {name: "Add Tracker", link: "/tracker/add"},
                    {name: "logout", link: "/logout"}
                ]
            }
        },
    beforeCreate: function(){
        if(sessionStorage.getItem("token") === null){
            this.$router.push({name:"login"})
        }
    }
}



export let get_tracker_data = async function(id){
    console.log(`Getting data of Tracker with ID ${id}`)
    let token = sessionStorage.getItem("token")
    let final_data = null
    await fetch(`/api/tracker/${id}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        
    })
    .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
    .then(({response, data}) => {
        if(!response.ok){
            throw new Error(`Error ${response.status}: ${data.msg}`)
        } else {            
            final_data = data
        }
    })
    .catch(error => {
        if(error.message.includes("Token has expired")){
            toastr.error("Re-login required, token has expired", 'Error')
            this.$router.push("/relogin")
        }
        toastr.error(error.message, 'Error')
        //console.log(error)
    })
    
    return final_data
}


export let get_log_data = async function(tid, lid){
    console.log(`Getting data of Log with ID ${lid} under Tracker with ID ${tid}`)
    let token = sessionStorage.getItem("token")
    let final_data = null
    await fetch(`/api/tracker/${tid}/logs/${lid}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        
    })
    .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
    .then(({response, data}) => {
        if(!response.ok){
            throw new Error(`Error ${response.status}: ${data.msg}`)
        } else {            
            final_data = data
        }
    })
    .catch(error => {
        if(error.message.includes("Token has expired")){
            toastr.error("Re-login required, token has expired", 'Error')
            this.$router.push("/relogin")
        }
        toastr.error(error.message, 'Error')
        //console.log(error)
    })
    
    return final_data
}


export let export_data = async function(id, type){
    console.log(`Exporting data of Tracker with ID ${id} as ${type}`)
    let token = sessionStorage.getItem("token")
    await fetch(`/api/export/tracker/${id}/${type}`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        
    })
    .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
    .then(({response, data}) => {
        if(!response.ok){
            throw new Error(`Error ${response.status}: ${data.msg}`)
        } else {            
            toastr.info(data.msg, "Export Request")
        }
    })
    .catch(error => {
        if(error.message.includes("Token has expired")){
            toastr.error("Re-login required, token has expired", 'Error')
            this.$router.push("/relogin")
        }
        toastr.error(error.message, 'Error')
        //console.log(error)
    })
}