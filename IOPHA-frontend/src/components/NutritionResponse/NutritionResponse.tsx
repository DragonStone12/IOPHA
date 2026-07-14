import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import { TipCard, type Tip } from "./TipCard";
import { PhysicianCard, type Physician } from "./PhysicianCard";
import { Button } from "../shared/button";
import { MOCK_NUTRITION_RESPONSE } from "../../mocks/nutritionData.mock";

export interface NutritionResponseData {
  introText: string;
  tips: Tip[];
  physician?: Physician;
  followUpChips: string[];
}

interface NutritionResponseProps {
  data?: NutritionResponseData;
  onChipSelect?: (chip: string) => void;
  onBookPhysician?: (physician: Physician) => void;
  timestamp?: string;
  className?: string;
}

export function NutritionResponse({
  data = MOCK_NUTRITION_RESPONSE,
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
      <div
        className="space-y-2"
        role="list"
        aria-label="Dietary adjustment tips"
      >
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
          <PhysicianCard physician={data.physician} onBook={onBookPhysician} />
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
