<template>
    <v-app>
        <v-app-bar
            color="#008cba"
            dense
            dark
            app
        >
            <v-toolbar-title style="font-size:28px">Super resolution
                <p id="appVersion">Beta</p>
                
                <v-btn 
                  icon
                  href="mailto:miaot2@nih.gov; hyun.jung@nih.gov; linmin.pei@nih.gov?Subject=Fucci%20Cell%20Detection"
                >
                  <v-icon>mdi-email</v-icon>
                </v-btn>
            </v-toolbar-title>
        </v-app-bar>
        <v-main>
            <v-container
            >
            <v-row>
                <v-col cols="6">
                    <v-row align="center" justify="center">
                        <v-col style="padding-bottom:0px" cols="6">
                            <v-card outlined >
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">Data Id:</v-card-title>
                                </v-toolbar>
                                <v-card-text>
                                    <v-text-field clearable label="Data Id" v-model="data_id"></v-text-field>
                                </v-card-text>
                            </v-card>
                        </v-col>
                        <v-col style="padding-bottom:0px" cols="6">
                            <v-card outlined>
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">Data Type:</v-card-title>
                                </v-toolbar>
                                <v-card-text>
                                    <v-text-field clearable label="Data Type" v-model="data_type"></v-text-field>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row >
                        <v-col cols="6">
                            <v-card style="height:180px;"
                                outlined>
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">
                                            Data Name:
                                    </v-card-title>
                                </v-toolbar>
                                <v-card-subtitle></v-card-subtitle>
                                <v-card-text style="font-size: 1.0em;">
                                    {{ dataInfo.name }}
                                </v-card-text>
                                <v-card-actions>
                                    <v-spacer></v-spacer>
                                </v-card-actions>
                            </v-card>
                            <v-card style="height:250px; margin-top:12px" 
                                outlined>
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">
                                        Analysis:
                                    </v-card-title>
                                </v-toolbar>
                                <v-card-subtitle></v-card-subtitle>
                                    <v-tabs
                                      v-model="tab"
                                      bg-color="transparent"
                                      color="basil"
                                      grow
                                    >
                                      <v-tab
                                        v-for="analysis in analysis_tabs"
                                        :key="analysis"
                                        :value="analysis"
                                      >
                                        {{ analysis.name }}
                                      </v-tab>
                                    </v-tabs>

                                    <v-window v-model="tab">
                                        <v-window-item
                                            v-for="analysis in analysis_tabs"
                                            :key="analysis"
                                            :value="analysis"
                                        >
                                            <v-card
                                              color="basil"
                                              flat
                                            >
                                                <v-card-text>{{ analysis.description }}</v-card-text>
                                            </v-card>
                                        </v-window-item>
                                    </v-window>
                                <v-card-actions class='card-actions'>
                                    <v-spacer></v-spacer>
                                    <v-btn
                                        outlined
                                        variant="tonal"
                                        color="deep-purple-accent-4"
                                        @click="runHPC()"
                                    >
                                        Run
                                    </v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-col>
                        <v-col cols="6">
                            <v-card style="height:450px; display: flex !important;flex-direction: column;"
                                outlined>
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">
                                        Records:
                                    </v-card-title>
                                </v-toolbar>
                                <v-card-subtitle></v-card-subtitle>
                                <v-card-text style="margin-left:0px; flex-grow: 1; overflow: auto; font-size: 1.0em;">
                                    <v-list>
                                        <v-list-item
                                            v-for="(record, i) in records"
                                            :key="i"
                                            color="primary"
                                            :value="record.id"
                                            rounded="xl"
                                            @click="checkRecord(record)"
                                            :subtitle="record.time"
                                            :title="record.title"
                                        >
                                            <template v-slot:prepend>
                                              <v-icon v-if="record.status === 3" icon="mdi-circle" color="green"></v-icon>
                                              <v-icon v-else="record.status === 2" icon="mdi-circle" color="orange"></v-icon>
                                            </template>
                                        </v-list-item>
                                    </v-list>
                                </v-card-text>
                                <v-card-actions>
                                </v-card-actions>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-col>
                <v-col cols="6">
                    <v-row>
                        <v-col style="padding-bottom:0px" cols=12>
                            <v-card style="height:385px; margin-left:40px; display: flex !important;flex-direction: column;">
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">Status: 
                                        <span v-if="status === 2">Running
                                        </span>
                                        <span v-if="status === 3">Complete
                                        </span>
                                    </v-card-title>
                                </v-toolbar>
                                <v-card-text style="margin-left:10px; padding: 0px; flex-grow: 1; overflow: auto;">
                                    <v-timeline density="compact" side="end">
                                        <v-timeline-item size=10 v-for="log in logs" :key="log.id">{{log}}</v-timeline-item>
                                    </v-timeline>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols=12>
                            <v-card style="height:250px; margin-left:40px; display: flex !important;flex-direction: column;">
                                <v-toolbar card>
                                    <v-card-title class="text-h7 text-md-h6 text-lg-h5">Warning & Error: {{slurm_id}} </v-card-title>
                                </v-toolbar>
                                <v-card-text style="margin-left: 10px; padding: 0px; flex-grow: 1; overflow: auto;">
                                    <v-timeline density="compact" side="end">
                                        <v-timeline-item size=10 v-for="err in error" :key="err.id">{{err}}</v-timeline-item>
                                    </v-timeline>
                                </v-card-text>
                            </v-card>
                        </v-col>
                    </v-row>
                </v-col>
            </v-row>
            </v-container>
            <v-container>
                <footer class='copy'>
                    © Imaging and Visualization Group, ABCS - {{year}}
                </footer>
            </v-container>
            <div class="footerSuccessAlert alert" role='alert'>
                <v-alert
                    dense
                    text
                    type="success"
                >
                    Successfully add new event
                </v-alert> 
            </div>
            <div class="footerErrorAlert alert" role='alert'>
                <v-alert
                    dense
                    text
                    type="warning"
                >
                    {{ warning }}
                </v-alert> 
            </div>
        </v-main>
    </v-app>
