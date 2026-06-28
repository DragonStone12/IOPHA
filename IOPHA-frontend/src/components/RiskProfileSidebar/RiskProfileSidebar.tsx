import React from "react";
import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import Logger from "../../utils/logger";
import { Avatar, AvatarFallback } from "../shared/avatar";
import { Progress } from "../shared/progress";
import { Button } from "../shared/button";

interface RiskProfileSidebarProps {
  userName?: string;
  userAge?: number;
  userLocation?: string;
  riskScore?: number;
  contributingFactors?: string[];
  bmi?: number;
  hospitalName?: string;
  lastAssessed?: string;
}

const DEFAULT_USER = {
  userName: "Sarah Mitchell",
  userAge: 34,
  userLocation: "Dallas, TX",
  riskScore: 78,
  contributingFactors: [
    "Sedentary lifestyle",
    "High-calorie diet",
    "Family history",
    "Irregular sleep",
  ],
  bmi: 31.2,
  hospitalName: "Baylor Scott & White Health",
  lastAssessed: "today",
};

export function RiskProfileSidebar({
  userName = DEFAULT_USER.userName,
  userAge = DEFAULT_USER.userAge,
  userLocation = DEFAULT_USER.userLocation,
  riskScore = DEFAULT_USER.riskScore,
  contributingFactors = DEFAULT_USER.contributingFactors,
  bmi = DEFAULT_USER.bmi,
  hospitalName = DEFAULT_USER.hospitalName,
  lastAssessed = DEFAULT_USER.lastAssessed,
}: RiskProfileSidebarProps) {
  useLogRenders("RiskProfileSidebar", { userName, riskScore });
  usePerformanceTracking();

  Logger.debug("[RiskProfileSidebar] Rendered", {
    userName,
    riskScore,
    bmi,
  });

  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const riskLevel =
    riskScore >= 70
      ? "HIGH RISK"
      : riskScore >= 40
        ? "MODERATE RISK"
        : "LOW RISK";
  const riskColor =
    riskScore >= 70
      ? "text-accent"
      : riskScore >= 40
        ? "text-amber-600"
        : "text-green-600";

  return (
    <aside className="w-80 shrink-0 bg-card border-r border-border flex flex-col">
      {/* Risk Profile Header */}
      <div className="px-6 py-6 border-b border-border">
        <div className="flex items-center gap-2 mb-1">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="size-5 text-primary"
          >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            RISK PROFILE
          </h2>
        </div>
        <p className="text-xs text-muted-foreground">{hospitalName}</p>
      </div>

      {/* User Card */}
      <div className="px-6 py-6 border-b border-border">
        <div className="flex items-center gap-3">
          <Avatar className="size-12">
            <AvatarFallback className="text-sm font-medium bg-secondary text-secondary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium text-foreground">{userName}</p>
            <p className="text-xs text-muted-foreground">
              {userAge} years · {userLocation}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Score */}
      <div className="px-6 py-6 border-b border-border">
        <div className="flex items-center gap-2 mb-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`size-4 ${riskColor}`}
          >
            <path d="M12 9v4" />
            <path d="M12 17h.01" />
            <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          </svg>
          <span className={`text-sm font-semibold ${riskColor}`}>
            {riskLevel}
          </span>
        </div>
        <div
          className="flex items-baseline gap-1 mb-2"
          aria-label={`Risk score ${riskScore} out of 100`}
        >
          <span className={`text-5xl font-normal ${riskColor}`}>
            {riskScore}
          </span>
          <span className="text-lg text-muted-foreground">/100</span>
        </div>
        <Progress
          value={riskScore}
          className="h-2"
          indicatorClassName={riskScore >= 70 ? "bg-accent" : undefined}
          aria-label={`Risk score progress bar: ${riskScore}%`}
        />
        <div className="flex justify-between mt-2 text-xs text-muted-foreground">
          <span>BMI {bmi}</span>
          <span>Last assessed {lastAssessed}</span>
        </div>
      </div>

      {/* Contributing Factors */}
      <div className="px-6 py-6 border-b border-border">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Contributing Factors
        </h3>
        <ul className="space-y-2">
          {contributingFactors.map((factor, index) => (
            <li key={index} className="flex items-start gap-2">
              <span className="size-2 rounded-full bg-accent mt-1.5 shrink-0" />
              <span className="text-sm text-foreground">{factor}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Quick Start Navigation */}
      <div className="px-6 py-6 flex-1">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Quick Start
        </h3>
        <nav className="space-y-1">
          {[
            "Weight & nutrition tips",
            "Find a doctor",
            "Exercise guidance",
            "Sleep & recovery",
          ].map((item) => (
            <Button
              key={item}
              variant="ghost"
              size="sm"
              className="w-full justify-between text-sm font-normal text-foreground hover:bg-primary/10 hover:text-primary transition-colors"
            >
              <span>{item}</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-4 text-muted-foreground"
              >
                <path d="m9 18 6-6-6-6" />
              </svg>
            </Button>
          ))}
        </nav>
      </div>
    </aside>
  );
}
