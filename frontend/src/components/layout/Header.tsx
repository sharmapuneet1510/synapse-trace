import { useAppStore } from '../../stores/appStore';

export default function Header() {
  const { activeView, setActiveView, jurisdictionId, configType, chatOpen, setChatOpen } = useAppStore();

  return (
    <header
      className="h-[48px] flex items-center px-5 shrink-0 text-white select-none"
      style={{
        background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 40%, #991b1b 100%)',
        boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <div
          className="w-[30px] h-[30px] rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <div>
          <span className="text-[14px] font-bold tracking-[-0.01em] leading-none">Synapse Trace</span>
          <span className="text-[9px] text-white/40 ml-2 font-medium tracking-wider uppercase">Data Lineage</span>
        </div>
      </div>

      {/* Breadcrumb */}
      {jurisdictionId && activeView === 'explorer' && (
        <div className="ml-6 flex items-center gap-1.5 text-[12px]">
          <div className="w-px h-4 bg-white/20 mr-2" />
          <span className="text-white/50 font-medium">Explorer</span>
          <svg className="w-3 h-3 text-white/30" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M9 18l6-6-6-6" />
          </svg>
          <span className="font-semibold">{jurisdictionId.toUpperCase()}</span>
          {configType && (
            <>
              <svg className="w-3 h-3 text-white/30" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M9 18l6-6-6-6" />
              </svg>
              <span className="font-semibold">{configType}</span>
            </>
          )}
        </div>
      )}

      {/* Right nav */}
      <nav className="ml-auto flex items-center gap-1">
        {(['explorer', 'dashboard'] as const).map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className="relative px-4 py-1.5 text-[11px] font-semibold tracking-wider uppercase rounded-lg transition-all duration-150"
            style={{
              background: activeView === view ? 'rgba(255,255,255,0.2)' : 'transparent',
              color: activeView === view ? '#fff' : 'rgba(255,255,255,0.55)',
            }}
          >
            <span className="flex items-center gap-1.5">
              {view === 'explorer' ? (
                <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              ) : (
                <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              )}
              {view}
            </span>
          </button>
        ))}

        <div className="w-px h-5 bg-white/15 mx-1.5" />

        {/* Chat toggle */}
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className="relative flex items-center gap-1.5 px-3.5 py-1.5 text-[11px] font-semibold tracking-wider uppercase rounded-lg transition-all duration-150"
          style={{
            background: chatOpen ? 'rgba(255,255,255,0.2)' : 'transparent',
            color: chatOpen ? '#fff' : 'rgba(255,255,255,0.55)',
          }}
        >
          <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Chat
          {chatOpen && (
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          )}
        </button>
      </nav>
    </header>
  );
}
