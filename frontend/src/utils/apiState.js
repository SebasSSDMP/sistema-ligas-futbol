// Global state for API loading and errors (non-react)
let globalLoadingCount = 0;
let globalError = null;
const listeners = new Set();

// Notify all listeners of state changes
function notifyListeners() {
  listeners.forEach(listener => listener({ loading: globalLoadingCount > 0, error: globalError }));
}

// Subscribe to global API state changes
export function subscribe(listener) {
  listeners.add(listener);
  // Initialize with current state
  listener({ loading: globalLoadingCount > 0, error: globalError });
  
  return () => listeners.delete(listener);
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