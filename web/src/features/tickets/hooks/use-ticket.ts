import { useCallback, useState } from "react";
import { errorMessage } from "@/shared/api/errors";
import { useRequest } from "@/shared/hooks/use-request";
import { correctTicket, fetchTicket, reclassifyTicket } from "../api/tickets";
import type { CorrectionRequest, TicketDetail } from "../types";

export function useTicket(id: string) {
  const load = useCallback(() => fetchTicket(id), [id]);
  const { data: ticket, error: loadError, setData } = useRequest(load);
  const [actionError, setActionError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<TicketDetail>, saving: boolean): Promise<void> {
    setBusy(true);
    setActionError("");
    setSaved(false);
    try {
      setData(await action());
      setSaved(saving);
    } catch (caught) {
      setActionError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  function correct(correction: CorrectionRequest): Promise<void> {
    return run(() => correctTicket(id, correction), true);
  }

  function reclassify(): Promise<void> {
    return run(async () => {
      await reclassifyTicket(id);
      return fetchTicket(id);
    }, false);
  }

  return { ticket, loadError, actionError, saved, busy, correct, reclassify };
}
