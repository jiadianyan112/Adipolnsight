import type { Project } from '../../types';
import StatusBadge from '../shared/StatusBadge';

export default function ProjectHeader({ project }: { project: Project }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{project.name}</h2>
          <p className="text-sm text-gray-500 mt-1">{project.research_goal}</p>
        </div>
        <StatusBadge status={project.status} />
      </div>
      <div className="flex gap-4 mt-3 text-sm text-gray-600">
        <span><strong>Exposure:</strong> {project.exposure}</span>
        <span><strong>Outcome:</strong> {project.outcome}</span>
        {project.mediator_set && <span><strong>Mediator:</strong> {project.mediator_set}</span>}
      </div>
    </div>
  );
}
