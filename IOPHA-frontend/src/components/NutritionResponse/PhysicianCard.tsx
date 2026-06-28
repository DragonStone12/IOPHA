import { cn } from "../shared/utils";
import { Avatar, AvatarImage, AvatarFallback } from "../shared/avatar";
import { Button } from "../shared/button";

export interface Physician {
  id: string;
  name: string;
  specialty: string;
  distance: string;
  rating: number;
  reviewCount: number;
  nextAvailable: string;
  imageUrl?: string;
}

interface PhysicianCardProps {
  physician: Physician;
  onBook?: (physician: Physician) => void;
  className?: string;
}

export function PhysicianCard({
  physician,
  onBook,
  className,
}: PhysicianCardProps) {
  const initials = physician.name
    .replace(/^Dr\.\s*/i, "")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div
      className={cn(
        "bg-background border border-border rounded-xl p-4 flex gap-3 hover:border-primary/30 transition-colors",
        className,
      )}
    >
      <Avatar className="w-12 h-12 shrink-0">
        <AvatarImage
          src={physician.imageUrl}
          alt={physician.name}
          className="object-cover"
        />
        <AvatarFallback className="text-xs font-semibold text-primary">
          {initials}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-foreground truncate">
          {physician.name}
        </p>
        <p className="text-xs text-muted-foreground">{physician.specialty}</p>

        <div className="flex items-center gap-3 mt-1.5">
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-3 h-3"
              aria-hidden="true"
            >
              <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            {physician.distance}
          </span>
          <span
            className="flex items-center gap-1 text-xs text-muted-foreground"
            aria-label={`Rating ${physician.rating} out of 5 stars based on ${physician.reviewCount} reviews`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-3 h-3 text-yellow-400"
              aria-hidden="true"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            {physician.rating} ({physician.reviewCount})
          </span>
        </div>

        <div className="flex items-center justify-between mt-2.5">
          <span className="flex items-center gap-1 text-xs text-primary font-medium">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-3 h-3"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            {physician.nextAvailable}
          </span>
          <Button
            size="sm"
            onClick={() => onBook?.(physician)}
            aria-label={`Book appointment with ${physician.name}`}
            className="gap-1"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-3 h-3"
              aria-hidden="true"
            >
              <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
              <line x1="16" x2="16" y1="2" y2="6" />
              <line x1="8" x2="8" y1="2" y2="6" />
              <line x1="3" x2="21" y1="10" y2="10" />
            </svg>
            Book
          </Button>
        </div>
      </div>
    </div>
  );
}
