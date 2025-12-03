import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            // Validate token or just set it for now. 
            // Ideally we should call an endpoint to get user info.
            // For now, we decode the token or just assume it's valid if present.
            // Let's decode the username from the token payload (simple base64 decode for now)
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                setUser({ username: payload.sub });
            } catch (e) {
                localStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await axios.post('http://localhost:8000/api/auth/login', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            const { access_token } = response.data;
            localStorage.setItem('token', access_token);

            const payload = JSON.parse(atob(access_token.split('.')[1]));
            setUser({ username: payload.sub });
            return true;
        } catch (error) {
            console.error('Login failed:', error);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
