import { ChatArea } from "./ChatArea";

describe("ChatArea Component", () => {
  it("should render greeting message with correct template", () => {
    cy.mount(
      <ChatArea
        userName="Jane Smith"
        hospitalName="Test Hospital"
        riskScore={75}
      />,
    );
    cy.contains("Welcome, Jane Smith").should("be.visible");
    cy.contains("Test Hospital AI assistant").should("be.visible");
    cy.contains("75/100").should("be.visible");
    cy.compareSnapshot({ name: "chat-area-default", testThreshold: 0.05 });
  });

  it("should render all 4 action chips", () => {
    cy.mount(<ChatArea />);
    cy.get("main .flex-wrap button").should("have.length", 4);
    cy.contains("Weight & nutrition tips").should("be.visible");
    cy.contains("Find a doctor").should("be.visible");
    cy.contains("Exercise guidance").should("be.visible");
    cy.contains("Sleep & recovery").should("be.visible");
  });

  it("should fire onTopicSelect callback when chip is clicked", () => {
    const callback = cy.stub().as("topicSelect");
    cy.mount(<ChatArea onTopicSelect={callback} />);
    cy.contains("Find a doctor").click();
    cy.get("@topicSelect").should("have.been.calledWith", "find_a_doctor");
  });

  it("should fire onTopicSelect for all topics", () => {
    const callback = cy.stub().as("topicSelect");
    cy.mount(<ChatArea onTopicSelect={callback} />);
    cy.contains("Weight & nutrition tips").click();
    cy.get("@topicSelect").should("have.been.calledWith", "nutrition_tips");
    cy.contains("Exercise guidance").click();
    cy.get("@topicSelect").should("have.been.calledWith", "exercise_guidance");
    cy.contains("Sleep & recovery").click();
    cy.get("@topicSelect").should("have.been.calledWith", "sleep_recovery");
  });

  it("should have input field with correct placeholder", () => {
    cy.mount(<ChatArea />);
    cy.get('input[placeholder*="Ask about nutrition"]').should("be.visible");
  });

  it("should have send button", () => {
    cy.mount(<ChatArea />);
    cy.get("button").should("exist");
  });

  it("should render disclaimer text", () => {
    cy.mount(<ChatArea />);
    cy.contains("AI responses are for informational purposes only").should(
      "be.visible",
    );
    cy.contains("Not a substitute for professional medical advice").should(
      "be.visible",
    );
  });

  it("should have hover states on action chips", () => {
    cy.mount(<ChatArea />);
    cy.contains("Find a doctor")
      .trigger("mouseover")
      .should("have.class", "hover:bg-primary/10");
  });
});
