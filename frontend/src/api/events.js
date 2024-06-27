import base from './base';
import axios from '@/utils/http';
import qs from 'qs';

// GET /api/v1/info
// POST /api/v1/submit

const events = {
    getDataInfo (params) {
        return axios.get(`${base.sq}/info`, {
            params: params 
        });
    },
    runCycleGanInfer (params) {
        return axios.post(`${base.sq}/submit`, {}, {
            params: params
        });
    },
    runMergeChannels(params) {
        return axios.post(`${base.sq}/merge_channels/submit`, {}, {
            params: params
        });
    },
    checklogs(params) {
        return axios.get(`${base.sq}/checklogs`, {
            params: params 
        });
    },
    getRecords (params) {
        return axios.get(`${base.sq}/jobs`, {
            params: params 
        });
    },
    getSubfolders (params) {
        return axios.get(`${base.sq}/subfolders`, {
            params: params 
        });
    },
}

export default events;
