import axios from 'axios'

export const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'x-user-id': 'demo_user',
    'x-dept-id': 'production',
  },
})
