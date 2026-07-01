Feature: Sleep and Recovery Guidance
  Scenario: User requests sleep and recovery advice
    Given I am on the IOPHA homepage
    When I click the "Sleep & recovery" chip
    Then I should see introductory text mentioning "ghrelin" and "leptin"
    And I should see 3 numbered sleep recommendation cards
    And the first card should be titled "Target 7–9 hours with a fixed schedule"
    And the second card should be titled "Screens off 60 minutes before bed"
    And the third card should be titled "Cool your bedroom to 65–68°F"
    And I should see follow-up chips including "Nutrition advice" and "Book a doctor"
