import { useEffect } from "react";
import { format } from "date-fns";
import { cn } from "../shared/utils";
import type { Physician } from "../NutritionResponse/PhysicianCard";

export interface SuccessModalProps {
  physician: Physician;
  selectedDate: Date;
  selectedTime: string;
  patientName: string;
  patientEmail: string;
  patientPhone: string;
  bookingId?: string;
  onClose?: () => void;
  onChangeDateTime?: () => void;
  className?: string;
}

export function SuccessModal({
  physician,
  selectedDate,
  selectedTime,
  patientName,
  patientEmail,
  patientPhone,
  bookingId,
  onClose,
  onChangeDateTime,
  className,
}: SuccessModalProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose?.();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const formattedDateTime = `${format(
    selectedDate,
    "EEEE, MMMM d, yyyy",
  )} at ${selectedTime}`;

  return (
    <div
      className={cn(
        "flex flex-col min-h-screen w-full bg-[#F5F3EF]",
        className,
      )}
      role="dialog"
      aria-label="Appointment confirmed"
    >
      {/* Change date or time link */}
      <div className="px-8 pt-6">
        <button
          onClick={onChangeDateTime}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Change date or time"
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
            aria-hidden="true"
          >
            <path d="m15 18-6-6 6-6" />
          </svg>
          Change date or time
        </button>
      </div>

      {/* Centered confirmation card */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="bg-card rounded-2xl p-8 max-w-md w-full shadow-sm border border-border">
          {/* Success Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-8 h-8 text-green-600"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-xl font-semibold text-foreground text-center mb-2">
            Appointment Confirmed!
          </h2>
          <p className="text-sm text-muted-foreground text-center mb-6">
            You will receive a confirmation email shortly with all the details.
          </p>

          {/* Appointment Summary */}
          <div className="bg-secondary/50 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">
              Appointment Summary
            </h3>
            <div className="space-y-3">
              {/* Doctor */}
              <div className="flex items-start gap-3">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0"
                  aria-hidden="true"
                >
                  <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                <div>
                  <p className="text-xs text-muted-foreground">Doctor</p>
                  <p className="text-sm font-medium text-foreground">
                    {physician.name}
                  </p>
                  {physician.specialty && (
                    <p className="text-xs text-muted-foreground">
                      {physician.specialty}
                    </p>
                  )}
                </div>
              </div>

              {/* Date & Time */}
              <div className="flex items-start gap-3">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0"
                  aria-hidden="true"
                >
                  <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
                  <line x1="16" x2="16" y1="2" y2="6" />
                  <line x1="8" x2="8" y1="2" y2="6" />
                  <line x1="3" x2="21" y1="10" y2="10" />
                </svg>
                <div>
                  <p className="text-xs text-muted-foreground">
                    Date &amp; Time
                  </p>
                  <p className="text-sm font-medium text-foreground">
                    {formattedDateTime}
                  </p>
                </div>
              </div>

              {/* Location */}
              {physician.facility && (
                <div className="flex items-start gap-3">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0"
                    aria-hidden="true"
                  >
                    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <div>
                    <p className="text-xs text-muted-foreground">Location</p>
                    <p className="text-sm font-medium text-foreground">
                      {physician.facility}
                    </p>
                  </div>
                </div>
              )}

              {/* Patient info */}
              <div className="pt-2 mt-2 border-t border-border">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-muted-foreground">Patient: </span>
                    <span className="text-foreground">{patientName}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Email: </span>
                    <span className="text-foreground">{patientEmail}</span>
                  </div>
                </div>
                <div className="text-xs mt-1">
                  <span className="text-muted-foreground">Phone: </span>
                  <span className="text-foreground">{patientPhone}</span>
                </div>
                {bookingId && (
                  <div className="text-xs mt-1">
                    <span className="text-muted-foreground">Booking ID: </span>
                    <span className="font-mono text-foreground">
                      {bookingId}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
