import { useState, useCallback, useEffect, useRef } from 'react';

export function useFetchData(fetchFunction, dependencies = [], options = {}) {
  const { immediate = true, onSuccess, onError } = options;
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(!immediate);
  
  const isMountedRef = useRef(true);
  const requestIdRef = useRef(null);
  const fetchFunctionRef = useRef(fetchFunction);
  
  fetchFunctionRef.current = fetchFunction;

  const execute = useCallback(async (deps = dependencies) => {
    if (!isMountedRef.current) return null;
    
    const id = `fetch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    requestIdRef.current = id;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log(`[useFetchData] Fetching with deps:`, deps);
      const result = await fetchFunctionRef.current(...deps);
      
      if (!isMountedRef.current) {
        console.log(`[useFetchData] Component unmounted, ignoring result`);
        return null;
      }
      
      if (requestIdRef.current !== id) {
        console.log(`[useFetchData] Stale request, ignoring result`);
        return null;
      }
      
      setData(result);
      setInitialized(true);
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      console.log(`[useFetchData] Success, data:`, result);
      return result;
    } catch (err) {
      if (!isMountedRef.current) return null;
      if (requestIdRef.current !== id) return null;
      
      console.error(`[useFetchData] Error:`, err);
      setError(err.message || 'Error desconocido');
      
      if (onError) {
        onError(err);
      }
      
      return null;
    } finally {
      if (isMountedRef.current && requestIdRef.current === id) {
        setLoading(false);
      }
    }
  }, [dependencies.join(',')]);

  useEffect(() => {
    isMountedRef.current = true;
    
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (immediate && !initialized) {
      execute();
    }
  }, [immediate, initialized]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setInitialized(!immediate);
  }, [immediate]);

  return {
    data,
    setData,
    loading,
    error,
    initialized,
    execute,
    reset,
    refetch: () => execute(),
  };
}

export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

export function usePrevious(value) {
  const ref = useRef();
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}
