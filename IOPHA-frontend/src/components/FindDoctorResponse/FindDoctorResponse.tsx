import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import {
  PhysicianCard,
  type Physician,
} from "../NutritionResponse/PhysicianCard";
import { Button } from "../shared/button";

export interface Provider {
  id: string;
  name: string;
  credentials?: string;
  specialty: string;
  facility?: string;
  distanceMiles: number;
  rating: number;
  reviewCount: number;
  nextAvailableSlot: string;
  imageUrl: string;
}

export interface FollowUpAction {
  label: string;
  actionType: "BOOK_PROVIDER" | "PIVOT_TIPS";
  providerId?: string;
}

export interface FindDoctorResponseData {
  summaryText: string;
  providers: Provider[];
  followUpActions: FollowUpAction[];
}

interface FindDoctorResponseProps {
  data: FindDoctorResponseData;
  onBookProvider?: (providerId: string) => void;
  onChipSelect?: (chip: string) => void;
  timestamp?: string;
  className?: string;
}

const DEFAULT_DATA: FindDoctorResponseData = {
  summaryText:
    "I have identified two Baylor Scott & White physicians near your location in Dallas who specialize in preventive and obesity medicine. Both are accepting new patients within your network. Dr. Chen at Baylor University Medical Center is the closest — just 1.8 miles away — with availability as early as this afternoon.",
  providers: [
    {
      id: "dr-chen",
      name: "Dr. Emily Chen, MD",
      specialty: "Obesity & Metabolic Medicine",
      facility: "Baylor University Medical Center",
      distanceMiles: 1.8,
      rating: 4.9,
      reviewCount: 234,
      nextAvailableSlot: "Today, 3:30 PM",
      imageUrl:
        "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
    },
    {
      id: "dr-patel",
      name: "Dr. Raj Patel, MD",
      specialty: "Internal & Preventive Medicine",
      facility: "Baylor Scott & White Medical Center",
      distanceMiles: 2.4,
      rating: 4.8,
      reviewCount: 187,
      nextAvailableSlot: "Tomorrow, 9:00 AM",
      imageUrl:
        "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=200&h=200&fit=crop&auto=format",
    },
  ],
  followUpActions: [
    {
      label: "Book with Dr. Chen",
      actionType: "BOOK_PROVIDER",
      providerId: "dr-chen",
    },
    {
      label: "Book with Dr. Patel",
      actionType: "BOOK_PROVIDER",
      providerId: "dr-patel",
    },
    { label: "Get health tips first", actionType: "PIVOT_TIPS" },
  ],
};

function providerToPhysician(provider: Provider): Physician {
  return {
    id: provider.id,
    name: provider.name,
    specialty: provider.specialty,
    distance: `${provider.distanceMiles} miles`,
    rating: provider.rating,
    reviewCount: provider.reviewCount,
    nextAvailable: provider.nextAvailableSlot,
    imageUrl: provider.imageUrl,
  };
}

export function FindDoctorResponse({
  data = DEFAULT_DATA,
  onBookProvider,
  onChipSelect,
  timestamp = "3:23 PM",
  className,
}: FindDoctorResponseProps) {
  useLogRenders("FindDoctorResponse", { providerCount: data.providers.length });
  usePerformanceTracking();

  const handleBook = (physician: Physician) => {
    onBookProvider?.(physician.id);
  };

  return (
    <div className={`flex flex-col gap-4 w-full ${className ?? ""}`}>
      {/* Summary text bubble */}
      <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
        <p className="text-sm text-foreground leading-relaxed">
          {data.summaryText}
        </p>
      </div>

      {/* Provider list */}
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
          Nearby Baylor Physicians
        </p>
        <ul className="space-y-3" role="list" aria-label="Nearby physicians">
          {data.providers.map((provider) => (
            <li key={provider.id} role="listitem">
              <PhysicianCard
                physician={providerToPhysician(provider)}
                onBook={handleBook}
              />
            </li>
          ))}
        </ul>
      </div>

      {/* Follow-up action chips */}
      <div className="flex flex-wrap gap-1.5 mt-1">
        {data.followUpActions.map((action) => (
          <Button
            key={action.label}
            variant="secondary"
            size="sm"
            className="rounded-full bg-card border border-border text-xs px-3 py-1.5 text-foreground hover:bg-secondary hover:border-primary/30 hover:text-primary transition-colors"
            onClick={() => onChipSelect?.(action.label)}
            aria-label={action.label}
          >
            {action.label}
          </Button>
        ))}
      </div>

      {/* Timestamp */}
      <time className="text-[10px] text-muted-foreground font-mono px-1">
        {timestamp}
      </time>
    </div>
  );
}
