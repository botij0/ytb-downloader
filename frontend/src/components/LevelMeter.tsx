export type MeterTone = "queued" | "active" | "done" | "failed";

const SEGMENT_COUNT = 16;
const SEGMENT_KEYS = Array.from(
  { length: SEGMENT_COUNT },
  (_, index) => `cell-${index}`,
);

const TONE_FILL: Record<MeterTone, string> = {
  queued: "bg-[var(--frost)]/40",
  active: "bg-[var(--amber)]",
  done: "bg-[var(--mint)]",
  failed: "bg-[var(--ember)]",
};

type LevelMeterProps = {
  percent: number;
  tone: MeterTone;
  label: string;
  className?: string;
};

/**
 * Bar-graph level meter: the machine's progress, read at a glance.
 * Discrete cells rather than a smooth bar, so the reading is unambiguous.
 */
export function LevelMeter({
  percent,
  tone,
  label,
  className = "",
}: LevelMeterProps) {
  const clamped = Math.min(100, Math.max(0, percent));
  const lit = Math.round((clamped / 100) * SEGMENT_COUNT);

  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={`flex h-3.5 items-stretch gap-[2px] ${className}`}
    >
      {SEGMENT_KEYS.map((key, index) => (
        <span
          key={key}
          aria-hidden="true"
          className={`meter-cell min-w-[2px] flex-1 rounded-[1px] transition-colors duration-300 ${
            index < lit ? TONE_FILL[tone] : "bg-[var(--frost)]/10"
          }`}
        />
      ))}
    </div>
  );
}
