import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { metricsApi } from "../lib/api";

export function useAdminMetrics() {
  return useQuery({
    queryKey: ["/api/eval/metrics"],
    queryFn: () => metricsApi.getMetrics(),
    refetchInterval: 30000,
  });
}

export function useRunEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dataset: string) => metricsApi.runEvaluation(dataset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/eval/metrics"] });
    },
  });
}
