import { FindDoctorResponse } from "./FindDoctorResponse";
import type { Provider } from "./FindDoctorResponse";

const MOCK_PROVIDERS: Provider[] = [
  {
    id: "dr-chen",
    name: "Dr. Emily Chen, MD",
    specialty: "Obesity & Metabolic Medicine",
    facility: "Baylor University Medical Center",
    distanceMiles: 1.8,
    rating: 4.9,
    reviewCount: 234,
    nextAvailableSlot: "Today, 3:30 PM",
    imageUrl:
      "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=200&h=200&fit=crop&auto=format",
  },
  {
    id: "dr-patel",
    name: "Dr. Raj Patel, MD",
    specialty: "Internal & Preventive Medicine",
    facility: "Baylor Scott & White Medical Center",
    distanceMiles: 2.4,
    rating: 4.8,
    reviewCount: 187,
    nextAvailableSlot: "Tomorrow, 9:00 AM",
    imageUrl:
      "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=200&h=200&fit=crop&auto=format",
  },
];

const MOCK_DATA = {
  summaryText:
    "I have identified two Baylor Scott & White physicians near your location in Dallas who specialize in preventive and obesity medicine. Both are accepting new patients within your network. Dr. Chen at Baylor University Medical Center is the closest — just 1.8 miles away — with availability as early as this afternoon.",
  providers: MOCK_PROVIDERS,
  followUpActions: [
    {
      label: "Book with Dr. Chen",
      actionType: "BOOK_PROVIDER" as const,
      providerId: "dr-chen",
    },
    {
      label: "Book with Dr. Patel",
      actionType: "BOOK_PROVIDER" as const,
      providerId: "dr-patel",
    },
    { label: "Get health tips first", actionType: "PIVOT_TIPS" as const },
  ],
};

describe("FindDoctorResponse Component", () => {
  it("should render the summary text mentioning Baylor Scott & White physicians and Dallas", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.contains("Baylor Scott & White physicians").should("be.visible");
    cy.contains("Dallas").should("be.visible");
  });

  it("should render exactly 2 physician cards", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.get('[role="listitem"]').should("have.length", 2);
  });

  it("should render Dr. Emily Chen with 1.8 miles distance", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.contains("Dr. Emily Chen, MD").should("be.visible");
    cy.contains("1.8 miles").should("be.visible");
  });

  it("should render Dr. Raj Patel with 2.4 miles distance", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.contains("Dr. Raj Patel, MD").should("be.visible");
    cy.contains("2.4 miles").should("be.visible");
  });

  it("should render Book button on each physician card", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.get('button').then(($buttons) => {
      const bookButtons = Cypress.$($buttons).filter((_, btn) => {
        const button = Cypress.$(btn);
        return button.text().trim() === 'Book';
      });
      expect(bookButtons.length).to.equal(2);
    });
  });

  it("should fire onBookProvider callback when Book button is clicked", () => {
    const callback = cy.stub().as("bookProvider");
    cy.mount(<FindDoctorResponse data={MOCK_DATA} onBookProvider={callback} />);
    cy.contains("Book").first().click();
    cy.get("@bookProvider").should("have.been.calledOnce");
    cy.get("@bookProvider").then((calls) => {
      expect(calls.firstCall.args[0]).to.have.property("id", "dr-chen");
    });
  });

  it("should fire onBookProvider callback when doctor name is clicked", () => {
    const callback = cy.stub().as("bookProvider");
    cy.mount(<FindDoctorResponse data={MOCK_DATA} onBookProvider={callback} />);
    cy.contains("Dr. Emily Chen, MD").click();
    cy.get("@bookProvider").should("have.been.called");
  });

  it("should render follow-up chips including Book with Dr. Chen and Get health tips first", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.contains("Book with Dr. Chen").should("be.visible");
    cy.contains("Get health tips first").should("be.visible");
  });

  it("should fire onBookProvider when Book with Dr. Chen chip is clicked", () => {
    const callback = cy.stub().as("bookProvider");
    cy.mount(<FindDoctorResponse data={MOCK_DATA} onBookProvider={callback} />);
    cy.contains("Book with Dr. Chen").click();
    cy.get("@bookProvider").should("have.been.calledOnce");
    cy.get("@bookProvider").then((calls) => {
      expect(calls.firstCall.args[0]).to.have.property("id", "dr-chen");
    });
  });

  it("should fire onChipSelect callback when Get health tips first chip is clicked", () => {
    const callback = cy.stub().as("chipSelect");
    cy.mount(<FindDoctorResponse data={MOCK_DATA} onChipSelect={callback} />);
    cy.contains("Get health tips first").click();
    cy.get("@chipSelect").should("have.been.calledWith", "Get health tips first");
  });

  it("should render the Nearby Baylor Physicians section header", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.contains("Nearby Baylor Physicians").should("be.visible");
  });

  it("should render with visual snapshot", () => {
    cy.mount(<FindDoctorResponse data={MOCK_DATA} />);
    cy.compareSnapshot({
      name: "find-doctor-response-default",
      testThreshold: Cypress.env("SNAPSHOT_TEST_THRESHOLD"),
    });
  });
});
