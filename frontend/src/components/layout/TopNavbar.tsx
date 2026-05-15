import { Link, useLocation } from 'react-router-dom';

export default function TopNavbar() {
  const loc = useLocation();
  const isAnalysisCenter = loc.pathname.startsWith('/projects');

  const navLinkCls = (active: boolean) =>
    `relative px-3 py-1.5 text-sm font-medium rounded-md transition-card ${
      active
        ? 'text-white bg-white/10'
        : 'text-navy-200 hover:text-white hover:bg-white/5'
    }`;

  return (
    <header className="navbar-dark h-14 flex items-center px-4 md:px-6 select-none z-50 relative" role="banner">
      {/* Brand */}
      <Link to="/" className="flex items-center gap-2 md:gap-2.5 mr-4 md:mr-8 shrink-0" aria-label="AdipoInsight home">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" className="shrink-0" aria-hidden="true">
          <rect width="32" height="32" rx="8" fill="white" fillOpacity="0.12" />
          <circle cx="16" cy="12" r="4" stroke="white" strokeWidth="1.5" fill="none" />
          <path d="M12 28c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
          <circle cx="16" cy="12" r="1.5" fill="white" />
          <circle cx="11.5" cy="11" r="0.8" fill="white" fillOpacity="0.6" />
          <circle cx="20.5" cy="11" r="0.8" fill="white" fillOpacity="0.6" />
          <path d="M10 10l-2-2M22 10l2-2" stroke="white" strokeWidth="1" strokeLinecap="round" opacity="0.5" />
        </svg>
        <span className="hidden sm:inline text-white font-heading font-semibold text-base tracking-tight">
          AdipoInsight
        </span>
      </Link>

      {/* Nav Links */}
      <nav className="flex items-center gap-0.5 md:gap-1" aria-label="Main navigation">
        <Link to="/" className={navLinkCls(false)}>
          我的数据
        </Link>
        <Link to="/projects/3" className={navLinkCls(isAnalysisCenter)}>
          分析中心
        </Link>
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* User */}
      <button
        className="flex items-center gap-1.5 md:gap-2 text-sm text-navy-200 hover:text-white transition-card rounded-lg px-2 py-1"
        aria-label="User menu"
      >
        <div className="w-7 h-7 md:w-8 md:h-8 rounded-full bg-white/15 flex items-center justify-center text-white font-heading font-medium text-[10px] md:text-xs" aria-hidden="true">
          DR
        </div>
        <svg className="w-3 h-3 hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
    </header>
  );
}
