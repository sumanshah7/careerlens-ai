import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface ScoreDonutProps {
  score: number;
}

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

export const ScoreDonut = ({ score }: ScoreDonutProps) => {
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={80}
          outerRadius={120}
          startAngle={90}
          endAngle={-270}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={index === 0 ? COLORS[0] : '#e5e7eb'} />
          ))}
        </Pie>
        <Tooltip />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-4xl font-bold fill-foreground"
        >
          {score}
        </text>
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

