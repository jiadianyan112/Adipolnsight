import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectCard from '../components/project/ProjectCard';
import PageShell from '../components/shared/PageShell';
import PrimaryButton from '../components/shared/PrimaryButton';
import SecondaryButton from '../components/shared/SecondaryButton';

export default function ProjectListPage() {
  const { projects, loading, fetchProjects, deleteProject, createDemo } = useProjectStore();
  const nav = useNavigate();

  useEffect(() => { fetchProjects(); }, []);

  const handleDemo = async () => {
    const p = await createDemo();
    nav(`/projects/${p.id}`);
  };

  return (
    <PageShell>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-heading font-bold text-text-primary">项目列表</h2>
          <p className="text-sm text-text-muted mt-1">管理您的医学科研分析项目</p>
        </div>
        <div className="flex gap-2">
          <SecondaryButton onClick={handleDemo}>
            一键创建示例
          </SecondaryButton>
          <PrimaryButton onClick={() => nav('/projects/new')}>
            新建项目
          </PrimaryButton>
        </div>
      </div>
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="flex items-center gap-3 text-text-muted">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="font-heading">加载项目列表...</span>
          </div>
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 text-text-muted">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-alt flex items-center justify-center">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-lg font-heading font-medium mb-1">暂无项目</p>
          <p className="text-sm">点击"一键创建示例"或"新建项目"开始使用</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDelete={deleteProject} />
          ))}
        </div>
      )}
    </PageShell>
  );
}
