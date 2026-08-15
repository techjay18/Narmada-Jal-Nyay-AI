import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Canal
export const getCanalStatus    = (scenario = 'normal') => api.get(`/canal/status?scenario=${scenario}`)
export const getFlowData       = (hours = 24, sensorId = null) => {
  const params = new URLSearchParams({ hours })
  if (sensorId) params.append('sensor_id', sensorId)
  return api.get(`/canal/flow?${params}`)
}
export const getSensors        = () => api.get('/canal/sensors')

// Farmers
export const getFarmers        = (params = {}) => api.get('/farmers', { params })
export const getFarmer         = (id) => api.get(`/farmers/${id}`)
export const getFarmerStatus   = (id, scenario = 'normal') =>
  api.get(`/farmers/${id}/water-status?scenario=${scenario}`)

// Schedule
export const getSchedule       = () => api.get('/schedule')
export const generateSchedule  = (data) => api.post('/schedule/generate', data)

// Complaints
export const getComplaints     = (params = {}) => api.get('/complaints', { params })
export const submitComplaint   = (data) => api.post('/complaints', data)
export const analyzeComplaint  = (id) => api.post(`/complaints/${id}/analyze`)
export const resolveComplaint  = (id, data) => api.post(`/complaints/${id}/resolve`, data)

// Dashboard
export const getDashboard      = (scenario = 'normal') => api.get(`/dashboard?scenario=${scenario}`)
export const agentAnalyze      = (question, scenario = 'normal') =>
  api.post(`/dashboard/agent/analyze?question=${encodeURIComponent(question)}&scenario=${scenario}`)

// Alerts
export const getAlerts         = (params = {}) => api.get('/alerts', { params })
export const acknowledgeAlert  = (id) => api.post(`/alerts/${id}/acknowledge`)

// Simulate
export const simulateSensors   = (scenario = 'normal') => api.post(`/simulate/sensor-data?scenario=${scenario}`)
export const runDemoScenario   = () => api.get('/simulate/demo-scenario')
