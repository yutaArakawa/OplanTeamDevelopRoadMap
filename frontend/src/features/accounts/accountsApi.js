import apiClient from '../../shared/api/client'

export const getUserList = (filters = {}) => {
    return apiClient.get('/accounts/user/list/', { params: filters })
}
