import { useState, useEffect, useCallback } from 'react';

export default function SearchBar({ 
  value, 
  onChange, 
  placeholder = "Buscar...", 
  onClear,
  countries = [],
  selectedCountry,
  onCountryChange,
  resultCount,
  totalCount
}) {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [localValue, onChange]);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleClear = () => {
    setLocalValue('');
    onChange('');
    if (onClear) onClear();
  };

  const showDropdown = countries && countries.length > 0;

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            placeholder={placeholder}
            className="w-full pl-12 pr-10 py-3 bg-dark-bg border border-dark-border rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 transition-all duration-200"
          />
          {localValue && (
            <button
              onClick={handleClear}
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        
        {showDropdown && (
          <select
            value={selectedCountry || ''}
            onChange={(e) => onCountryChange(e.target.value || null)}
            className="px-4 py-3 bg-dark-bg border border-dark-border rounded-xl text-white focus:outline-none focus:border-accent-purple focus:ring-2 focus:ring-accent-purple/20 transition-all min-w-[160px]"
          >
            <option value="">Todos los países</option>
            {countries.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>
        )}
      </div>
      
      {resultCount !== undefined && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-gray-400">
            {localValue || selectedCountry ? (
              <span>
                {resultCount === 0 ? (
                  <span className="text-gray-500">No se encontraron resultados</span>
                ) : (
                  <>
                    Mostrando <span className="text-accent-blue font-semibold">{resultCount}</span> de {totalCount} ligas
                  </>
                )}
              </span>
            ) : (
              <span>{totalCount} ligas disponibles</span>
            )}
          </p>
          {(localValue || selectedCountry) && resultCount === 0 && (
            <button
              onClick={() => {
                handleClear();
                if (onCountryChange) onCountryChange(null);
              }}
              className="text-accent-blue hover:text-accent-blue/80 transition-colors"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      )}
    </div>
  );
}
