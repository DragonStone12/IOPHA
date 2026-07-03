import { useState, useCallback } from "react";
import { z } from "zod";
import { format } from "date-fns";
import { cn } from "../shared/utils";
import { Input } from "../shared/input";
import type { Physician } from "../NutritionResponse/PhysicianCard";

const REQUIRED_FIELD_ERROR = "This field is required";

const validationSchema = z.object({
  name: z.string().min(1, REQUIRED_FIELD_ERROR),
  email: z
    .string()
    .min(1, REQUIRED_FIELD_ERROR)
    .email("Please enter a valid email address"),
  phone: z
    .string()
    .min(1, REQUIRED_FIELD_ERROR)
    .regex(/^\d{10}$/, "Please enter a valid 10-digit phone number"),
  reason: z.string().optional(),
});

type FormData = z.infer<typeof validationSchema>;
type FormErrors = Partial<Record<keyof FormData, string>>;

export interface ConfirmationFormProps {
  physician: Physician;
  selectedDate: Date;
  selectedTime: string;
  patientName?: string;
  patientEmail?: string;
  patientPhone?: string;
  onConfirm?: (data: FormData) => void;
  onChangeDateTime?: () => void;
  onBack?: () => void;
  className?: string;
}

export function ConfirmationForm({
  physician,
  selectedDate,
  selectedTime,
  patientName,
  patientEmail,
  patientPhone,
  onConfirm,
  onChangeDateTime,
  onBack,
  className,
}: ConfirmationFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: patientName || "",
    email: patientEmail || "",
    phone: patientPhone || "",
    reason: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<keyof FormData, boolean>>({
    name: false,
    email: false,
    phone: false,
    reason: false,
  });

  const validate = useCallback((data: FormData): FormErrors => {
    try {
      validationSchema.parse(data);
      return {};
    } catch (err) {
      if (err instanceof z.ZodError) {
        const fieldErrors: FormErrors = {};
        for (const issue of err.issues) {
          if (issue.path.length > 0) {
            const field = issue.path[0] as keyof FormData;
            if (!fieldErrors[field]) {
              fieldErrors[field] = issue.message;
            }
          }
        }
        return fieldErrors;
      }
      return {};
    }
  }, []);

  const handleChange = (field: keyof FormData, value: string) => {
    const sanitizedValue = field === "phone" ? value.replace(/\D/g, "") : value;
    const newData = { ...formData, [field]: sanitizedValue };
    setFormData(newData);

    if (touched[field]) {
      const newErrors = validate(newData);
      setErrors((prev) => ({
        ...prev,
        [field]: newErrors[field],
      }));
    }
  };

  const handleBlur = (field: keyof FormData) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    const newErrors = validate(formData);
    setErrors((prev) => ({
      ...prev,
      [field]: newErrors[field],
    }));
  };

  const handleSubmit = () => {
    const newErrors = validate(formData);
    setErrors(newErrors);
    setTouched({ name: true, email: true, phone: true, reason: true });

    if (Object.keys(newErrors).length === 0) {
      onConfirm?.(formData);
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col min-h-screen w-full bg-[#F5F3EF]",
        className,
      )}
    >
      {/* Main Content */}
      <div className="flex-1 p-8">
        <div className="max-w-3xl mx-auto">
          {/* Change date or time */}
          <button
            onClick={onChangeDateTime}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors"
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
            >
              <path d="m15 18-6-6 6-6" />
            </svg>
            Change date or time
          </button>

          {/* Back to calendar */}
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors"
            aria-label="Back to calendar"
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
            Back to calendar
          </button>

          {/* Title */}
          <h1 className="text-2xl font-semibold text-foreground mb-1">
            Confirm Your Appointment
          </h1>
          <p className="text-base text-muted-foreground mb-8">
            Please review your appointment details and provide your information
          </p>

          <div className="flex gap-6">
            {/* Patient Information Card */}
            <div className="flex-1 bg-card rounded-xl p-6 border border-border">
              <h2 className="text-lg font-semibold text-foreground mb-6">
                Patient Information
              </h2>

              <form
                autoComplete="off"
                className="space-y-4"
                onSubmit={(e) => e.preventDefault()}
              >
                <input
                  type="text"
                  name="fake_user_name"
                  autoComplete="username"
                  className="hidden"
                  tabIndex={-1}
                  aria-hidden="true"
                />
                <input
                  type="password"
                  name="fake_password"
                  autoComplete="new-password"
                  className="hidden"
                  tabIndex={-1}
                  aria-hidden="true"
                />
                {/* Name Field */}
                <div>
                  <label
                    htmlFor="patient-name"
                    className="block text-sm font-medium text-foreground mb-1.5"
                  >
                    Full Name <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="patient-name"
                    type="text"
                    name="patient_name"
                    value={formData.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleChange("name", e.target.value)
                    }
                    onBlur={() => handleBlur("name")}
                    placeholder="Enter your full name"
                    autoComplete="new-password"
                    aria-invalid={!!errors.name}
                    aria-describedby={errors.name ? "name-error" : undefined}
                    className={cn(
                      "border-blue-600 focus:border-blue-600 focus-visible:border-blue-600 focus:ring-blue-600/50 focus-visible:ring-blue-600/50 focus:!outline-none",
                      errors.name &&
                        "border-destructive focus:border-destructive focus-visible:border-destructive focus:ring-destructive/20 focus-visible:ring-destructive/20",
                    )}
                  />
                  {errors.name && (
                    <p
                      id="name-error"
                      className="text-xs text-destructive mt-1"
                      role="alert"
                    >
                      {errors.name}
                    </p>
                  )}
                </div>

                {/* Email Field */}
                <div>
                  <label
                    htmlFor="patient-email"
                    className="block text-sm font-medium text-foreground mb-1.5"
                  >
                    Email Address <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="patient-email"
                    type="email"
                    name="patient_email"
                    value={formData.email}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleChange("email", e.target.value)
                    }
                    onBlur={() => handleBlur("email")}
                    placeholder="Enter your email address"
                    autoComplete="new-password"
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    className={cn(
                      "border-blue-600 focus:border-blue-600 focus-visible:border-blue-600 focus:ring-blue-600/50 focus-visible:ring-blue-600/50 focus:!outline-none",
                      errors.email &&
                        "border-destructive focus:border-destructive focus-visible:border-destructive focus:ring-destructive/20 focus-visible:ring-destructive/20",
                    )}
                  />
                  {errors.email && (
                    <p
                      id="email-error"
                      className="text-xs text-destructive mt-1"
                      role="alert"
                    >
                      {errors.email}
                    </p>
                  )}
                </div>

                {/* Phone Field */}
                <div>
                  <label
                    htmlFor="patient-phone"
                    className="block text-sm font-medium text-foreground mb-1.5"
                  >
                    Phone Number <span className="text-destructive">*</span>
                  </label>
                  <Input
                    id="patient-phone"
                    type="tel"
                    name="patient_phone"
                    value={formData.phone}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleChange("phone", e.target.value)
                    }
                    onBlur={() => handleBlur("phone")}
                    placeholder="Enter 10-digit phone number"
                    autoComplete="new-password"
                    aria-invalid={!!errors.phone}
                    aria-describedby={errors.phone ? "phone-error" : undefined}
                    className={cn(
                      "border-blue-600 focus:border-blue-600 focus-visible:border-blue-600 focus:ring-blue-600/50 focus-visible:ring-blue-600/50 focus:!outline-none",
                      errors.phone &&
                        "border-destructive focus:border-destructive focus-visible:border-destructive focus:ring-destructive/20 focus-visible:ring-destructive/20",
                    )}
                  />
                  {errors.phone && (
                    <p
                      id="phone-error"
                      className="text-xs text-destructive mt-1"
                      role="alert"
                    >
                      {errors.phone}
                    </p>
                  )}
                </div>

                {/* Reason for Visit */}
                <div>
                  <label
                    htmlFor="patient-reason"
                    className="block text-sm font-medium text-foreground mb-1.5"
                  >
                    Reason for Visit (Optional)
                  </label>
                  <textarea
                    id="patient-reason"
                    name="patient_reason"
                    value={formData.reason}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                      handleChange("reason", e.target.value)
                    }
                    onBlur={() => handleBlur("reason")}
                    placeholder="Describe the reason for your visit"
                    rows={3}
                    autoComplete="off"
                    className="w-full rounded-lg border border-blue-600 bg-input-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:border-blue-500 focus-visible:ring-blue-500/50 focus-visible:ring-[3px] outline-none transition-colors resize-none"
                  />
                </div>

                {/* Confirm Button */}
                <button
                  onClick={handleSubmit}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors mt-2"
                >
                  Confirm Appointment
                </button>
              </form>
            </div>

            {/* Appointment Details Card */}
            <div className="w-80 shrink-0">
              <div className="bg-card rounded-xl p-6 border border-border sticky top-4">
                <h2 className="text-lg font-semibold text-foreground mb-6">
                  Appointment Details
                </h2>

                <div className="space-y-4">
                  {/* Provider */}
                  <div className="flex gap-3">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="w-5 h-5 text-blue-600 mt-0.5 shrink-0"
                    >
                      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Healthcare Provider
                      </p>
                      <p className="text-sm font-semibold text-foreground">
                        {physician.name}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {physician.specialty}
                      </p>
                    </div>
                  </div>

                  <hr className="border-border" />

                  {/* Date */}
                  <div className="flex gap-3">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="w-5 h-5 text-blue-600 mt-0.5 shrink-0"
                    >
                      <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
                      <line x1="16" x2="16" y1="2" y2="6" />
                      <line x1="8" x2="8" y1="2" y2="6" />
                      <line x1="3" x2="21" y1="10" y2="10" />
                    </svg>
                    <div>
                      <p className="text-xs text-muted-foreground">Date</p>
                      <p className="text-sm font-semibold text-foreground">
                        {format(selectedDate, "EEEE, MMMM d, yyyy")}
                      </p>
                    </div>
                  </div>

                  <hr className="border-border" />

                  {/* Time */}
                  <div className="flex gap-3">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="w-5 h-5 text-blue-600 mt-0.5 shrink-0"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    <div>
                      <p className="text-xs text-muted-foreground">Time</p>
                      <p className="text-sm font-semibold text-foreground">
                        {selectedTime}
                      </p>
                    </div>
                  </div>

                  <hr className="border-border" />

                  {/* Location */}
                  <div className="flex gap-3">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="w-5 h-5 text-blue-600 mt-0.5 shrink-0"
                    >
                      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                    <div>
                      <p className="text-xs text-muted-foreground">Location</p>
                      <p className="text-sm font-semibold text-foreground">
                        Baylor University Medical Center
                      </p>
                    </div>
                  </div>

                  {/* Note */}
                  <div className="bg-blue-50 rounded-lg p-4 mt-4">
                    <p className="text-sm text-foreground">
                      <span className="font-semibold">Note:</span> Please arrive
                      15 minutes early to complete any necessary paperwork.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
