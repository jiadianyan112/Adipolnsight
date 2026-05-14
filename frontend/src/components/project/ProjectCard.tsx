import { Link } from 'react-router-dom';
import type { Project } from '../../types';
import StatusBadge from '../shared/StatusBadge';

export default function ProjectCard({ project, onDelete }: { project: Project; onDelete: (id: number) => void }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-800">{project.name}</h3>
        <StatusBadge status={project.status} />
      </div>
      <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.research_goal}</p>
      <div className="flex gap-2 text-xs text-gray-400 mb-3">
        <span>Exposure: {project.exposure}</span>
        <span>|</span>
        <span>Outcome: {project.outcome}</span>
      </div>
      <div className="flex gap-2">
        <Link to={`/projects/${project.id}`} className="text-sm text-blue-600 hover:underline">
          Open Workspace →
        </Link>
        <button onClick={() => onDelete(project.id)} className="text-sm text-red-400 hover:text-red-600 ml-auto">
          Delete
        </button>
      </div>
    </div>
  );
}
