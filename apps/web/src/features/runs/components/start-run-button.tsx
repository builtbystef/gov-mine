"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2Icon, PlayIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { institutionKeys } from "@/features/institutions/queries";
import { browserApi } from "@/lib/api/client";
import { errorMessage, unwrap } from "@/lib/api/errors";

import { runKeys } from "../queries";

/** Queues a full run of the institution from the dashboard and opens the Runs list. */
export function StartRunButton({ institutionId }: { institutionId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const start = useMutation({
    mutationFn: async () =>
      unwrap(
        await browserApi.POST("/runs", { body: { institution_id: institutionId, mode: "full" } }),
      ),
    onSuccess: async (run) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: runKeys.all }),
        queryClient.invalidateQueries({ queryKey: institutionKeys.all }),
      ]);
      toast.success(`Queued a full run of ${run.institution_name}`);
      router.push("/runs");
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  return (
    <Button size="sm" onClick={() => start.mutate()} disabled={start.isPending}>
      {start.isPending ? <Loader2Icon className="animate-spin" /> : <PlayIcon />}
      Start full run
    </Button>
  );
}
