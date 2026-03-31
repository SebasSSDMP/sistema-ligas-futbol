import React from 'react'  // 
import { useState, useCallback } from 'react';

// Global state for API loading and errors
let globalLoadingCount = 0;
let globalError = null;
const listeners = new Set();

// Notify all listeners of state changes
function notifyListeners() {
  listeners.forEach(listener => listener({ loading: globalLoadingCount > 0, error: globalError }));
}

// Subscribe to global API state changes
export function useApiState() {
  const [state, setState] = useState({ loading: false, error: null });
  
  // Subscribe on mount
  React.useEffect(() => {
    listeners.add(setState);
    // Initialize with current state
    setState({ loading: globalLoadingCount > 0, error: globalError });
    
    return () => listeners.delete(setState);
  }, []);
  
  return state;
}

// Increment global loading counter
export function startGlobalLoading() {
  globalLoadingCount++;
  if (globalLoadingCount === 1) {
    // First request started
    notifyListeners();
  }
}

// Decrement global loading counter
export function stopGlobalLoading() {
  globalLoadingCount = Math.max(0, globalLoadingCount - 1);
  if (globalLoadingCount === 0) {
    // No more requests
    notifyListeners();
  }
}

// Set global error
export function setGlobalError(error) {
  globalError = error;
  notifyListeners();
}

// Clear global error
export function clearGlobalError() {
  globalError = null;
  notifyListeners();
}

// Custom hook for API requests with automatic loading/error handling
export function useApiRequest() {
  const apiState = useApiState();
  
  const executeRequest = useCallback(async (requestFn) => {
    startGlobalLoading();
    clearGlobalError();
    
    try {
      const result = await requestFn();
      return result;
    } catch (error) {
      // Determine error message
      let errorMessage = 'Error desconocido';
      
      if (error.name === 'AbortError') {
        errorMessage = 'Solicitud cancelada';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Servidor no disponible';
      } else if (error.message.includes('timeout')) {
        errorMessage = 'Tiempo de espera agotado';
      } else if (error.message.includes('HTTP')) {
        errorMessage = error.message.replace('Error: ', '');
      } else {
        errorMessage = error.message || 'Error inesperado';
      }
      
      setGlobalError(errorMessage);
      throw error;
    } finally {
      stopGlobalLoading();
    }
  }, []);
  
  return {
    ...apiState,
    executeRequest
  };
}