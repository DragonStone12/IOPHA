import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import { TipCard, type Tip } from "./TipCard";
import { PhysicianCard, type Physician } from "./PhysicianCard";
import { Button } from "../shared/button";

export interface NutritionResponseData {
  introText: string;
  tips: Tip[];
  physician?: Physician;
  followUpChips: string[];
}

interface NutritionResponseProps {
  data: NutritionResponseData;
  onChipSelect?: (chip: string) => void;
  onBookPhysician?: (physician: Physician) => void;
  timestamp?: string;
  className?: string;
}

const DEFAULT_DATA: NutritionResponseData = {
  introText:
    "Based on your profile and current clinical guidelines, here are three evidence-based dietary adjustments most effective for your risk factors. Because your assessment noted irregular meal timing, aligning your eating window with your waking hours is particularly impactful.",
  tips: [
    {
      number: 1,
      title: "Time-restricted eating — 10-hour window",
      description:
        "Limit food intake to a consistent window such as 8 AM–6 PM. This alone reduces average daily caloric intake by 15–20% without strict counting and improves insulin sensitivity within 2 weeks.",
    },
    {
      number: 2,
      title: "Protein-first meals",
      description:
        "Begin each meal with 25–30g of lean protein (eggs, chicken, legumes). This slows gastric emptying, regulates appetite hormones, and reduces overall meal calories without hunger.",
    },
    {
      number: 3,
      title: "Eliminate liquid calories",
      description:
        "Replacing sweetened beverages with water, black coffee, or unsweetened tea removes an average of 350 excess calories per day — one of the highest-return single changes for your profile.",
    },
  ],
  physician: {
    id: "dr-chen",
    name: "Dr. Emily Chen, MD",
    specialty: "Obesity & Metabolic Medicine",
    distance: "1.8 miles",
    rating: 4.9,
    reviewCount: 234,
    nextAvailable: "Today, 3:30 PM",
    imageUrl:
      "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
  },
  followUpChips: [
    "Exercise tips",
    "Book Dr. Chen",
    "Sleep advice",
    "More nutrition guidance",
  ],
};

export function NutritionResponse({
  data = DEFAULT_DATA,
  onChipSelect,
  onBookPhysician,
  timestamp = "3:14 PM",
  className,
}: NutritionResponseProps) {
  useLogRenders("NutritionResponse", { tipCount: data.tips.length });
  usePerformanceTracking();

  return (
    <div className={`flex flex-col gap-4 w-full ${className ?? ""}`}>
      {/* Intro text bubble */}
      <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
        <p className="text-sm text-foreground leading-relaxed">
          {data.introText}
        </p>
      </div>

      {/* Numbered tip cards */}
      <div className="space-y-2" role="list" aria-label="Dietary adjustment tips">
        {data.tips.map((tip) => (
          <TipCard key={tip.id ?? tip.number} tip={tip} />
        ))}
      </div>

      {/* Physician recommendation */}
      {data.physician && (
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
            Nearby Baylor Physicians
          </p>
          <PhysicianCard
            physician={data.physician}
            onBook={onBookPhysician}
          />
        </div>
      )}

      {/* Follow-up action chips */}
      <div className="flex flex-wrap gap-1.5 mt-1">
        {data.followUpChips.map((chip) => (
          <Button
            key={chip}
            variant="secondary"
            size="sm"
            className="rounded-full bg-card border border-border text-xs px-3 py-1.5 text-foreground hover:bg-secondary hover:border-primary/30 hover:text-primary transition-colors"
            onClick={() => onChipSelect?.(chip)}
            aria-label={`Ask about ${chip}`}
          >
            {chip}
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
