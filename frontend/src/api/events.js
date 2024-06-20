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
    runHPC (params) {
        return axios.post(`${base.sq}/submit`, {}, {
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
}

export default events;
