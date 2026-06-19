import apiClient from '../../shared/api/client'

export const loginApi = (username, password) => {
    return apiClient.post('/auth/login/', { username, password})
}

export const logoutApi = () => {
    return apiClient.post('/auth/logout/')
}