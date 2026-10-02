/** Format integer paise as Indian rupees, e.g. 150000 -> "₹1,500.00". */
export function formatPaise(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(rupees);
}

/** Parse a rupee string/number to integer paise. */
export function rupeesToPaise(rupees: number | string): number {
  const n = typeof rupees === "string" ? parseFloat(rupees) : rupees;
  return Math.round((Number.isFinite(n) ? n : 0) * 100);
}
