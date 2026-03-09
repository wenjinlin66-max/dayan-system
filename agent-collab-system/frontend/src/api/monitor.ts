import { http } from './client'

export const fetchMetrics = async () => http.get('/v1/monitor/metrics')
