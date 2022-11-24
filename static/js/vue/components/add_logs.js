import { get_tracker_data } from "./common.js"
import { get_log_data } from "./common.js"

export const add_logs = {
    template: `
    <div id="add_logs">
        <div class="col col-11">
            <div class="row justify-content-md-center">
                <div class="col-md-auto">                    
                    <h2 class="page-head">
                        {{title}}
                    </h2>
                </div>                
            </div>

            <div v-if="errors.length" class="alert alert-danger alert-dismissible fade show highest-index" role="alert">
                <h4 class="alert-heading">Vaidation Error</h4>
                <p v-for="err in errors">{{err}}</p>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>

            <div class="row justify-content-md-center">
                <div class="col-md-6">
                    <form id="app" @submit="checkForm" method="post" />
                        <div class="form-group">
                            <label for="timestamp">Timestamp</label>
                            <input id="timestamp" class="form-control" v-model="timestamp" name="timestamp" required type="text">
                            <small class="form-text text-muted">Current timestamp, you can change it from the dropdown</small>
                        </div>
                        <div class="form-group" v-if="tracker.type!='ms'">
                            <label v-if="tracker.type=='integer'" for="lvalue">Numerical Value (Integral)</label>
                            <label v-if="tracker.type=='float'" for="lvalue">Numerical Value (Fractional)</label>
                            <label v-if="tracker.type=='timerange'" for="lvalue">Time Range</label>
                            <input id="lvalue" @focus="onFocus()" name="lvalue" v-model="lvalue" class="form-control" required minlength="1" type="text">
                            <small class="form-text text-muted">The value you want to log in {{tracker.type}} format.</small> 
                        </div>            
                        <div class="form-group" v-if="tracker.type=='ms'">
                            <label for="divchoices">Select Choice(s):</label>
                            <div id="divchoices" v-for="item in tracker.choices">
                                <input id="choice" :id="item.id" type="checkbox" v-model="lchoices" v-bind:value="item.id" class="form-check-input" />
                                <label class="form-check-label" for="choice" :for="item.id"> {{item.value}}</label><br/>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="lnote">Notes</label> 
                            <textarea class="form-control" id="lnote" placeholder="Anything you wanna say about the information you are logging." v-model="lnote" name="lnote" maxlength="255"></textarea>
                        </div>
                        <div class="form-group">
                            <button type="submit" @click="checkForm" name="submit" class="form-control btn btn-primary">Submit</button>                            
                        </div>            
                    </form>
                </div>
            </div>
        </div>
    </div>`,

    data: function(){
        return {
            title: "Log Value",
            tid: this.$route.params.tid,
            tracker: {},

            lvalue: null,
            lchoices: [],
            lnote: "",

            errors: [],

            elid: null,
            timestamp: new Date().toLocaleString(),
            tstart: "",
            tend: ""
        }
    },

    methods: {
        checkForm: function(){
            this.errors.splice(0)

            if(this.tracker.type == 'ms'){
                if(this.lchoices.length <= 0){
                    this.errors.push("Choices are required")
                }
            } else {
                if(!this.lvalue){
                    this.errors.push("Value is required")
                }
            }
            
            if(!this.errors.length){
                this.submitForm()
            }

        },

        submitForm: async function(){
            let token = sessionStorage.getItem("token")
            let api_url = `/api/tracker/${this.tid}/logs`
            let api_method = 'POST'
            let value = this.lvalue            
            
            if(this.tracker.type == 'ms'){
                value = this.lchoices
            }

            let body = {
                "value": value,
                "note": this.lnote
            }

            if(this.elid != null){
                api_url = `/api/tracker/${this.tid}/logs/${this.elid}`
                api_method = 'PATCH'
                body = {
                    "value": value,
                    "note": this.lnote,
                    "timestamp": this.timestamp
                }
            }
            
            await fetch(api_url, {
                method: api_method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'                    
                },
                body: JSON.stringify(body)
            })
            .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
            .then(({response, data}) => {
                if(!response.ok){
                    if(data.error != null){
                        this.errors.push(data.error)
                        throw new Error(`Error ${response.status}: ${data.error}`)
                    } else if (data.message != null) {
                        this.errors.push(data.message.value)
                        throw new Error(`Error ${response.status}: ${data.message.value}`)
                    } else {
                        this.errors.push(data.msg)
                        throw new Error(`Error ${response.status}: ${data.msg}`)
                    }
                }                
                toastr.success(data.msg, this.title)
                this.$router.push({name: 'tracker', params: {id: this.tid}})
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

        edit_mode: async function(id){
            this.elid = id
            console.log(`Edit mode: Log ID ${this.elid}`)
            
            let ldata = await get_log_data(this.tid, this.elid)
            this.title = `Edit Log`
            this.lvalue = ldata.value
            this.lnote = ldata.note
            this.timestamp = ldata.timestamp       
            
            if(this.tracker.type == 'ms'){
                for(let item of ldata.value){
                    this.lchoices.push(item.choice_id)
                }
            } else if (this.tracker.type == "timerange"){
                this.tstart = ldata.start
                this.tend = ldata.end                
            }
            toastr.info(`Editing log with ID ${id}`, 'Edit Log')                        
        },

        onFocus: function() {
            var vm = this;            
            if(this.tracker.type == "timerange"){                
                $('input[name="lvalue"]').daterangepicker({
                    timePicker: true,
                    startDate: moment().startOf('hour'),
                    endDate: moment().startOf('hour').add(32, 'hour'),
                    ranges: {
                        'Today': [moment(), moment()],
                        'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                        'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                        'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                        'This Month': [moment().startOf('month'), moment().endOf('month')],
                        'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
                     },
                    locale: {
                    format: 'M/DD/YYYY hh:mm A'
                    }
                }, function(start, end, label) {
                    vm.lvalue = start.format('M/DD/YYYY hh:mm A') + ' - ' + end.format('M/DD/YYYY hh:mm A');
                });
            }
          }
    },
    

    mounted: async function(){
        if(this.$route.params.lid != null){
            await this.edit_mode(this.$route.params.lid)
        }        
    },


    created: function() {
        get_tracker_data(this.tid).then(data => {this.tracker = data}).catch(e=>console.log(e))

        this.$watch(
          () => this.$route.params,
          async function (toParams, previousParams) {
            console.log(toParams, previousParams)
            if(this.$route.params.lid != null){
                console.log("Log ID changed from " + previousParams.lid + " to " + toParams.lid)
                await this.edit_mode(this.$route.params.lid)
            }
          }
        )
    },


}