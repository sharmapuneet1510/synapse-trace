import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { TraceView } from '../../features/trace-view/TraceView';
import { NodeDetailsPanel } from '../../features/node-details/NodeDetailsPanel';
import { ConfigPanel } from '../../features/config-panel/ConfigPanel';
import { LogsPanel } from '../../features/logs-panel/LogsPanel';
import { useAppStore } from '../../store/appStore';

export function AppShell() {
  const { logsOpen } = useAppStore();

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden relative">
          <div className="flex-1 overflow-hidden">
            <TraceView />
          </div>
          {logsOpen && (
            <div className="h-44 shrink-0 border-t border-slate-700">
              <LogsPanel />
            </div>
          )}
        </main>

        <NodeDetailsPanel />
      </div>

      <ConfigPanel />
    </div>
  );
}
