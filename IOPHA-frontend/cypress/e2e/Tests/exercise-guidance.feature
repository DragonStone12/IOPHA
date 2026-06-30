Feature: Exercise Guidance
  Scenario: User requests exercise guidance
    Given I am on the IOPHA homepage
    When I click the "Exercise guidance" chip
    Then I should see introductory text mentioning "ACSM protocol" and "BMI"
    And I should see 3 numbered exercise recommendation cards
    And the first card should be titled "Start with daily walking"
    And the second card should be titled "Resistance training twice weekly"
    And the third card should be titled "Maximize NEAT (non-exercise activity)"
    And I should see follow-up chips including "Nutrition tips" and "Find a doctor"
