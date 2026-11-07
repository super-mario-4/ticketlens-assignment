import { useEffect, useState } from "react";
import { errorMessage } from "@/shared/api/errors";

/** Runs `load` on mount and whenever it changes, so callers pass a stable function.
 *  The last result stays on screen while the next one loads or if it fails. */
export function useRequest<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let current = true;
    setLoading(true);
    load()
      .then((next) => {
        if (!current) return;
        setData(next);
        setError("");
      })
      .catch((caught: unknown) => {
        if (current) setError(errorMessage(caught));
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
    };
  }, [load]);

  return { data, error, loading, setData };
}
