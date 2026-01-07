import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const LLMContext = createContext();

export const useLLM = () => useContext(LLMContext);

export const LLMProvider = ({ children }) => {
    const [configs, setConfigs] = useState([]);
    const [selectedConfigId, setSelectedConfigId] = useState(null);
    const [loading, setLoading] = useState(false);
    const [isInitialized, setIsInitialized] = useState(false); // New state to track initialization

    // 1. Initial Load: Fetch configs
    useEffect(() => {
        fetchConfigs();
    }, []);

    // 2. Sync: Once configs are loaded, restore selection or default
    useEffect(() => {
        if (configs.length > 0 && !isInitialized) {
            const savedConfigId = localStorage.getItem('selectedLLMConfigId');

            if (savedConfigId) {
                const parsedId = parseInt(savedConfigId);
                // Verify the saved ID actually exists in the fetched configs
                const configExists = configs.some(c => c.id === parsedId);
                if (configExists) {
                    setSelectedConfigId(parsedId);
                } else {
                    // Saved config no longer exists, default to first
                    setSelectedConfigId(configs[0].id);
                }
            } else {
                // No saved config, default to first
                setSelectedConfigId(configs[0].id);
            }
            setIsInitialized(true);
        } else if (configs.length === 0 && !loading) {
            // Handle case where there are no configs at all
            setIsInitialized(true);
        }
    }, [configs, isInitialized, loading]);

    // 3. Persist: Save selection whenever it changes
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
            // Note: We don't set selectedConfigId here anymore to avoid race conditions
            // The useEffect handling 'isInitialized' will take care of it.
        } catch (err) {
            console.error('Failed to fetch LLM configs:', err);
        } finally {
            setLoading(false);
        }
    };

    const addConfig = async (config) => {
        console.log('addConfig called with:', config);
        try {
            const response = await axios.post(`${API_URL}/api/llm-configs`, config);
            console.log('addConfig success:', response.data);
            const newConfig = response.data;
            setConfigs(prev => [...prev, newConfig]);

            // If it's the first config, select it automatically
            if (!selectedConfigId) {
                setSelectedConfigId(newConfig.id);
            }
            return newConfig;
        } catch (err) {
            console.error('Failed to add LLM config:', err);
            throw err;
        }
    };

    const updateConfig = async (id, config) => {
        try {
            const response = await axios.put(`${API_URL}/api/llm-configs/${id}`, config);
            setConfigs(prev => prev.map(c => c.id === id ? response.data : c));
            return response.data;
        } catch (err) {
            console.error('Failed to update LLM config:', err);
            throw err;
        }
    };

    const deleteConfig = async (id) => {
        try {
            await axios.delete(`${API_URL}/api/llm-configs/${id}`);

            setConfigs(prev => {
                const newConfigs = prev.filter(c => c.id !== id);
                return newConfigs;
            });

            if (selectedConfigId === id) {
                setSelectedConfigId(null);
                // Logic to select next available could go here, or let the user select
                // Ideally, we might want to auto-select the first one if available:
                // But we can't access the *new* state of configs here immediately due to closure.
                // We can do it optimistically or useEffect, but simpler is fine for now:
                localStorage.removeItem('selectedLLMConfigId');
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
