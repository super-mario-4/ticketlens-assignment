import { useRequest } from "@/shared/hooks/use-request";
import { fetchMeta } from "../api/tickets";

export function useMeta() {
  const { data: meta, error } = useRequest(fetchMeta);
  return { meta, error };
}
