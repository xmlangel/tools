import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const LLMContext = createContext();

export const useLLM = () => useContext(LLMContext);

export const LLMProvider = ({ children }) => {
    const [configs, setConfigs] = useState([]);
    const [selectedConfigId, setSelectedConfigId] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchConfigs();
        // Load selected config from local storage if exists
        const savedConfigId = localStorage.getItem('selectedLLMConfigId');
        if (savedConfigId) {
            setSelectedConfigId(parseInt(savedConfigId));
        }
    }, []);

    useEffect(() => {
        if (selectedConfigId) {
            localStorage.setItem('selectedLLMConfigId', selectedConfigId);
        }
    }, [selectedConfigId]);

    const fetchConfigs = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/api/llm-configs`);
            setConfigs(response.data);

            // If no config selected and configs exist, select the first one
            if (!selectedConfigId && response.data.length > 0) {
                setSelectedConfigId(response.data[0].id);
            }
        } catch (err) {
            console.error('Failed to fetch LLM configs:', err);
        } finally {
            setLoading(false);
        }
    };

    const addConfig = async (config) => {
        try {
            const response = await axios.post(`${API_URL}/api/llm-configs`, config);
            setConfigs([...configs, response.data]);
            if (!selectedConfigId) {
                setSelectedConfigId(response.data.id);
            }
            return response.data;
        } catch (err) {
            console.error('Failed to add LLM config:', err);
            throw err;
        }
    };

    const updateConfig = async (id, config) => {
        try {
            const response = await axios.put(`${API_URL}/api/llm-configs/${id}`, config);
            setConfigs(configs.map(c => c.id === id ? response.data : c));
            return response.data;
        } catch (err) {
            console.error('Failed to update LLM config:', err);
            throw err;
        }
    };

    const deleteConfig = async (id) => {
        try {
            await axios.delete(`${API_URL}/api/llm-configs/${id}`);
            setConfigs(configs.filter(c => c.id !== id));
            if (selectedConfigId === id) {
                setSelectedConfigId(null);
            }
        } catch (err) {
            console.error('Failed to delete LLM config:', err);
            throw err;
        }
    };

    const getSelectedConfig = () => {
        return configs.find(c => c.id === selectedConfigId);
    };

    return (
        <LLMContext.Provider value={{
            configs,
            selectedConfigId,
            setSelectedConfigId,
            addConfig,
            updateConfig,
            deleteConfig,
            getSelectedConfig,
            loading
        }}>
            {children}
        </LLMContext.Provider>
    );
};
