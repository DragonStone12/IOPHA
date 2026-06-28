Feature: Weight and Nutrition Guidance
  Scenario: User selects weight and nutrition tips
    Given I am on the IOPHA homepage
    When I click the "Weight & nutrition tips" chip
    Then I should see the introductory text mentioning "irregular meal timing"
    And I should see 3 numbered dietary adjustment cards
    And I should see a physician card for "Dr. Emily Chen"
    And I should see a "Book" button on the physician card
    And I should see follow-up chips including "Exercise tips" and "Book Dr. Chen"
