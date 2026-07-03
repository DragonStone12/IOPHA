import { ExerciseGuidanceResponse } from "./ExerciseGuidanceResponse";
import type { ExerciseGuidanceData } from "./ExerciseGuidanceResponse";

const MOCK_DATA: ExerciseGuidanceData = {
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

describe("ExerciseGuidanceResponse Component", () => {
  it("should render introductory text mentioning ACSM protocol and BMI", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.contains("ACSM protocol").should("be.visible");
    cy.contains("BMI").should("be.visible");
  });

  it("should render exactly 3 numbered exercise recommendation cards", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.get("[aria-posinset]").should("have.length", 3);
  });

  it("should render the first card titled Start with daily walking", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.contains("Start with daily walking").should("be.visible");
  });

  it("should render the second card titled Resistance training twice weekly", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.contains("Resistance training twice weekly").should("be.visible");
  });

  it("should render the third card titled Maximize NEAT", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.contains("Maximize NEAT").should("be.visible");
  });

  it("should render follow-up chips including Nutrition tips and Find a doctor", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.contains("Nutrition tips").should("be.visible");
    cy.contains("Find a doctor").should("be.visible");
  });

  it("should fire onChipSelect callback when follow-up chip is clicked", () => {
    const callback = cy.stub().as("chipSelect");
    cy.mount(
      <ExerciseGuidanceResponse data={MOCK_DATA} onChipSelect={callback} />,
    );
    cy.contains("Nutrition tips").click();
    cy.get("@chipSelect").should("have.been.calledWith", "Nutrition tips");
  });

  it("should render with visual snapshot", () => {
    cy.mount(<ExerciseGuidanceResponse data={MOCK_DATA} />);
    cy.compareSnapshot("exercise-guidance-default");
  });
});
