import { Navigate, Outlet, Route, Routes } from "react-router";
import { LoginPage } from "@/features/auth";
import { ImportPage } from "@/features/imports";
import { StatsPage } from "@/features/stats";
import { QueuePage, ReviewQueuePage, TicketDetailPage } from "@/features/tickets";
import { type Role, useSession } from "@/shared/api/session";
import { AppLayout } from "./layout/AppLayout";

// The login screen replaces the page, so the URL survives signing in.
function RequireSession() {
  const session = useSession();
  return session ? <AppLayout session={session} /> : <LoginPage />;
}

function RequireRole({ role }: { role: Role }) {
  return useSession()?.role === role ? <Outlet /> : <Navigate to="/" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<RequireSession />}>
        <Route index element={<QueuePage />} />
        <Route path="review" element={<ReviewQueuePage />} />
        <Route path="tickets/:id" element={<TicketDetailPage />} />
        <Route element={<RequireRole role="operator" />}>
          <Route path="import" element={<ImportPage />} />
        </Route>
        <Route element={<RequireRole role="lead" />}>
          <Route path="stats" element={<StatsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
