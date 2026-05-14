import { useState, type FormEvent } from 'react';
import type { ProjectCreate } from '../../types';

interface Props { onSubmit: (data: ProjectCreate) => Promise<void>; loading: boolean; }

export default function ProjectForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<ProjectCreate>({
    name: '', research_goal: '', exposure: '', outcome: '', mediator_set: '',
  });

  const handle = async (e: FormEvent) => { e.preventDefault(); await onSubmit(form); };

  const field = (label: string, key: keyof ProjectCreate, required = false) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="text" value={form[key]} required={required}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

  return (
    <form onSubmit={handle} className="space-y-4 max-w-lg">
      {field('Project Name *', 'name', true)}
      {field('Research Goal', 'research_goal')}
      {field('Exposure (e.g. Liver_PDFF)', 'exposure')}
      {field('Outcome (e.g. Osteoporosis)', 'outcome')}
      {field('Mediator Set', 'mediator_set')}
      <button type="submit" disabled={loading}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
        {loading ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  );
}
