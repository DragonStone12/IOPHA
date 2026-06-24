Feature: App
  Scenario: User views the app
    Given I am on the IOPHA homepage
    When I view the page
    Then I should see the title "IOPHA - Interactive Obesity Prevention Health Assistant"