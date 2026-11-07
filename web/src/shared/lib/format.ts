export function dateText(value: string): string {
  return new Date(value).toLocaleString("uz-UZ", { dateStyle: "short", timeStyle: "short" });
}
