import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const loc = useLocation();
  const linkCls = (p: string) =>
    `block px-4 py-2 rounded-lg text-sm ${loc.pathname === p ? 'bg-blue-100 text-blue-800 font-medium' : 'text-gray-600 hover:bg-gray-100'}`;

  return (
    <aside className="w-56 bg-white border-r border-gray-200 p-4 flex flex-col">
      <h1 className="text-lg font-bold text-gray-800 mb-6">AdipoInsight</h1>
      <nav className="flex-1 space-y-1">
        <Link to="/" className={linkCls('/')}>Projects</Link>
      </nav>
      <div className="text-xs text-gray-400 pt-4 border-t">v0.1.0 Mock-First</div>
    </aside>
  );
}
