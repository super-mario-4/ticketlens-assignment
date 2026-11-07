import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { LoginForm } from "../components/LoginForm";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>
            <h1>TicketLens</h1>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </div>
  );
}
