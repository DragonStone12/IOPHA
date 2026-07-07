import { useState, useEffect, useCallback } from "react";
import { DayPicker } from "react-day-picker";
import { format } from "date-fns";
import { cn } from "../shared/utils";
import type { Physician } from "../NutritionResponse/PhysicianCard";

export interface TimeSlot {
  id: string;
  time: string;
  label: string;
  available: boolean;
}

export interface TimeSelectorProps {
  physician: Physician;
  selectedDate?: Date;
  selectedTime?: string;
  onDateSelect?: (date: Date) => void;
  onTimeSelect?: (time: string) => void;
  onContinue?: () => void;
  onBack?: () => void;
  onBackToSearch?: () => void;
  className?: string;
}

const generateMockSlots = (date: Date): TimeSlot[] => {
  const slots: TimeSlot[] = [];
  const baseHour = 9;
  for (let i = 0; i < 8; i++) {
    const hour = baseHour + i;
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour > 12 ? hour - 12 : hour;
    const timeStr = `${displayHour.toString().padStart(2, "0")}:00 ${ampm}`;
    slots.push({
      id: `${format(date, "yyyy-MM-dd")}-${timeStr}`,
      time: timeStr,
      label: timeStr,
      available: (i + 1) % 3 !== 0,
    });
    if (i < 7) {
      const halfHour = `${displayHour.toString().padStart(2, "0")}:30 ${ampm}`;
      slots.push({
        id: `${format(date, "yyyy-MM-dd")}-${halfHour}`,
        time: halfHour,
        label: halfHour,
        available: (i + 2) % 3 !== 0,
      });
    }
  }
  return slots;
};

export function TimeSelector({
  physician,
  selectedDate,
  selectedTime,
  onDateSelect,
  onTimeSelect,
  onContinue,
  onBack,
  onBackToSearch,
  className,
}: TimeSelectorProps) {
  const [currentMonth, setCurrentMonth] = useState<Date>(
    selectedDate || new Date(),
  );
  const [internalSelectedDate, setInternalSelectedDate] = useState<
    Date | undefined
  >(selectedDate);
  const [internalSelectedTime, setInternalSelectedTime] = useState<
    string | undefined
  >(selectedTime);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);

  useEffect(() => {
    if (internalSelectedDate) {
      const slots = generateMockSlots(internalSelectedDate);
      setAvailableSlots(slots.filter((s) => s.available));
    } else {
      setAvailableSlots([]);
    }
  }, [internalSelectedDate]);

  const handleDateSelect = useCallback(
    (date: Date | undefined) => {
      if (date) {
        setInternalSelectedDate(date);
        setInternalSelectedTime(undefined);
        onDateSelect?.(date);
      }
    },
    [onDateSelect],
  );

  const handleTimeSelect = useCallback(
    (time: string) => {
      setInternalSelectedTime(time);
      onTimeSelect?.(time);
    },
    [onTimeSelect],
  );

  const handleContinue = () => {
    if (internalSelectedDate && internalSelectedTime) {
      onContinue?.();
    }
  };

  const isContinueEnabled = !!internalSelectedDate && !!internalSelectedTime;

  return (
    <div
      className={cn(
        "flex flex-col min-h-screen w-full bg-[#F5F3EF]",
        className,
      )}
    >
      {/* Main Content */}
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Back to Health Assistant */}
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
            aria-label="Back to Health Assistant"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-4 h-4"
            >
              <path d="m15 18-6-6 6-6" />
            </svg>
            Back to Health Assistant
          </button>

          {/* Back to search */}
          <button
            onClick={onBackToSearch}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
            aria-label="Back to search"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-4 h-4"
            >
              <path d="m15 18-6-6 6-6" />
            </svg>
            Back to search
          </button>

          {/* Title */}
          <h1 className="text-2xl font-semibold text-foreground mb-1">
            Select Appointment Time
          </h1>
          <p className="text-base text-muted-foreground mb-8">
            Booking with {physician.name}
          </p>

          {/* Calendar and Time Slots */}
          <div className="flex gap-6">
            {/* Calendar Card */}
            <div className="bg-card rounded-xl p-6 border border-border w-80">
              <h2 className="text-lg font-semibold text-foreground mb-6 text-center">
                Choose a Date
              </h2>
              <div className="flex justify-center">
                <DayPicker
                  mode="single"
                  selected={internalSelectedDate}
                  onSelect={handleDateSelect}
                  month={currentMonth}
                  onMonthChange={setCurrentMonth}
                  disabled={{ before: new Date() }}
                  showOutsideDays={false}
                  classNames={{
                    months: "flex flex-col items-center",
                    month: "space-y-4 w-full",
                    caption_label: "text-base font-semibold text-foreground",
                    nav: "flex items-center gap-2",
                    day: "h-9 w-9 p-0 group",
                    day_button:
                      "h-9 w-9 rounded-full font-normal cursor-pointer transition-colors " +
                      "outline-none focus-visible:ring-2 focus-visible:ring-blue-400 " +
                      "group-aria-selected:border-2 group-aria-selected:border-blue-600 " +
                      "group-aria-selected:bg-blue-50 group-aria-selected:font-semibold",
                    today: "font-semibold",
                    outside: "text-muted-foreground opacity-30",
                    disabled:
                      "text-muted-foreground opacity-30 cursor-not-allowed",
                    hidden: "invisible",
                  }}
                  components={{
                    Chevron: ({ orientation }) => (
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="h-4 w-4"
                      >
                        {orientation === "left" ? (
                          <path d="m15 18-6-6 6-6" />
                        ) : (
                          <path d="m9 18 6-6-6-6" />
                        )}
                      </svg>
                    ),
                  }}
                />
              </div>
            </div>

            {/* Time Slots Card */}
            <div className="bg-card rounded-xl p-6 border border-border w-80">
              <h2 className="text-lg font-semibold text-foreground mb-6">
                Choose a Time
              </h2>
              {internalSelectedDate ? (
                availableSlots.length > 0 ? (
                  <div className="flex flex-wrap gap-3">
                    {availableSlots.map((slot) => (
                      <button
                        key={slot.id}
                        onClick={() => handleTimeSelect(slot.time)}
                        className={cn(
                          "px-4 py-2 rounded-lg border text-sm font-medium transition-all",
                          internalSelectedTime === slot.time
                            ? "bg-blue-600 text-white border-blue-600"
                            : "bg-white text-foreground border-gray-200 hover:border-blue-300",
                        )}
                        aria-label={`Select ${slot.label}`}
                        aria-pressed={internalSelectedTime === slot.time}
                      >
                        {slot.label}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No appointments available for this date. Please select
                    another day.
                  </p>
                )
              ) : (
                <p className="text-sm text-muted-foreground">
                  Please select a date to see available times.
                </p>
              )}
            </div>
          </div>

          {/* Summary Bar */}
          {isContinueEnabled && (
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  Selected appointment:
                </p>
                <p className="text-base font-semibold text-foreground">
                  {internalSelectedDate && internalSelectedTime
                    ? `${format(internalSelectedDate, "EEEE, MMMM d, yyyy")} at ${internalSelectedTime}`
                    : ""}
                </p>
              </div>
              <button
                onClick={handleContinue}
                className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Continue to Confirmation
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
