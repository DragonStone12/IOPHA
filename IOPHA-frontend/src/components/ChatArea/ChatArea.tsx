import React, { useState, useRef, useEffect } from "react";
import { useLogRenders } from "../../hooks/useLogRenders";
import { usePerformanceTracking } from "../../utils/performance";
import Logger from "../../utils/logger";
import { Button } from "../shared/button";
import { Input } from "../shared/input";

interface ChatAreaProps {
  userName?: string;
  hospitalName?: string;
  riskScore?: number;
  onTopicSelect?: (topic: string) => void;
}

const DEFAULT_USER = {
  userName: "Sarah Mitchell",
  hospitalName: "Baylor Health",
  riskScore: 78,
};

const TOPICS = [
  { label: "Weight & nutrition tips", value: "nutrition_tips" },
  { label: "Find a doctor", value: "find_a_doctor" },
  { label: "Exercise guidance", value: "exercise_guidance" },
  { label: "Sleep & recovery", value: "sleep_recovery" },
];

export function ChatArea({
  userName = DEFAULT_USER.userName,
  hospitalName = DEFAULT_USER.hospitalName,
  riskScore = DEFAULT_USER.riskScore,
  onTopicSelect,
}: ChatAreaProps) {
  useLogRenders("ChatArea", { userName, riskScore });
  usePerformanceTracking();

  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleTopicClick = (topic: string) => {
    Logger.info("[ChatArea] Topic selected", { topic });
    onTopicSelect?.(topic);
  };

  const handleSend = () => {
    if (!inputValue.trim()) return;
    Logger.info("[ChatArea] Message sent", { message: inputValue });
    setInputValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const greetingMessage = `Welcome, ${userName}. I'm your ${hospitalName} AI assistant. Based on your recently completed health survey, your obesity risk score is ${riskScore}/100 — placing you in the high-risk category. The encouraging news: this is exactly when early intervention is most effective. I can provide personalized, evidence-based guidance right now, and connect you with a ${hospitalName.split(" ")[0]} physician nearby if you'd like a professional consultation. How can I help you today?`;

  return (
    <main className="flex-1 flex flex-col min-w-0">
      {/* Chat Content */}
      <div className="flex-1 overflow-y-auto p-8 bg-[#F5F3EF]">
        <div className="max-w-4xl mx-auto">
          {/* AI Greeting - No avatar, centered bubble */}
          <div className="mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-200">
              <p className="text-gray-800 leading-relaxed text-[15px]">
                {greetingMessage}
              </p>
            </div>
          </div>

          {/* AI Avatar + Action Chips Row */}
          <div className="flex items-start gap-3 mb-8">
            <div className="flex flex-col items-center shrink-0">
              <div className="size-9 rounded-full bg-primary flex items-center justify-center">
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
                  <rect width="18" height="18" x="3" y="3" rx="2" />
                  <path d="M9 10h0" />
                  <path d="M15 10h0" />
                  <path d="M12 14v4" />
                </svg>
              </div>
              <span className="text-xs text-gray-500 mt-1.5">3:10 PM</span>
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              {TOPICS.map((topic) => (
                <Button
                  key={topic.value}
                  variant="secondary"
                  size="sm"
                  className="rounded-full bg-white border border-gray-200 text-sm px-4 py-2 text-gray-700 hover:bg-primary/10 hover:border-primary/30 transition-colors"
                  onClick={() => handleTopicClick(topic.value)}
                >
                  {topic.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="max-w-5xl mx-auto">
          <div className="flex gap-3">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about nutrition, exercise, finding a doctor..."
              className="flex-1 bg-[#F0EEEB] border-0 rounded-full text-gray-700 placeholder:text-gray-400 focus-visible:ring-0 h-12 px-5"
            />
            <Button
              onClick={handleSend}
              disabled={!inputValue.trim()}
              className="bg-[#B0C8CC] hover:bg-[#9AB0B5] text-white rounded-full size-12 p-0 shrink-0"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="size-5"
              >
                <path d="m22 2-7 20-4-9-9-4Z" />
                <path d="M22 2 11 13" />
              </svg>
            </Button>
          </div>
          <p className="text-xs text-gray-500 text-center mt-2">
            AI responses are for informational purposes only · Not a substitute
            for professional medical advice
          </p>
        </div>
      </div>
    </main>
  );
}
