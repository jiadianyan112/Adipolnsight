import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../stores/projectStore';
import ProjectCard from '../components/project/ProjectCard';

export default function ProjectListPage() {
  const { projects, loading, fetchProjects, deleteProject, createDemo } = useProjectStore();
  const nav = useNavigate();

  useEffect(() => { fetchProjects(); }, []);

  const handleDemo = async () => {
    const p = await createDemo();
    nav(`/projects/${p.id}`);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Projects</h2>
        <div className="flex gap-2">
          <button onClick={handleDemo}
            className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
            One-Click Demo
          </button>
          <button onClick={() => nav('/projects/new')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
            New Project
          </button>
        </div>
      </div>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg mb-2">No projects yet</p>
          <p>Click "One-Click Demo" or "New Project" to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDelete={deleteProject} />
          ))}
        </div>
      )}
    </div>
  );
}
