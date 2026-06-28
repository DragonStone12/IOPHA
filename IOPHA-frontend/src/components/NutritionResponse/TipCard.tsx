import { cn } from "../shared/utils";

export interface Tip {
  id?: string;
  number: number;
  title: string;
  description: string;
}

interface TipCardProps {
  tip: Tip;
  className?: string;
}

export function TipCard({ tip, className }: TipCardProps) {
  return (
    <div
      className={cn(
        "bg-card border border-border rounded-xl p-4",
        className,
      )}
      role="listitem"
      aria-posinset={tip.number}
      aria-setsize={3}
    >
      <div className="flex gap-3">
        <span
          className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-mono font-bold flex items-center justify-center shrink-0 mt-0.5"
          aria-hidden="true"
        >
          {tip.number}
        </span>
        <div>
          <p className="text-sm font-semibold text-foreground leading-snug">
            {tip.title}
          </p>
          <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
            {tip.description}
          </p>
        </div>
      </div>
    </div>
  );
}
