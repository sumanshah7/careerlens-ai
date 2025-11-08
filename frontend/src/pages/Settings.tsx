import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

interface AlertRule {
  id: string;
  role: string;
  location: string;
  minMatch: number;
  frequency: string;
}

export const Settings = () => {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [formData, setFormData] = useState({
    role: '',
    location: '',
    minMatch: 70,
    frequency: 'daily',
  });

  useEffect(() => {
    // Load rules from localStorage
    const saved = localStorage.getItem('alertRules');
    if (saved) {
      setRules(JSON.parse(saved));
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newRule: AlertRule = {
      id: Date.now().toString(),
      ...formData,
    };
    const updated = [...rules, newRule];
    setRules(updated);
    localStorage.setItem('alertRules', JSON.stringify(updated));
    toast.success('Alert rule created');
    setFormData({
      role: '',
      location: '',
      minMatch: 70,
      frequency: 'daily',
    });
  };

  const handleDelete = (id: string) => {
    const updated = rules.filter((r) => r.id !== id);
    setRules(updated);
    localStorage.setItem('alertRules', JSON.stringify(updated));
    toast.success('Alert rule deleted');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your alert rules and preferences</p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Create Alert Rule</CardTitle>
          <CardDescription>
            Get notified when new jobs match your criteria
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                placeholder="e.g., Senior Frontend Engineer"
                required
              />
            </div>
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g., San Francisco, CA or Remote"
                required
              />
            </div>
            <div>
              <Label htmlFor="minMatch">Minimum Match %</Label>
              <Input
                id="minMatch"
                type="number"
                min="0"
                max="100"
                value={formData.minMatch}
                onChange={(e) =>
                  setFormData({ ...formData, minMatch: parseInt(e.target.value) })
                }
                required
              />
            </div>
            <div>
              <Label htmlFor="frequency">Frequency</Label>
              <Select
                value={formData.frequency}
                onValueChange={(value) => setFormData({ ...formData, frequency: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit">Create Rule</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Active Alert Rules</CardTitle>
          <CardDescription>Your saved alert rules</CardDescription>
        </CardHeader>
        <CardContent>
          {rules.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No alert rules created yet
            </p>
          ) : (
            <div className="space-y-4">
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <div className="font-semibold">{rule.role}</div>
                    <div className="text-sm text-muted-foreground">
                      {rule.location} • Min {rule.minMatch}% match • {rule.frequency}
                    </div>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(rule.id)}
                  >
                    Delete
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

