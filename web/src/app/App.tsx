import { HashRouter } from "react-router";
import { AppRoutes } from "./routes";

export function App() {
  return (
    <HashRouter>
      <AppRoutes />
    </HashRouter>
  );
}