</template>

<script>
    // import axios from 'axios';
    // import $ from 'jquery';
    // import TableView from '../components/tableView.vue'

    export default {
        name: 'home',
        // components: {
        //     TableView
        // },
        data: () => ({
            token: '',
            user: '',
            data_id: '',
            data_type: '',
            dataInfo: '',
            year: new Date().getFullYear(),
            warning: '',
            records: null,
            logs: '',
            error: '',
            status: null,
            slurm_id: null,
            job_name: null,
            tab: 'Analysis',
            analysis_tabs: [{'name': 'analysis_1', 'description': 'Fetching data from omero with original format & run analysis 1 sned the result back to the omero'}, {'name': 'analysis_2', 'description': 'Fetching data from omero with original format & run analysis 2 sned the result back to the omero'}]
        }),
        methods: {
            runHPC() {
                this.$api.events.runHPC({'token': this.token, 'user': this.user,
                    'data_id': this.data_id, 'data_type': this.data_type,
                    'data_name': this.dataInfo.name,}).then(res=> {
                        this.slurm_id = res.data['slurm_id'];
                        this.job_name = res.data['job_name'];
                        this.checklogs();
                    });
            },
            initialData() {
                this.slider['value'] = 0;
                this.item = [];
                this.currentImage = {
                    imageFrameHeight: 0,
                    imageFrameWidth: 0,
                    imageName: null,
                    frame: 0,
                    annsOnFrame: []
                };
                this.selected = [];
                this.initSelected = [];
                this.update = {};
                // this.annotations = [];
            },
            checklogs() {
                let params = {};
                if (this.slurm_id && this.job_name) {
                    params = {'slurm_id': this.slurm_id, 'job_name': this.job_name};
                }
                this.$api.events.checklogs(params).then(res => {
                    this.status = res.data['status'];
                    this.logs = res.data['logs'];
                    this.error = res.data['error'];
                    this.records = res.data['records'];
                });
            },
            checkRecord(record) {
                this.slurm_id = record.slurm_id;
                this.job_name = record.title;
                this.status = record.status;
                this.checklogs();
            },
            getUrl (path) {
                const href = window.location.href
                const hashPos = href.indexOf('#')
                let base = hashPos > -1 ? href.slice(0, hashPos) : href

                const searchPos = base.indexOf('?')
                const query = searchPos > -1 ? base.slice(searchPos) : ''
                base = query ? base.slice(0, searchPos) : base

                return `${base}#${path + query}`
            }
        },
        mounted() {
            let urlParams = new URLSearchParams(window.location.search);
            this.token = urlParams.get('token');
            this.user = urlParams.get('username');
            console.log(this.user)
            this.data_id = urlParams.get('data_id');
            this.data_type = urlParams.get('data_type');
            this.$api.events.getDataInfo({'token': this.token, 'user': this.user,
                'data_id': this.data_id, 'data_type': this.data_type}).then(res => {
                this.dataInfo = res.data;
            });

            this.checklogs()
            setInterval(this.checklogs, 10000);
        }
    }

</script>

<style>
#appVersion {
    display: inline;
    font-size: 12px;
}
.page-header {
    border-bottom: 1px solid #dddddd;
    font-size: 26px 
}

.v-text-field input {
    font-size: 1.8em;
}

.footerSuccessAlert {
    position: fixed;
    right: 0px;
    bottom: 0px;
    display: none;
}
.footerErrorAlert {
    position: fixed;
    right: 0px;
    bottom: 0px;
    display: none;
}
.card-actions {
  position: absolute;
  bottom: 0;
  right: 0;
}
</style>