Feature: Weight and Nutrition Guidance
  Scenario: User selects weight and nutrition tips
    Given I am on the IOPHA homepage
    When I click the "Weight & nutrition tips" chip
    Then I should see the introductory text mentioning "irregular meal timing"
    And I should see 3 numbered dietary adjustment cards
