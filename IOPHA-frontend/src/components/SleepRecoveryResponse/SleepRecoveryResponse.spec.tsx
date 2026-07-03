import { SleepRecoveryResponse } from "./SleepRecoveryResponse";
import type { SleepRecoveryData } from "./SleepRecoveryResponse";

const MOCK_DATA: SleepRecoveryData = {
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

describe("SleepRecoveryResponse Component", () => {
  it("should render introductory text mentioning ghrelin and leptin", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.contains("ghrelin").should("be.visible");
    cy.contains("leptin").should("be.visible");
  });

  it("should render exactly 3 numbered sleep recommendation cards", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.get("[aria-posinset]").should("have.length", 3);
  });

  it("should render the first card titled Target 7–9 hours with a fixed schedule", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.contains("Target 7–9 hours with a fixed schedule").should("be.visible");
  });

  it("should render the second card titled Screens off 60 minutes before bed", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.contains("Screens off 60 minutes before bed").should("be.visible");
  });

  it("should render the third card titled Cool your bedroom to 65–68°F", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.contains("Cool your bedroom to 65–68°F").should("be.visible");
  });

  it("should render follow-up chips including Nutrition advice and Book a doctor", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.contains("Nutrition advice").should("be.visible");
    cy.contains("Book a doctor").should("be.visible");
  });

  it("should fire onChipSelect callback when follow-up chip is clicked", () => {
    const callback = cy.stub().as("chipSelect");
    cy.mount(
      <SleepRecoveryResponse data={MOCK_DATA} onChipSelect={callback} />,
    );
    cy.contains("Nutrition advice").click();
    cy.get("@chipSelect").should("have.been.calledWith", "Nutrition advice");
  });

  it("should render with visual snapshot", () => {
    cy.mount(<SleepRecoveryResponse data={MOCK_DATA} />);
    cy.compareSnapshot({ name: "sleep-recovery-default", testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD") });
  });
});
