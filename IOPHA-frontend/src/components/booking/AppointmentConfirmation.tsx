import { format } from "date-fns";
import { Button } from "../shared/button";

export interface AppointmentConfirmationProps {
  physicianName: string;
  facility: string;
  date: Date;
  time: string;
  onChipSelect?: (chip: string) => void;
  timestamp?: string;
  className?: string;
}

export function AppointmentConfirmation({
  physicianName,
  facility,
  date,
  time,
  onChipSelect,
  timestamp = "3:39 PM",
  className,
}: AppointmentConfirmationProps) {
  const formattedDate = format(date, "EEEE, MMMM d");
  const formattedTime = time.replace(/^0/, "");

  const confirmationText = `Your appointment has been confirmed. You are all set to see ${physicianName} at ${facility}. Please arrive 10 minutes early to complete intake paperwork. In the meantime, I recommend starting with the dietary adjustments we discussed — even small changes before your visit will help your physician tailor recommendations more precisely.`;

  return (
    <div className={`flex flex-col gap-3 w-full ${className ?? ""}`}>
      {/* Confirmation text bubble */}
      <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-5 py-4">
        <p className="text-sm text-foreground leading-relaxed">
          {confirmationText}
        </p>
      </div>

      {/* Confirmation card */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-start gap-3">
        <div className="shrink-0 mt-0.5">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-5 h-5 text-green-600"
            aria-hidden="true"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-green-800">
            Appointment confirmed
          </p>
          <p className="text-xs text-green-700 mt-0.5">
            {physicianName} · {formattedDate} · {formattedTime}
          </p>
        </div>
      </div>

      {/* Follow-up action chips */}
      <div className="flex flex-wrap gap-1.5 mt-1">
        {[
          "Weight & nutrition tips",
          "Exercise guidance",
          "Sleep & recovery",
        ].map((chip) => (
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
