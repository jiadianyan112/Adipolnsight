import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectForm from '../components/project/ProjectForm';
import type { ProjectCreate } from '../types';

export default function ProjectCreatePage() {
  const { createProject, loading } = useProjectStore();
  const nav = useNavigate();

  const handle = async (data: ProjectCreate) => {
    const p = await createProject(data);
    nav(`/projects/${p.id}`);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">New Project</h2>
      <ProjectForm onSubmit={handle} loading={loading} />
    </div>
  );
}
