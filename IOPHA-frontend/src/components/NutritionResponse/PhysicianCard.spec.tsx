import { PhysicianCard } from "./PhysicianCard";
import type { Physician } from "./PhysicianCard";

const MOCK_PHYSICIAN: Physician = {
  id: "dr-chen",
  name: "Dr. Emily Chen, MD",
  specialty: "Obesity & Metabolic Medicine",
  distance: "1.8 miles",
  rating: 4.9,
  reviewCount: 234,
  nextAvailable: "Today, 3:30 PM",
  imageUrl:
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
};

describe("PhysicianCard Component", () => {
  it("should render physician name", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("Dr. Emily Chen, MD").should("be.visible");
  });

  it("should render physician specialty", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("Obesity & Metabolic Medicine").should("be.visible");
  });

  it("should render distance", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("1.8 miles").should("be.visible");
  });

  it("should render rating and review count", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("4.9 (234)").should("be.visible");
  });

  it("should render next available time", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("Today, 3:30 PM").should("be.visible");
  });

  it("should render Book button", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.contains("Book").should("be.visible");
  });

  it("should fire onBook callback when Book button is clicked", () => {
    const callback = cy.stub().as("bookCallback");
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} onBook={callback} />);
    cy.contains("Book").click();
    cy.get("@bookCallback").should("have.been.calledWith", MOCK_PHYSICIAN);
  });

  it("should render initials in avatar when no image provided", () => {
    const physicianWithoutImage: Physician = {
      ...MOCK_PHYSICIAN,
      imageUrl: undefined,
    };
    cy.mount(<PhysicianCard physician={physicianWithoutImage} />);
    cy.contains("EC").should("be.visible");
    cy.compareSnapshot("physician-card-no-image");
  });

  it("should render hover state", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.get("div").first().trigger("mouseover");
    cy.compareSnapshot("physician-card-hover");
  });

  it("should have aria-label for rating", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.get('[aria-label*="Rating 4.9"]').should("exist");
  });

  it("should have aria-label for Book button", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.get('[aria-label*="Book appointment"]').should("exist");
  });

  it("should apply custom className", () => {
    cy.mount(
      <PhysicianCard physician={MOCK_PHYSICIAN} className="custom-class" />,
    );
    cy.get(".custom-class").should("exist");
  });

  it("should render with visual snapshot", () => {
    cy.mount(<PhysicianCard physician={MOCK_PHYSICIAN} />);
    cy.compareSnapshot("physician-card-default");
  });
});
