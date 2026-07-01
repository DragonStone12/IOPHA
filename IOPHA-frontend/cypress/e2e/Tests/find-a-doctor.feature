Feature: Find a Doctor
  Scenario: User searches for nearby physicians
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    Then I should see a summary mentioning "Baylor Scott & White physicians" and "Dallas"
    And I should see a physician card for "Dr. Emily Chen" with "1.8 miles" distance
    And I should see a physician card for "Dr. Raj Patel" with "2.4 miles" distance
    And each physician card should have a "Book" button
    And I should see follow-up chips including "Book with Dr. Chen" and "Get health tips first"
