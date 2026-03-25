import { useAppStore } from '../../stores/appStore';
import Header from './Header';
import Sidebar from './Sidebar';
import FieldDetailPanel from '../main/FieldDetailPanel';
import DashboardPanel from '../main/DashboardPanel';
import ChatPanel from '../main/ChatPanel';

export default function AppShell() {
  const { activeView } = useAppStore();

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        {activeView === 'explorer' && <Sidebar />}
        <main className="flex-1 overflow-auto">
          {activeView === 'explorer' ? <FieldDetailPanel /> : <DashboardPanel />}
        </main>
      </div>
      <ChatPanel />
    </div>
  );
}
