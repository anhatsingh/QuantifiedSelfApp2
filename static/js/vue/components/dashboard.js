import { export_data } from "./common.js"

Vue.component('dtracker', {
    props: ['dataObj', "dex"],
    template: `
        <div class="col-sm-4">
            <div class="card" style="width: 20rem;min-height:250px;margin:10px;">
                <h5 class="card-header d-flex justify-content-center">
                    <router-link :to="{name: 'tracker', params: {id: dataObj.id}}">{{dataObj.name}}</router-link>
                    <!--<a href="#">{{dataObj.name}}<i class="fa fa-regular fa-info icon-right"></i></a>-->
                </h5>
                <div class="card-body">
                    <h5 class="card-title"></h5>      
                    <p class="card-text text-justify">{{dataObj.description}}</p>                            
                </div>
                <div class="text-center card-footer">
                    <router-link type="button card-link" class="btn btn-outline-primary btn-sm" :to="{name: 'add_log', params: {tid: dataObj.id}}" tag="button">Log Value</router-link>
                    <router-link type="button card-link" class="btn btn-outline-success btn-sm" :to="{name: 'tracker', params: {id: dataObj.id}}" tag="button">Show Logs</router-link>
                    <div class="btn-group" type="button card-link" role="group">
                        <button id="btnGroupDrop1" type="button" class="btn btn-outline-secondary btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            More
                        </button>
                        <div class="dropdown-menu" aria-labelledby="btnGroupDrop1">
                            <router-link class="dropdown-item" :to="{name: 'edit_tracker', params: {id: dataObj.id}}">Edit</router-link>
                            <a class="dropdown-item" @click="$emit('delete', dex)">Delete Tracker</a>
                            <a class="dropdown-item" @click="$emit('export_pdf', dex)">Export as PDF</a>
                            <a class="dropdown-item" @click="$emit('export_csv', dex)">Export as CSV</a>
                        </div>
                    </div>

                    
                </div>
            </div>
        </div>`
})

export const dashboard = {    
    template:`
        <div class="col col-10">
            <div class="row justify-content-md-center">
                <div class="col-md-auto">
                    <h2 class="page-head">
                        Hi, {{user}}
                    </h2>
                </div>
            </div>

            <div class="row">
                <dtracker v-for="(tracker, index) in tracker_data" @delete="deleteTracker" @export_pdf="exportTrackerData_asPDF" @export_csv="exportTrackerData_asCSV" :dataObj="tracker" :dex="index" :key="tracker.id"></dtracker>
            </div>
        </div>
    `,
    data: function(){
        return {
            tracker_data: null,
            user: sessionStorage.getItem("username")
        }
    },
    
    methods: {
        deleteTracker: async function(arr_dex){
            let token = sessionStorage.getItem("token")
            await fetch(`/api/tracker/${this.tracker_data[arr_dex].id}`, {
                method: 'DELETE',
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
                    this.tracker_data.splice(arr_dex, 1);
                    toastr.success(data.msg, 'Delete Tracker')
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
        },

        exportTrackerData_asPDF: async function(index){
            export_data(this.tracker_data[index].id, "pdf")
        },

        exportTrackerData_asCSV: async function(index){
            export_data(this.tracker_data[index].id, "csv")
        }
    },


    mounted: async function(){
        let token = sessionStorage.getItem("token")
        await fetch('/api/tracker', {
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
            }
            this.tracker_data = data
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
}