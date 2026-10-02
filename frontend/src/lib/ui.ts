/**
 * Shared class strings for form controls, so inputs/labels/selects/tables are
 * styled consistently without a component per field. Token-driven (see style.css).
 */
export const inputClass =
  "w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/40 focus:border-ring disabled:opacity-60";

export const labelClass = "text-sm font-medium text-foreground/80";

export const selectClass = inputClass;

export const tableWrap =
  "rounded-xl border border-border bg-card overflow-hidden shadow-card";
export const theadClass = "bg-muted/60 text-left text-xs uppercase tracking-wide text-muted-foreground";
export const thClass = "px-4 py-2.5 font-medium";
export const rowClass = "border-t border-border transition-colors hover:bg-muted/40";
