export function LigaCard({ liga = {}, onSelect, onEdit, onDelete, isLoading }) {
  const handleDelete = (e) => {
    e.stopPropagation();
    if (onDelete && liga?.id) onDelete(liga);
  };

  const handleEdit = (e) => {
    e.stopPropagation();
    if (onEdit && liga?.id) onEdit(liga);
  };

  const handleSelect = () => {
    if (onSelect && liga?.id) onSelect(liga);
  };

  return (
    <div
      onClick={handleSelect}
      className="group relative bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-accent-blue/50 transition-all duration-300 hover:shadow-xl hover:shadow-accent-blue/10 cursor-pointer hover:scale-[1.02]"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-14 h-14 bg-gradient-to-br from-accent-blue to-accent-purple rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-lg">
          <span className="text-3xl">⚽</span>
        </div>
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <button
            onClick={handleEdit}
            disabled={isLoading}
            className="p-2 rounded-lg bg-accent-blue/20 text-accent-blue hover:bg-accent-blue hover:text-white transition-all duration-200 disabled:opacity-50"
            title="Editar liga"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={handleDelete}
            disabled={isLoading}
            className="p-2 rounded-lg bg-red-500/20 text-red-500 hover:bg-red-500 hover:text-white transition-all duration-200 disabled:opacity-50"
            title="Eliminar liga"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      
      <h3 className="text-xl font-bold text-white mb-1 group-hover:text-accent-blue transition-colors duration-300">
        {liga.nombre || 'Sin nombre'}
      </h3>
      <p className="text-gray-400 text-sm flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        {liga.pais || 'Sin país'}
      </p>
      
      <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <svg className="w-6 h-6 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
}
