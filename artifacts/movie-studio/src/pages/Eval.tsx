import { ShieldAlert, Play, CheckCircle2, XCircle, Shield } from "lucide-react";
import { Card, Button, Badge } from "../components/UI";
import { useAdminMetrics, useRunEval } from "../hooks/use-metrics";
import type { EvalMetric, AdversarialResult } from "../lib/types";

export default function Eval() {
  const { data: metrics } = useAdminMetrics();
  const runEval = useRunEval();

  const evalData = metrics?.last_eval_run;

  const handleRun = () => {
    runEval.mutate("movie_eval_set");
  };

  const adversarialResults: AdversarialResult[] = evalData?.adversarial_results || [];

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto h-full overflow-y-auto">
      <div className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-display font-bold text-white mb-2">Evaluation Suite</h2>
          <p className="text-muted-foreground">Run automated RAGAS and custom metric evaluations.</p>
        </div>
        <Button onClick={handleRun} disabled={runEval.isPending} className="py-6 px-8 rounded-full shadow-lg shadow-primary/20">
          <Play className={`w-5 h-5 mr-2 ${runEval.isPending ? 'animate-pulse' : ''}`} />
          {runEval.isPending ? 'Running Suite...' : 'Run Full Evaluation'}
        </Button>
      </div>

      {evalData ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 bg-gradient-to-br from-card to-black">
              <p className="text-sm text-muted-foreground mb-1">Pass Rate</p>
              <h3 className="text-4xl font-display font-bold text-white mb-2">
                {Math.round((evalData.passed / (evalData.passed + evalData.failed)) * 100)}%
              </h3>
              <div className="flex gap-2 text-sm font-medium">
                <span className="text-green-400">{evalData.passed} Passed</span>
                <span className="text-white/20">&bull;</span>
                <span className="text-red-400">{evalData.failed} Failed</span>
              </div>
            </Card>
            <Card className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Dataset</p>
              <h3 className="text-2xl font-display font-bold text-white mb-2">{evalData.dataset_name}</h3>
              <Badge variant="outline">{evalData.total_queries} Test Cases</Badge>
            </Card>
            <Card className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Run ID</p>
              <h3 className="text-2xl font-mono text-white mb-2">{evalData.run_id}</h3>
              <p className="text-sm text-muted-foreground">{new Date(evalData.timestamp).toLocaleString()}</p>
            </Card>
          </div>

          <Card className="overflow-hidden border-white/10">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="p-4 text-sm font-semibold text-white/80">Metric Name</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Description</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Score</th>
                  <th className="p-4 text-sm font-semibold text-white/80">Threshold</th>
                  <th className="p-4 text-sm font-semibold text-white/80 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {evalData.metrics.map((m: EvalMetric, i: number) => (
                  <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                    <td className="p-4 font-medium text-white capitalize">{m.name.replace(/_/g, ' ')}</td>
                    <td className="p-4 text-sm text-muted-foreground max-w-xs truncate" title={m.description}>{m.description}</td>
                    <td className="p-4 font-mono text-primary">{(m.value * 100).toFixed(1)}%</td>
                    <td className="p-4 font-mono text-muted-foreground">{m.threshold !== null ? `>${(m.threshold * 100).toFixed(0)}%` : '—'}</td>
                    <td className="p-4 text-right">
                      {m.passed ? (
                        <Badge variant="success"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> PASS</Badge>
                      ) : (
                        <Badge variant="error"><XCircle className="w-3.5 h-3.5 mr-1" /> FAIL</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="p-6 border-white/10">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-red-500/10 text-red-400 rounded-lg">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Adversarial Prompt Injection Tests</h3>
                <p className="text-sm text-muted-foreground">Tests for prompt injection, jailbreak, and boundary violations</p>
              </div>
            </div>
            {adversarialResults.length === 0 ? (
              <p className="text-muted-foreground text-center py-6">No adversarial test results in this evaluation run. Include adversarial test cases in your dataset to see results here.</p>
            ) : (
              <div className="space-y-3">
                {adversarialResults.map((result, i) => (
                  <div key={i} className={`p-4 rounded-lg border ${result.passed ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white mb-1 truncate" title={result.prompt}>{result.prompt}</p>
                        <p className="text-xs text-muted-foreground">Expected: {result.expected_behavior}</p>
                        <p className="text-xs text-muted-foreground mt-1">Actual: {result.actual_behavior}</p>
                      </div>
                      {result.passed ? (
                        <Badge variant="success"><CheckCircle2 className="w-3.5 h-3.5 mr-1" /> SAFE</Badge>
                      ) : (
                        <Badge variant="error"><XCircle className="w-3.5 h-3.5 mr-1" /> VULN</Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      ) : (
        <Card className="p-16 flex flex-col items-center justify-center text-center border-dashed border-white/20">
          <ShieldAlert className="w-16 h-16 text-muted-foreground mb-4" />
          <h3 className="text-xl font-medium text-white mb-2">No Evaluation Data</h3>
          <p className="text-muted-foreground max-w-sm">Click the button above to run the evaluation pipeline against the configured dataset.</p>
        </Card>
      )}
    </div>
  );
}
