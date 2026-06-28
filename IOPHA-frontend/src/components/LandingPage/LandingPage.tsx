import React from "react";
import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import Logger from "../../utils/logger";
import { AppErrorBoundary } from "../AppErrorBoundary";
import { RiskProfileSidebar } from "../RiskProfileSidebar/RiskProfileSidebar";
import { ChatArea } from "../ChatArea/ChatArea";

interface LandingPageProps {
  userName?: string;
  userAge?: number;
  userLocation?: string;
  riskScore?: number;
  contributingFactors?: string[];
  bmi?: number;
  hospitalName?: string;
  lastAssessed?: string;
  onTopicSelect?: (topic: string) => void;
}

const DEFAULT_PROPS = {
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

export function LandingPage({
  userName = DEFAULT_PROPS.userName,
  userAge = DEFAULT_PROPS.userAge,
  userLocation = DEFAULT_PROPS.userLocation,
  riskScore = DEFAULT_PROPS.riskScore,
  contributingFactors = DEFAULT_PROPS.contributingFactors,
  bmi = DEFAULT_PROPS.bmi,
  hospitalName = DEFAULT_PROPS.hospitalName,
  lastAssessed = DEFAULT_PROPS.lastAssessed,
  onTopicSelect,
}: LandingPageProps) {
  useLogRenders("LandingPage", { userName, riskScore });
  usePerformanceTracking();

  Logger.debug("[LandingPage] Rendered", {
    userName,
    riskScore,
    hospitalName,
  });

  const handleTopicSelect = (topic: string) => {
    Logger.info("[LandingPage] Topic selected via chip", { topic });
    onTopicSelect?.(topic);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-background">
      {/* Top Header Bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-card border-b border-border">
        <div className="flex items-center gap-3">
          <div className="size-8 rounded-lg bg-primary flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="size-4 text-primary-foreground"
            >
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            </svg>
          </div>
          <div>
            <h1 className="font-semibold text-foreground">Health Assistant</h1>
            <p className="text-xs text-muted-foreground">{hospitalName}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-green-500" />
          <span className="text-sm text-muted-foreground">Online</span>
        </div>
      </header>

      <div className="flex flex-1 w-full">
        <AppErrorBoundary boundaryName="LandingPage">
          <AppErrorBoundary boundaryName="RiskProfileSidebar">
            <RiskProfileSidebar
              userName={userName}
              userAge={userAge}
              userLocation={userLocation}
              riskScore={riskScore}
              contributingFactors={contributingFactors}
              bmi={bmi}
              hospitalName={hospitalName}
              lastAssessed={lastAssessed}
            />
          </AppErrorBoundary>
          <AppErrorBoundary boundaryName="ChatArea">
            <ChatArea
              userName={userName}
              hospitalName={hospitalName}
              riskScore={riskScore}
              onTopicSelect={handleTopicSelect}
            />
          </AppErrorBoundary>
        </AppErrorBoundary>
      </div>
    </div>
  );
}
