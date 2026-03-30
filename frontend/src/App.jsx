import { useState, useEffect, useCallback } from 'react';
import LigaDashboard from './components/LigaDashboard';
import ExplorarLigas from './components/ExplorarLigas';
import { LigaCard } from './components/LigaCard';
import { LigaForm } from './components/LigaForm';
import { Modal, ConfirmDialog } from './components/Modal';
import { Toast } from './components/Toast';
import GlobalLoader from './components/GlobalLoader';
import { obtenerLigas, crearLiga, actualizarLiga, eliminarLiga, resetDatabase } from './api';

function App() {
  const [vista, setVista] = useState('ligas');
  const [ligaSeleccionada, setLigaSeleccionada] = useState(null);
  const [ligas, setLigas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Modales
  const [mostrarForm, setMostrarForm] = useState(false);
  const [mostrarConfirm, setMostrarConfirm] = useState(false);
  const [mostrarResetConfirm, setMostrarResetConfirm] = useState(false);
  const [ligaEditando, setLigaEditando] = useState(null);
  const [ligaEliminando, setLigaEliminando] = useState(null);
  
  // Notificaciones
  const [toast, setToast] = useState(null);
  
  // Validar que ligas sea siempre un array
  const ligasData = Array.isArray(ligas) ? ligas : [];

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
  }, []);

  const hideToast = useCallback(() => {
    setToast(null);
  }, []);

  useEffect(() => {
    cargarLigas();
  }, []);

  const cargarLigas = async () => {
    setLoading(true);
    try {
      const data = await obtenerLigas();
      setLigas(Array.isArray(data) ? data : []);
    } catch (error) {
      showToast('Error al cargar las ligas', 'error');
      setLigas([]);
    } finally {
      setLoading(false);
    }
  };

  const seleccionarLiga = (liga) => {
    setLigaSeleccionada(liga);
    setVista('liga');
  };

  const volver = () => {
    setLigaSeleccionada(null);
    setVista('ligas');
    cargarLigas();
  };

  // ABRIR FORMULARIOS
  const abrirFormCrear = () => {
    setLigaEditando(null);
    setMostrarForm(true);
  };

  const abrirFormEditar = (liga) => {
    setLigaEditando(liga);
    setMostrarForm(true);
  };

  // CREAR / ACTUALIZAR
  const handleSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      if (ligaEditando) {
        await actualizarLiga(ligaEditando.id, data);
        showToast('Liga actualizada correctamente', 'success');
      } else {
        await crearLiga(data);
        showToast('Liga creada correctamente', 'success');
      }
      setMostrarForm(false);
      setLigaEditando(null);
      cargarLigas();
    } catch (error) {
      showToast(error.message || 'Error al guardar la liga', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // ELIMINAR
  const confirmarEliminar = (liga) => {
    setLigaEliminando(liga);
    setMostrarConfirm(true);
  };

  const handleEliminar = async () => {
    if (!ligaEliminando) return;
    
    setIsSubmitting(true);
    try {
      await eliminarLiga(ligaEliminando.id);
      showToast('Liga eliminada correctamente', 'success');
      setMostrarConfirm(false);
      setLigaEliminando(null);
      cargarLigas();
    } catch (error) {
      showToast(error.message || 'Error al eliminar la liga', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // RESET DATABASE
  const handleResetDatabase = async () => {
    setIsSubmitting(true);
    try {
      await resetDatabase();
      showToast('Base de datos limpiada correctamente', 'success');
      setMostrarResetConfirm(false);
      cargarLigas();
      setLigaSeleccionada(null);
      setVista('ligas');
    } catch (error) {
      showToast(error.message || 'Error al limpiar la base de datos', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-accent-blue border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Cargando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <header className="bg-dark-card border-b border-dark-border sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {(vista === 'liga' || vista === 'explorar') && (
                <button 
                  onClick={() => { setVista('ligas'); setLigaSeleccionada(null); }}
                  className="text-gray-400 hover:text-white transition-all p-2 hover:bg-dark-border rounded-lg"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
              )}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-accent-blue to-accent-purple rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-2xl">⚽</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Fútbol Stats</h1>
                  <p className="text-xs text-gray-400">Gestión de Ligas</p>
                </div>
              </div>
            </div>
            <nav className="flex items-center gap-2">
              <button
                onClick={() => { setVista('ligas'); setLigaSeleccionada(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  vista === 'ligas' 
                    ? 'bg-accent-blue text-dark-bg shadow-lg shadow-accent-blue/30' 
                    : 'text-gray-400 hover:text-white hover:bg-dark-border'
                }`}
              >
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  Mis Ligas
                </span>
              </button>
              <button
                onClick={() => { setVista('explorar'); setLigaSeleccionada(null); }}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  vista === 'explorar' 
                    ? 'bg-accent-purple text-white shadow-lg shadow-accent-purple/30' 
                    : 'text-gray-400 hover:text-white hover:bg-dark-border'
                }`}
              >
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  Explorar
                </span>
              </button>
              <button
                onClick={() => setMostrarResetConfirm(true)}
                className="px-4 py-2 rounded-lg font-medium text-gray-400 hover:text-white hover:bg-dark-border transition-all flex items-center gap-2"
                title="Limpiar base de datos"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reset
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {vista === 'ligas' && (
          <div>
            {/* Header Section */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">Ligas de Fútbol</h2>
                  <p className="text-gray-400">Gestiona todas las ligas del sistema</p>
                </div>
                <button
                  onClick={abrirFormCrear}
                  className="bg-accent-green hover:bg-accent-green/90 text-dark-bg font-bold px-6 py-3 rounded-xl transition-all shadow-lg shadow-green-500/20 flex items-center gap-2 hover:scale-105"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Agregar Liga
                </button>
              </div>
            </div>
            
            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-accent-blue/20 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-accent-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Total Ligas</p>
                    <p className="text-2xl font-bold text-white">{ligasData.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-accent-green/20 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Activas</p>
                    <p className="text-2xl font-bold text-accent-green">{ligasData.length}</p>
                  </div>
                </div>
              </div>
              <div className="bg-dark-card rounded-xl p-4 border border-dark-border">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-accent-purple/20 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-accent-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Sistema</p>
                    <p className="text-2xl font-bold text-accent-purple">Online</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Empty State */}
            {ligasData.length === 0 ? (
              <div className="bg-dark-card rounded-2xl p-12 text-center border border-dark-border">
                <div className="w-24 h-24 bg-dark-border rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-5xl">🏆</span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">No hay ligas creadas</h3>
                <p className="text-gray-400 mb-6 max-w-md mx-auto">
                  Comienza agregando tu primera liga al sistema. Podrás gestionar temporadas, equipos y partidos.
                </p>
                <button
                  onClick={abrirFormCrear}
                  className="bg-accent-green hover:bg-accent-green/90 text-dark-bg font-bold px-8 py-4 rounded-xl transition-all shadow-lg shadow-green-500/20 inline-flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Crear Primera Liga
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {ligasData.map((liga) => (
                  <LigaCard
                    key={liga?.id || Math.random()}
                    liga={liga}
                    onSelect={seleccionarLiga}
                    onEdit={abrirFormEditar}
                    onDelete={confirmarEliminar}
                    isLoading={isSubmitting}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {vista === 'liga' && ligaSeleccionada && (
          <LigaDashboard liga={ligaSeleccionada} onVolver={volver} />
        )}

        {vista === 'explorar' && (
          <ExplorarLigas />
        )}
      </main>

      {/* Modal Crear/Editar */}
      <Modal
        isOpen={mostrarForm}
        onClose={() => { setMostrarForm(false); setLigaEditando(null); }}
        title={ligaEditando ? 'Editar Liga' : 'Nueva Liga'}
      >
        <LigaForm
          liga={ligaEditando}
          onSubmit={handleSubmit}
          onCancel={() => { setMostrarForm(false); setLigaEditando(null); }}
          isSubmitting={isSubmitting}
        />
      </Modal>

      {/* Modal Confirmar Eliminar */}
      <ConfirmDialog
        isOpen={mostrarConfirm}
        onClose={() => { setMostrarConfirm(false); setLigaEliminando(null); }}
        onConfirm={handleEliminar}
        title="¿Eliminar Liga?"
        message={`¿Estás seguro de eliminar "${ligaEliminando?.nombre || 'esta liga'}"? Esta acción eliminará todas las temporadas, equipos y partidos asociados.`}
        confirmText="Eliminar"
        cancelText="Cancelar"
        type="danger"
      />

      {/* Modal Confirmar Reset Database */}
      <ConfirmDialog
        isOpen={mostrarResetConfirm}
        onClose={() => setMostrarResetConfirm(false)}
        onConfirm={handleResetDatabase}
        title="¿Limpiar Base de Datos?"
        message="¿Estás seguro de eliminar TODOS los datos del sistema? Esta acción eliminará todas las ligas, temporadas, equipos y partidos."
        confirmText="Limpiar Todo"
        cancelText="Cancelar"
        type="danger"
      />

       {/* Toast Notifications */}
       {toast && <Toast {...toast} onClose={hideToast} />}
       
       {/* Global Loader and Error Handler */}
       <GlobalLoader />
     </div>
   );
 }
 
 export default App;
