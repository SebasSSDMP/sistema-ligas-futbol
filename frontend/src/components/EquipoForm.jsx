import React from 'react';
import { useState, useEffect } from 'react';

export function EquipoForm({ equipo, onSubmit, onCancel, isSubmitting }) {
  const [nombre, setNombre] = useState('');
  const [error, setError] = useState('');

  const isEditando = !!equipo;

  useEffect(() => {
    if (equipo) {
      setNombre(equipo.nombre || '');
    } else {
      setNombre('');
    }
    setError('');
  }, [equipo]);

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
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-4">
        <label className="block text-gray-300 text-sm font-medium mb-2">
          Nombre del Equipo *
        </label>
        <input
          type="text"
          value={nombre}
          onChange={(e) => {
            setNombre(e.target.value);
            setError('');
          }}
          placeholder="Ej: Real Madrid, Barcelona"
          className={`w-full px-4 py-3 rounded-xl bg-dark-bg border ${
            error ? 'border-red-500' : 'border-dark-border'
          } text-white placeholder-gray-500 focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 outline-none transition-all`}
          autoFocus
        />
        {error && (
          <p className="mt-1 text-sm text-red-500">{error}</p>
        )}
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 bg-accent-blue hover:bg-accent-blue/90 disabled:bg-accent-blue/50 text-dark-bg font-bold py-3 px-6 rounded-xl transition-all flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span>Guardando...</span>
            </>
          ) : (
            <span>{isEditando ? 'Actualizar' : 'Crear'}</span>
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
