import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import { TipCard, type Tip } from "../NutritionResponse/TipCard";
import { Button } from "../shared/button";

export interface ExerciseTip extends Tip {}

export interface FollowUpAction {
  label: string;
  actionType: "NAVIGATE_TOPIC";
  topicId: string;
}

export interface ExerciseGuidanceData {
  introText: string;
  tips: ExerciseTip[];
  followUpActions: FollowUpAction[];
}

interface ExerciseGuidanceResponseProps {
  data: ExerciseGuidanceData;
  onChipSelect?: (chip: string) => void;
  timestamp?: string;
  className?: string;
}

const DEFAULT_DATA: ExerciseGuidanceData = {
  introText:
    "For your risk profile, structured movement delivers the highest return of any single intervention. The ACSM protocol for high-risk individuals at your BMI focuses on consistency over intensity — especially in the first 8 weeks.",
  tips: [
    {
      number: 1,
      title: "Start with daily walking",
      description:
        "20 minutes of brisk walking (3 mph) five days per week. This alone significantly reduces insulin resistance within 2 weeks and burns 150–200 calories per session.",
    },
    {
      number: 2,
      title: "Resistance training twice weekly",
      description:
        "Bodyweight squats, push-ups, and rows preserve lean muscle mass, which directly improves your resting metabolic rate and is protective against weight regain.",
    },
    {
      number: 3,
      title: "Maximize NEAT (non-exercise activity)",
      description:
        "Taking stairs, standing desks, and walking during calls can add 300–500 extra calories burned daily with zero scheduled workout time — a major advantage for busy schedules.",
    },
  ],
  followUpActions: [
    {
      label: "Nutrition tips",
      actionType: "NAVIGATE_TOPIC",
      topicId: "nutrition_tips",
    },
    {
      label: "Find a doctor",
      actionType: "NAVIGATE_TOPIC",
      topicId: "find_a_doctor",
    },
    {
      label: "Sleep advice",
      actionType: "NAVIGATE_TOPIC",
      topicId: "sleep_recovery",
    },
  ],
};

export function ExerciseGuidanceResponse({
  data = DEFAULT_DATA,
  onChipSelect,
  timestamp = "3:28 PM",
  className,
}: ExerciseGuidanceResponseProps) {
  useLogRenders("ExerciseGuidanceResponse", { tipCount: data.tips.length });
  usePerformanceTracking();

  return (
    <div className={`flex flex-col gap-4 w-full ${className ?? ""}`}>
      {/* Intro text bubble */}
      <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
        <p className="text-sm text-foreground leading-relaxed">
          {data.introText}
        </p>
      </div>

      {/* Numbered exercise tip cards */}
      <ol
        className="space-y-2"
        role="list"
        aria-label="Exercise recommendations"
      >
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
