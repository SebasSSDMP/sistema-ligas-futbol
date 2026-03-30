import { useApiState } from '../hooks/useApi';

export default function GlobalLoader() {
  const { loading, error } = useApiState();

  return (
    <>
      {/* Global Loader Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-dark-card rounded-xl p-6 text-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-accent-blue border-t-transparent"></div>
            <p className="text-white">Cargando...</p>
          </div>
        </div>
      )}
      
      {/* Global Error Banner */}
      {error && (
        <div className="fixed bottom-4 left-4 right-4 z-50">
          <div className="bg-red-500/90 text-white px-6 py-4 rounded-xl text-center">
            <p className="font-medium">{error}</p>
            <button 
              onClick={() => {
                // Import here to avoid circular dependency
                import('../utils/apiState').then(({ clearGlobalError }) => {
                  clearGlobalError();
                });
              }}
              className="mt-2 text-accent-blue hover:underline text-sm"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </>
  );
}