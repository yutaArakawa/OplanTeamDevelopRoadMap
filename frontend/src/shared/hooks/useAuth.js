import { useState, useEffect } from 'react'
import apiClient from '../api/client'

export function useAuth() {
    const [userInfo, setUserInfo] = useState(null)

    useEffect(() => {
        apiClient.get('/auth/me/')
            .then(res => setUserInfo(res.data))
            .catch(() => setUserInfo(null))

    }, [])

    return { userInfo }
}