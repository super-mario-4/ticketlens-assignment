import { Search, X } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { CATEGORY, STATUS } from "@/shared/lib/labels";
import type { Meta, TicketFilterValues } from "../types";

// Radix Select does not allow an empty item value.
const ALL = "all";

type FilterSelectProps = {
  label: string;
  value: string;
  options: string[];
  names?: Record<string, string>;
  onChange: (value: string) => void;
};

function FilterSelect({ label, value, options, names = {}, onChange }: FilterSelectProps) {
  return (
    <Select
      value={value || ALL}
      onValueChange={(next) => onChange(next === ALL ? "" : next)}
    >
      <SelectTrigger aria-label={label} className="bg-card">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>{label}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option} value={option}>
            {names[option] ?? option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

type Props = {
  meta: Meta | null;
  review: boolean;
  filters: TicketFilterValues;
  filtered: boolean;
  onFilter: (name: keyof TicketFilterValues, value: string) => void;
  onSearch: (text: string) => void;
  onClear: () => void;
};

export function TicketFilters({
  meta,
  review,
  filters,
  filtered,
  onFilter,
  onSearch,
  onClear,
}: Props) {
  const [text, setText] = useState("");

  function submit(event: FormEvent) {
    event.preventDefault();
    onSearch(text);
  }

  function clear() {
    setText("");
    onClear();
  }

  return (
    <div className="space-y-2">
      <form onSubmit={submit} role="search" className="flex gap-2">
        <Input
          aria-label="Matn bo‘yicha qidirish"
          className="bg-card sm:max-w-sm"
          placeholder="Matn bo‘yicha qidirish"
          maxLength={200}
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <Button type="submit" variant="outline" className="bg-card">
          <Search aria-hidden />
          Qidirish
        </Button>
        {filtered && (
          <Button type="button" variant="ghost" onClick={clear}>
            <X aria-hidden />
            <span className="hidden sm:inline">Tozalash</span>
            <span className="sr-only sm:hidden">Tozalash</span>
          </Button>
        )}
      </form>
      {meta && (
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3 lg:grid-cols-5">
          <FilterSelect
            label="Kategoriya"
            value={filters.category}
            options={meta.categories}
            names={CATEGORY}
            onChange={(value) => onFilter("category", value)}
          />
          <FilterSelect
            label="Ustuvorlik"
            value={filters.priority}
            options={meta.priorities}
            onChange={(value) => onFilter("priority", value)}
          />
          <FilterSelect
            label="Jamoa"
            value={filters.team}
            options={meta.teams}
            onChange={(value) => onFilter("team", value)}
          />
          <FilterSelect
            label="Kanal"
            value={filters.channel}
            options={meta.channels}
            onChange={(value) => onFilter("channel", value)}
          />
          {!review && (
            <FilterSelect
              label="Holat"
              value={filters.status}
              options={meta.statuses}
              names={STATUS}
              onChange={(value) => onFilter("status", value)}
            />
          )}
        </div>
      )}
    </div>
  );
}
