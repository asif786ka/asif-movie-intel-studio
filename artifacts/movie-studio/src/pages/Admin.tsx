import { Activity, Database, Server, Clock, AlertTriangle, BarChart3, FileCheck } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card, Badge } from "../components/UI";
import { useAdminMetrics } from "../hooks/use-metrics";
import type { TraceSummary } from "../lib/types";

export default function Admin() {
  const { data, isLoading } = useAdminMetrics();

  if (isLoading || !data) return <div className="p-10 flex justify-center"><Activity className="w-8 h-8 animate-pulse text-primary" /></div>;

  const rd = data.route_distribution || {};
  const pieData = [
    { name: 'Structured (TMDB)', value: rd.structured_only || 0, color: 'hsl(var(--primary))' },
    { name: 'RAG Only', value: rd.rag_only || 0, color: 'hsl(190 90% 50%)' },
    { name: 'Hybrid', value: rd.hybrid || 0, color: 'hsl(280 80% 60%)' },
  ];

  const citationRate = typeof data.citation_rate === "number" ? data.citation_rate : (data.avg_citation_count > 0 ? 1 : 0);

  const statCards = [
    { label: "Vector Chunks", value: data.total_chunks, icon: Database, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Total Queries", value: data.total_queries, icon: Activity, color: "text-green-400", bg: "bg-green-500/10" },
    { label: "P95 Latency", value: `${Math.round(data.p95_latency_ms)}ms`, icon: Clock, color: "text-amber-400", bg: "bg-amber-500/10" },
    { label: "Citation Rate", value: `${(citationRate * 100).toFixed(1)}%`, icon: FileCheck, color: "text-cyan-400", bg: "bg-cyan-500/10" },
    { label: "Refusal Rate", value: `${(data.refusal_rate * 100).toFixed(1)}%`, icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10" },
    { label: "Avg Citations", value: data.avg_citation_count.toFixed(1), icon: BarChart3, color: "text-purple-400", bg: "bg-purple-500/10" },
  ];

  const recentTraces: TraceSummary[] = data.recent_traces || [];

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto h-full overflow-y-auto">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-display font-bold text-white mb-2">System Dashboard</h2>
          <p className="text-muted-foreground">Real-time metrics from the Asif Movie Intel Engine.</p>
        </div>
        <Badge variant="success" className="px-4 py-2 text-sm"><Server className="w-4 h-4 mr-2" /> System Healthy</Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-10">
        {statCards.map((stat, i) => (
          <Card key={i} className="p-5 flex flex-col justify-center relative overflow-hidden group hover:border-white/20 transition-colors">
            <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full blur-3xl opacity-50 ${stat.bg}`} />
            <stat.icon className={`w-5 h-5 mb-3 ${stat.color}`} />
            <h3 className="text-2xl font-display font-bold text-white mb-1">{stat.value}</h3>
            <p className="text-xs font-medium text-muted-foreground">{stat.label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-white mb-6">Routing Distribution</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={80} outerRadius={110} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />)}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '12px', color: 'white' }}
                  itemStyle={{ color: 'white' }}
                />
                <Legend verticalAlign="bottom" height={36} iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Prompt Versions</h3>
          <div className="space-y-4">
            {Object.entries(
              "prompts" in data.prompt_versions ? data.prompt_versions.prompts : data.prompt_versions
            ).map(([key, ver]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-white/5">
                <span className="text-sm font-medium text-white/80 capitalize">{key.replace(/_/g, ' ')}</span>
                <Badge variant="outline" className="font-mono text-xs text-primary bg-primary/10 border-primary/20">v{ver}</Badge>
              </div>
            ))}
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/10">
            <p className="text-sm text-muted-foreground mb-4">Guardrail Violations</p>
            <div className="flex items-center justify-between">
              <span className="text-white">Unsupported Claims</span>
              <span className="font-bold text-red-400">{(data.unsupported_claim_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-white/10 h-2 rounded-full mt-2 overflow-hidden">
              <div className="bg-red-500 h-full rounded-full" style={{ width: `${data.unsupported_claim_rate * 100}%` }} />
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-white mb-6">Recent Trace Summaries</h3>
        {recentTraces.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">No traces recorded yet. Start chatting to generate trace data.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="p-3 text-xs font-semibold text-white/80">Trace ID</th>
                  <th className="p-3 text-xs font-semibold text-white/80">Query</th>
                  <th className="p-3 text-xs font-semibold text-white/80">Route</th>
                  <th className="p-3 text-xs font-semibold text-white/80">Latency</th>
                  <th className="p-3 text-xs font-semibold text-white/80">Citations</th>
                  <th className="p-3 text-xs font-semibold text-white/80">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {recentTraces.map((trace) => (
                  <tr key={trace.trace_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-3 font-mono text-xs text-primary">{trace.trace_id.slice(0, 12)}...</td>
                    <td className="p-3 text-sm text-white max-w-xs truncate">{trace.query}</td>
                    <td className="p-3"><Badge variant="outline" className="text-xs capitalize">{trace.route_type}</Badge></td>
                    <td className="p-3 font-mono text-sm text-white">{trace.latency_ms}ms</td>
                    <td className="p-3 text-sm text-white">{trace.citation_count}</td>
                    <td className="p-3 text-xs text-muted-foreground">{new Date(trace.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
