import {
  BarChart3,
  ClipboardCheck,
  Inbox,
  LogOut,
  type LucideIcon,
  Menu,
  Upload,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router";
import { type Role, type Session, setSession } from "@/shared/api/session";
import { Button } from "@/shared/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/shared/components/ui/sheet";
import { cn } from "@/shared/lib/utils";

type NavItem = { to: string; label: string; icon: LucideIcon; role?: Role };

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Navbat", icon: Inbox },
  { to: "/review", label: "Qo‘lda tekshirish", icon: ClipboardCheck },
  { to: "/import", label: "Import", icon: Upload, role: "operator" },
  { to: "/stats", label: "Statistika", icon: BarChart3, role: "lead" },
];

const ROLE_NAME: Record<Role, string> = { operator: "operator", lead: "rahbar" };

function NavItems({ items, onNavigate }: { items: NavItem[]; onNavigate?: () => void }) {
  return items.map(({ to, label, icon: Icon }) => (
    <NavLink
      key={to}
      to={to}
      end
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
          isActive
            ? "bg-accent text-accent-foreground"
            : "text-muted-foreground hover:bg-muted hover:text-foreground",
        )
      }
    >
      <Icon className="size-4" aria-hidden />
      {label}
    </NavLink>
  ));
}

export function AppLayout({ session }: { session: Session }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const items = NAV_ITEMS.filter((item) => !item.role || item.role === session.role);
  const user = `${session.username} (${ROLE_NAME[session.role]})`;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b bg-card">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-2 px-4">
          <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="-ml-2 md:hidden" aria-label="Menyu">
                <Menu aria-hidden />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72" aria-describedby={undefined}>
              <SheetHeader>
                <SheetTitle>TicketLens</SheetTitle>
              </SheetHeader>
              <nav className="mt-4 grid gap-1">
                <NavItems items={items} onNavigate={() => setMenuOpen(false)} />
              </nav>
              <p className="mt-4 border-t px-3 pt-4 text-sm text-muted-foreground">{user}</p>
            </SheetContent>
          </Sheet>

          <span className="mr-4 font-semibold">TicketLens</span>
          <nav className="hidden items-center gap-1 md:flex">
            <NavItems items={items} />
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <span className="hidden text-sm text-muted-foreground md:inline">{user}</span>
            <Button variant="outline" size="sm" onClick={() => setSession(null)}>
              <LogOut aria-hidden />
              Chiqish
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
