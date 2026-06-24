import apiClient from '../../shared/api/client'

export const getDashboard = () => {
    return apiClient.get('/dashboard/')
}