import { get_tracker_data, export_data } from "./common.js"

export const tracker_logs = {
    template: `
    <div id="logs">
        <div class="row">
            <div class="col col-8">
                <div class="row justify-content-md-center">
                    <div class="col-md-auto">                        
                        <h2 class="page-head">
                            {{tracker['name']}} - Tracker
                        </h2>
                    </div>
                </div>
            </div>
            <div class="col col-8">
                <div class="col-12 border cchart">
                    <div id="chart"></div>
                </div>

                <h2 class="page-head">Logs of {{tracker.name}}</h2>

                <table class="table table-bordered display nowrap dataTable dtr-inline collapsed" id="logsTable">
                    <thead class="thead-dark">
                        <tr>
                            <th>Sr. No</th>
                            <th>Date-Time</th>
                            <th>Value</th>
                            <th>Note</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(log, index) in logs" v-bind:key="log.id">
                            <td>{{index+1}}</td>
                            <td>{{log.timestamp}}</td>
                            <td v-if="(tracker.type=='integer')||(tracker.type=='float')">{{log.value}}</td>
                            <td v-if="tracker.type=='timerange'">{{log.start}} - {{log.end}}</td>
                            <td v-if="tracker.type=='ms'"><span v-for="choice in log.value" :key="choice.choice_id">{{choice.choice_name}}, </span></td>
                            <td>{{log.note}}</td>
                            <td class="d-flex justify-content-center">
                                <div class="btn-group" type="button" role="group">
                                    <button id="btnGroupDrop1" type="button" class="btn btn-outline-primary btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                        Action
                                    </button>
                                    <div class="dropdown-menu" aria-labelledby="btnGroupDrop1">
                                        <router-link class="dropdown-item" :to="{name:'edit_log', params:{tid:tracker_id, lid:log.id}}">Edit</router-link>
                                        <a class="dropdown-item" @click="deleteLog(index)">Delete</a>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="col col-4">
                <div class="container">
                    <div class="row border csidebarfirst" v-if="tracker.type!='ms'">
                        <div class="row justify-content-md-center"><h4 class="page-head">Period</h4></div>
                        <div class="form-group">
                            <select class="form-control" v-model="timeperiod" @change="tpChanged">
                                <option value="d">Daily</option>
                                <option value="w">Weekly</option>
                                <option value="m">Monthly</option>
                                <option value="a">All Data</option>
                            </select>
                        </div>            
                    </div>

                    <div class="row border csidebar" v-if="(tracker.type=='integer')||(tracker.type=='float')">
                        <div class="row justify-content-md-center"><h4 class="page-head">Statistics</h4></div>
                        <div class="form-group">
                            <table class="table table-borderless">
                                <tr>
                                    <td>Mean</td>
                                    <td>{{stats.extra.mean}}</td>
                                </tr>
                                <tr>
                                    <td>Median</td>
                                    <td>{{stats.extra.median}}</td>
                                </tr>
                                <tr>
                                    <td>25th Percentile</td>
                                    <td>{{stats["extra"]["25th"]}}</td>
                                </tr>
                                <tr>
                                    <td>75th Percentile</td>
                                    <td>{{stats["extra"]["75th"]}}</td>
                                </tr>
                            </table>
                        </div>            
                    </div>

                    <div class="row border" v-bind:class="(tracker.type=='ms')?'csidebarfirst':'csidebar'">
                        <div class="row justify-content-md-center"><h4 class="page-head">Tracker information</h4></div>
                        <table class="table table-borderless">
                            <tr>
                                <td>ID</td>
                                <td>{{tracker.id}}</td>
                            </tr>
                            <tr>
                                <td>Name</td>
                                <td>{{tracker.name}}</td>
                            </tr>
                            <tr>
                                <td>Description</td>
                                <td>{{tracker.description}}</td>
                            </tr>
                            <tr>
                                <td>Type</td>
                                <td v-if="tracker.type=='integer'">Numerical (Integral)</td>
                                <td v-if="tracker.type=='float'">Numerical (Fractional)</td>
                                <td v-if="tracker.type=='ms'">Multiple Choice Selection</td>
                                <td v-if="tracker.type=='timerange'">Time Range</td>
                            </tr>
                            <tr>
                                <td>Action</td>
                                <td>
                                    <div class="btn-group" type="button card-link" role="group">
                                        <button id="btnGroupDrop1" type="button" class="btn btn-info btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                            Tracker
                                        </button>
                                        <div class="dropdown-menu" aria-labelledby="btnGroupDrop1">                                            
                                            <router-link class="dropdown-item" :to="{name: 'add_log', params: {tid: tracker_id}}">Log value</router-link>
                                            <router-link class="dropdown-item" :to="{name: 'edit_tracker', params: {id: tracker_id}}">Edit</router-link>
                                        </div>
                                    </div>
                                    
                                </td>
                            </tr>
                            <tr>
                                <td>Extra</td>                    
                                <td>
                                    <div class="btn-group" type="button card-link" role="group">
                                        <button id="btnGroupDrop1" type="button" class="btn btn-warning btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                            Action
                                        </button>
                                        <div class="dropdown-menu" aria-labelledby="btnGroupDrop1">                                            
                                            <a class="dropdown-item" @click="exp_data('pdf')">Export Data as PDF</a>
                                            <a class="dropdown-item" @click="exp_data('csv')">Export Data as CSV</a>
                                            <a class="dropdown-item" @click="autogen('add')">Auto-Generate Values</a>
                                            <a class="dropdown-item" @click="autogen('delete')">Delete all Logs</a>
                                        </div>
                                    </div>
                                    
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>`,

    data: function(){
        return {
            tracker_id: this.$route.params.id,
            logs: [],
            tracker: {},
            stats:{extra:{}},
            timeperiod: "a"
        }
    },



    methods: {
        deleteLog: async function(arr_dex){
            let token = sessionStorage.getItem("token")
            await fetch(`/api/tracker/${this.tracker_id}/logs/${this.logs[arr_dex].id}`, {
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
                }
                toastr.success(data.msg, 'Success')
                this.logs.splice(arr_dex, 1);
                this.reloadChart()
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

        autogen: async function(fxn){
            let token = sessionStorage.getItem("token")
            let url = `/tracker/${this.tracker_id}/autolog/200`
            if(this.tracker.type == "timerange"){
                url = `/tracker/${this.tracker_id}/autolog/25`
            }
            
            let method = "GET"

            if(fxn == "delete"){
                url = `/tracker/${this.tracker_id}/logs/delete_all`
                method = "DELETE"
            }

            await fetch(url, {
                method: method,
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
                toastr.success(data.msg, 'Success')
                if(fxn == "delete"){
                    this.logs.splice(0);
                } else {
                    this.load_data(this.tracker_id)
                }
                this.reloadChart()
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

        load_data: async function(tid){
            let token = sessionStorage.getItem("token")
            this.tracker = await get_tracker_data(tid)
            await fetch(`/api/tracker/${tid}/logs`, {
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
                this.logs.splice(0)
                this.logs.push(... data)
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

        get_stats: async function(tid, timeperiod="a"){
            let token = sessionStorage.getItem("token")
            await fetch(`/api/tracker/${tid}/stats/${timeperiod}`, {
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
                this.stats = data
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

        draw_chart: function(){
            let ctype = ""
            let cdata = []           

            if(this.tracker.type == "float" || this.tracker.type == "integer"){
                ctype = "line"
                for(let date in this.stats.chart){
                    cdata.push({the_d: date, value: this.stats.chart[date]})
                }
            } else if (this.tracker.type == "ms"){
                ctype = "bar"
                for(let name in this.stats.chart){
                    cdata.push({ y: name, a: this.stats.chart[name] })
                }
            } else if (this.tracker.type == "timerange"){
                ctype = "gantt"
                for(let item of this.stats.chart){
                    console.log(item)
                    cdata.push(
                        {
                            x: item.note,
                            y: [
                              new Date(item.start).getTime(),
                              new Date(item.end).getTime()
                            ]
                        }
                    )
                }
            }

            $("#chart").empty();
            create_chart('chart', cdata, ctype, 'the_d', ['value'], ['Values'])

        },

        reloadChart: async function(){
            await this.get_stats(this.$route.params.id, this.timeperiod)
            this.draw_chart()
        },
        
        tpChanged: async function(){
            this.reloadChart()
        },
        
        exp_data: async function(type){
            export_data(this.tracker_id, type)
        }
    },

    mounted: async function(){
        await this.load_data(this.$route.params.id)
        await this.get_stats(this.$route.params.id)
        this.draw_chart()
        $('#logsTable').DataTable( {
            "order": [[ 1, 'asc']],            
            dom: 'flrtip'
        } );
    },

    created() {
        this.$watch(
          () => this.$route.params,
          async function (toParams, previousParams) {
            console.log("Tracker ID changed from " + previousParams.id + " to " + toParams.id)            
            await this.load_data(toParams.id)
            await this.get_stats(toParams.id, this.timeperiod)
            this.draw_chart()
          }
        )
    },

}




function create_chart(ele_name, chart_data, ctype, xkey='y', ykeys=['a'], labels=['Series A']){    
    if(ctype == "line"){
        window.chart = new Morris.Line({
            // ID of the element in which to draw the chart.
            element: ele_name,
            // Chart data records -- each entry in this array corresponds to a point on
            // the chart.
            data: chart_data,
            // The name of the data record attribute that contains x-values.
            xkey: xkey,
            // A list of names of data record attributes that contain y-values.
            ykeys: ykeys,
            // Labels for the ykeys -- will be displayed when you hover over the
            // chart.
            labels: labels,
            parseTime: false,
            resize: true,
            redraw: true
        });
    } else if (ctype == "bar"){
        window.chart = new Morris.Bar({
            // ID of the element in which to draw the chart.
            element: ele_name,
            data: chart_data,
            xkey: 'y',
            ykeys: ['a'],
            labels: ['Series A'],
            resize: true,
            redraw: true
          });
    } else if (ctype == "gantt"){
        var options = {
            series: [
            {
              data: chart_data
            }
          ],
            chart: {
            height: 350,
            type: 'rangeBar'
          },
          plotOptions: {
            bar: {
              horizontal: true
            }
          },
          xaxis: {
            type: 'datetime'
          }
          };
      
          window.chart = new ApexCharts(document.querySelector(`#${ele_name}`), options);
          chart.render();
    }
}