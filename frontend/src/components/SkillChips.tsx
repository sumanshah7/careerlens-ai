import { Skill } from '../types';
import { cn } from '../lib/utils';

interface SkillChipsProps {
  skills: Skill[];
  groupBy?: 'level' | 'status';
}

export const SkillChips = ({ skills, groupBy = 'level' }: SkillChipsProps) => {
  const grouped = skills.reduce((acc, skill) => {
    const key = skill[groupBy];
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(skill);
    return acc;
  }, {} as Record<string, Skill[]>);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'have':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'gap':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'learning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'core':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'adjacent':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'advanced':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([key, groupSkills]) => (
        <div key={key}>
          <h3 className="text-sm font-semibold mb-2 capitalize">{key}</h3>
          <div className="flex flex-wrap gap-2">
            {groupSkills.map((skill) => (
              <span
                key={skill.name}
                className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium border',
                  groupBy === 'status' ? getStatusColor(skill.status) : getLevelColor(skill.level)
                )}
              >
                {skill.name}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

