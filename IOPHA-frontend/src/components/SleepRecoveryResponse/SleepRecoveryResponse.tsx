import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import { TipCard, type Tip } from "../NutritionResponse/TipCard";
import { Button } from "../shared/button";

export interface SleepTip extends Tip {}

export interface FollowUpAction {
  label: string;
  actionType: "NAVIGATE_TOPIC" | "BOOK_DOCTOR";
  topicId?: string;
}

export interface SleepRecoveryData {
  introText: string;
  tips: SleepTip[];
  followUpActions: FollowUpAction[];
}

interface SleepRecoveryResponseProps {
  data: SleepRecoveryData;
  onChipSelect?: (chip: string) => void;
  timestamp?: string;
  className?: string;
}

const DEFAULT_DATA: SleepRecoveryData = {
  introText:
    "Sleep quality is directly correlated with metabolic health and weight regulation. Research shows sleeping under 6 hours increases ghrelin (the hunger hormone) by 28% and decreases leptin (satiety hormone) by 18% — both of which amplify the risk factors in your profile.",
  tips: [
    {
      number: 1,
      title: "Target 7–9 hours with a fixed schedule",
      description:
        "Set a consistent bedtime and wake time, including weekends. Consistency regulates cortisol, which directly controls where your body stores fat.",
    },
    {
      number: 2,
      title: "Screens off 60 minutes before bed",
      description:
        "Blue light suppresses melatonin production by up to 50%. Switch to reading or dimmed warm lighting in the final hour to accelerate sleep onset.",
    },
    {
      number: 3,
      title: "Cool your bedroom to 65–68°F",
      description:
        "Core body temperature drop is the primary trigger for sleep onset and deeper sleep stages. This single environmental change improves sleep quality for most people within days.",
    },
  ],
  followUpActions: [
    {
      label: "Nutrition advice",
      actionType: "NAVIGATE_TOPIC",
      topicId: "nutrition_tips",
    },
    {
      label: "Exercise tips",
      actionType: "NAVIGATE_TOPIC",
      topicId: "exercise_guidance",
    },
    { label: "Book a doctor", actionType: "BOOK_DOCTOR" },
  ],
};

export function SleepRecoveryResponse({
  data = DEFAULT_DATA,
  onChipSelect,
  timestamp = "3:32 PM",
  className,
}: SleepRecoveryResponseProps) {
  useLogRenders("SleepRecoveryResponse", { tipCount: data.tips.length });
  usePerformanceTracking();

  return (
    <div className={`flex flex-col gap-4 w-full ${className ?? ""}`}>
      {/* Intro text bubble */}
      <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
        <p className="text-sm text-foreground leading-relaxed">
          {data.introText}
        </p>
      </div>

      {/* Numbered sleep tip cards */}
      <ol className="space-y-2" role="list" aria-label="Sleep recommendations">
        {data.tips.map((tip) => (
          <li key={tip.id ?? tip.number}>
            <TipCard tip={tip} />
          </li>
        ))}
      </ol>

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
