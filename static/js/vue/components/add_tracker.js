import { get_tracker_data } from "./common.js"

export const add_tracker = {
    template: `
    <div id="add_tracker">
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
                            <label for="atname">Name</label>
                            <input id="atname" class="form-control" v-model="atname" name="atname" aria-describedby="trackerNameHelp" required minlength="5" maxlength="55" type="text" />     
                            <small id="trackerNameHelp" class="form-text text-muted">This is the name of the tracker, you are gonna track this everyday :P</small>
                        </div>
                        <div class="form-group">
                            <label for="atdescription">Description</label>
                            <textarea id="atdescription" v-model="atdescription" name="atdescription" class="form-control" aria-describedby="trackerDescriptionHelp" maxlength="255" type="text"></textarea>
                            <small id="trackerDescriptionHelp" class="form-text text-muted">Description of the tracker. Don't worry, no one is gonna judge your grammar ;)</small>
                        </div>
                        <div class="form-group">
                            <label for="attype">Tracker Type</label>
                            <select class="form-control" v-model="attype" name="attype" @change="activate_tagify" required>
                                <option value="ms">Multiple-Choice</option>
                                <option value="integer">Integer</option>
                                <option value="float">Float</option>
                                <option value="timerange">Time Range</option>
                            </select>
                            <small v-if="etid" id="trackerDescriptionHelp" class="form-text text-muted"><p style="color:red;">WARNING! Changing this will delete all the logged items of this tracker</p></small>
                        </div>
                        <div class="form-group" v-if="attype=='ms'">
                            <label for="atchoices">Choices</label>
                            <textarea @change="on_tagify_change" name="atchoices" class="form-control" id="atchoices" aria-describedby="trackerChoiceHelp"></textarea>
                            <small id="trackerChoiceHelp" class="form-text text-muted">Type the choices of tracker here (comma separated)</small>
                            <small v-if="etid" id="trackerDescriptionHelp" class="form-text text-muted"><p style="color:red;">WARNING! Deleting choices will also delete their logged data</p></small>
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
            title: "Add Tracker",
            atname: null,
            atdescription: "",
            attype: null,
            atchoices: [],
            processed_choices: [],

            errors: [],

            etid: null,
            ochoices: [],            
        }
    },

    methods: {
        checkForm: function(){
            this.errors.splice(0)
            if(!this.atname){
                this.errors.push("Name is required")
            }
            else if(!this.atdescription){
                this.errors.push("Description is required")
            }
            else if(!this.attype){
                this.errors.push("Type is required")
            }    
            
            if(!this.errors.length){
                this.submitForm()
            }

        },

        activate_tagify: async function(data){
            if(this.attype==='ms'){
                await new Promise(r => setTimeout(r, 1000));

                let choices = document.querySelector('textarea[name=atchoices]');
                let tagify_choices = new Tagify(choices);
                this.tagify = tagify_choices

                if(data.isTrusted == null){
                    tagify_choices.addTags(data)
                }
            }
        },

        on_tagify_change: function(e){
            let vals = JSON.parse(e.target.value)

            if(this.etid == null){
                for(let item of vals){                
                    if(!this.processed_choices.includes(item.value)){
                        this.processed_choices.push(item.value)
                    }
                }
            } else {
                this.processed_choices = vals
            }
        },

        submitForm: async function(){
            let token = sessionStorage.getItem("token")
            let api_url = `/api/tracker`
            let api_method = 'POST'
            let body_choices = this.processed_choices

            if(this.etid != null){
                api_url = `/api/tracker/${this.etid}`
                api_method = 'PATCH'

                if(this.ochoices != null){
                    let difference = this.ochoices.filter(({ id: id1 }) => !this.processed_choices.some(({ id: id2 }) => id2 === id1))                    
                    for(let item of difference){
                        body_choices.push({id: item.id, value: ""})
                    }
                }
            }

            await fetch(api_url, {
                method: api_method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                    
                },
                body: JSON.stringify({
                    "name": this.atname, 
                    "description": this.atdescription, 
                    "type": this.attype,
                    "choices": body_choices,
                    "settings": ["x1","x2"]
                })
            })
            .then(response => response.json().then(jdata=> ({response: response, data: jdata})))
            .then(({response, data}) => {
                if(!response.ok){
                    if(data.error != null){
                        this.errors.push(data.error)
                        throw new Error(`Error ${response.status}: ${data.error}`)
                    } else {
                        this.errors.push(data.msg)
                        throw new Error(`Error ${response.status}: ${data.msg}`)
                    }
                }                
                toastr.success(data.msg, this.title)
                if(this.etid){
                    this.$router.push({name: 'tracker', params:{id: this.etid}})
                } else {
                    this.$router.push({name: 'home'})
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

        edit_mode: async function(id){
            this.etid = id
            console.log(`Edit mode: Tracker ID ${this.etid}`)
            
            let tdata = await get_tracker_data(this.etid)
            this.title = `Edit Tracker ${tdata.name}`
            this.atname = tdata.name
            this.atdescription = tdata.description
            this.attype = tdata.type
            this.ochoices = tdata.choices
            
            toastr.info(`Editing tracker with ID ${id}`, 'Edit Tracker')
            this.activate_tagify(tdata.choices)
        }
    },
    

    mounted: async function(){
        if(this.$route.params.id != null){
            await this.edit_mode(this.$route.params.id)
        }
    },

    created() {
        this.$watch(
          () => this.$route.params,
          async function (toParams, previousParams) {
            console.log(toParams, previousParams)
            if(this.$route.params.id != null){
                console.log("Tracker ID changed from " + previousParams.id + " to " + toParams.id)
                await this.edit_mode(this.$route.params.id)
            }
          }
        )
    }
}