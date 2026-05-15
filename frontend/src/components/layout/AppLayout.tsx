import { Outlet } from 'react-router-dom';
import TopNavbar from './TopNavbar';

export default function AppLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-surface">
      <TopNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
