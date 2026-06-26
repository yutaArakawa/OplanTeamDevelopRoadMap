import apiClient from '../../shared/api/client'

export const getUserList = (filters = {}) => {
    return apiClient.get('/accounts/user/list/', { params: filters })
}

export const getUserFormOptions = () => {
    return apiClient.get('/accounts/user/create/')
}

export const createUser = (data) => {
    return apiClient.post('/accounts/user/create/', data)
}

export const getUserDetail = (pk) => {
    return apiClient.get(`/accounts/user/${pk}/`)
}

export const updateUser = (pk, data) => {
    return apiClient.put(`/accounts/user/${pk}/`, data)
}

export const deleteUser = (pk) => {
    return apiClient.delete(`/accounts/user/${pk}/`)
}
