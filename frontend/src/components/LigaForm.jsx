import { useState, useEffect } from 'react';

export function LigaForm({ liga, onSubmit, onCancel, isSubmitting }) {
  const [nombre, setNombre] = useState('');
  const [pais, setPais] = useState('');
  const [error, setError] = useState('');

  const isEditando = !!liga;

  useEffect(() => {
    if (liga) {
      setNombre(liga.nombre || '');
      setPais(liga.pais || '');
    } else {
      setNombre('');
      setPais('');
    }
    setError('');
  }, [liga]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!nombre.trim()) {
      setError('El nombre es requerido');
      return;
    }
    
    if (nombre.trim().length < 2) {
      setError('El nombre debe tener al menos 2 caracteres');
      return;
    }

    onSubmit({
      nombre: nombre.trim(),
      pais: pais.trim() || null,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label className="block text-gray-300 text-sm font-medium mb-2">
            Nombre de la Liga *
          </label>
          <input
            type="text"
            value={nombre}
            onChange={(e) => {
              setNombre(e.target.value);
              setError('');
            }}
            placeholder="Ej: La Liga, Premier League"
            className={`w-full px-4 py-3 rounded-xl bg-dark-bg border ${
              error ? 'border-red-500' : 'border-dark-border'
            } text-white placeholder-gray-500 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all`}
            autoFocus
          />
          {error && (
            <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </p>
          )}
        </div>

        <div>
          <label className="block text-gray-300 text-sm font-medium mb-2">
            País
          </label>
          <input
            type="text"
            value={pais}
            onChange={(e) => setPais(e.target.value)}
            placeholder="Ej: España, Inglaterra"
            className="w-full px-4 py-3 rounded-xl bg-dark-bg border border-dark-border text-white placeholder-gray-500 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all"
          />
        </div>
      </div>

      <div className="flex gap-3 mt-6">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 bg-accent-green hover:bg-accent-green/90 disabled:bg-accent-green/50 text-dark-bg font-bold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>Guardando...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span>{isEditando ? 'Actualizar' : 'Crear'} Liga</span>
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-6 py-3 bg-dark-border hover:bg-dark-border/80 disabled:opacity-50 text-white font-medium rounded-xl transition-all"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
