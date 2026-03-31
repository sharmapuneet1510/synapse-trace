import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { TraceView } from '../../features/trace-view/TraceView';
import { NodeDetailsPanel } from '../../features/node-details/NodeDetailsPanel';
import { ConfigPanel } from '../../features/config-panel/ConfigPanel';
import { LogsPanel } from '../../features/logs-panel/LogsPanel';
import { ChatPanel } from '../../features/chat/ChatPanel';
import { DerivationPanel } from '../../features/derivation/DerivationPanel';
import { ApiDocsPanel } from '../../features/api-docs/ApiDocsPanel';
import { useAppStore } from '../../store/appStore';

export function AppShell() {
  const { logsOpen, chatOpen, derivationOpen, apiDocsOpen } = useAppStore();

  const rightPanelOpen = chatOpen || derivationOpen || apiDocsOpen;
  const rightPanelWidth = apiDocsOpen ? 640 : 500;

  return (
    <div
      className="h-screen flex flex-col overflow-hidden"
      style={{ background: 'var(--bg-base)' }}
    >
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden relative transition-all duration-200">
          <div
            className="flex-1 overflow-hidden transition-all duration-200"
            style={{ marginRight: rightPanelOpen ? rightPanelWidth : 0 }}
          >
            <TraceView />
          </div>

          {logsOpen && (
            <div
              className="shrink-0 transition-all duration-200"
              style={{
                height: 160,
                borderTop: '1px solid var(--border)',
                marginRight: rightPanelOpen ? rightPanelWidth : 0,
              }}
            >
              <LogsPanel />
            </div>
          )}
        </main>

        {/* Node detail panel — only when no slide-in is open */}
        {!rightPanelOpen && <NodeDetailsPanel />}
      </div>

      {/* Slide-in panels */}
      <ChatPanel />
      <DerivationPanel />
      <ApiDocsPanel />

      {/* Modal */}
      <ConfigPanel />
    </div>
  );
}
