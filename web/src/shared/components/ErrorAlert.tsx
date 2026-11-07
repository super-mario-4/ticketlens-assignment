import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";

export function ErrorAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="size-4" aria-hidden />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}
