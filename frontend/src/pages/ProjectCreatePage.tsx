import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectForm from '../components/project/ProjectForm';
import PageShell from '../components/shared/PageShell';
import type { ProjectCreate } from '../types';

export default function ProjectCreatePage() {
  const { createProject, loading } = useProjectStore();
  const nav = useNavigate();

  const handle = async (data: ProjectCreate) => {
    const p = await createProject(data);
    nav(`/projects/${p.id}`);
  };

  return (
    <PageShell>
      <h2 className="text-2xl font-heading font-bold text-text-primary mb-2">新建项目</h2>
      <p className="text-sm text-text-muted mb-6">配置您的医学科研分析项目</p>
      <ProjectForm onSubmit={handle} loading={loading} />
    </PageShell>
  );
}
