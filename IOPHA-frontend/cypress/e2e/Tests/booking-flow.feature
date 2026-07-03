Feature: Appointment Booking Flow
  Scenario: User views the time selection screen
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    Then I should see the "Select Appointment Time" screen
    And I should see "Choose a Date" heading
    And I should see "Choose a Time" heading
    And I should see "Back to Health Assistant" link
    And I should see "Back to search" link
    And I should not see the summary bar
    And I should see the time selector initial state

  Scenario: User selects a date and time
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    Then I should see time slots available
    When I select a time slot
    Then I should see the summary bar
    And I should see "Selected appointment:" text
    And I should see "Continue to Confirmation" button
    And I should see the time selector with selection state

  Scenario: User continues to confirmation form
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    Then I should see the "Confirm Your Appointment" screen
    And I should see "Patient Information" heading
    And I should see "Appointment Details" heading
    And I should see "Back to calendar" link
    And I should see the confirmation form default state

  Scenario: User fills out confirmation form with valid data
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I fill in the patient name field with "John Doe"
    And I fill in the patient email field with "john@example.com"
    And I fill in the patient phone field with "1234567890"
    And I click the "Confirm Appointment" button
    Then I should see the "Appointment Confirmed!" screen
    And I should see "Change date or time" link
    And I should not see a "Done" button
    When I wait for 3 seconds
    Then I should see the chat interface
    And I should see the appointment confirmation box in chat

  Scenario: User attempts to submit form with empty fields
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I click the "Confirm Appointment" button without filling fields
    Then I should see validation errors for required fields
    And I should see the confirmation form with validation errors

  Scenario: User navigates back from time selection
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I click the "Back to Health Assistant" link
    Then I should see the chat interface

  Scenario: User navigates back from confirmation form
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I click the "Back to calendar" link
    Then I should see the "Select Appointment Time" screen

  Scenario: User changes date or time from confirmation form
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I click the "Change date or time" link
    Then I should see the "Select Appointment Time" screen

  Scenario: User corrects a validation error
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I click the "Confirm Appointment" button without filling fields
    Then I should see validation errors for required fields
    When I fill in the patient name field with "John Doe"
    Then I should not see the name validation error
    And I should see the corrected form state

  Scenario: User starts booking by clicking on a doctor's name
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click on "Dr. Emily Chen, MD" physician name
    Then I should see the "Select Appointment Time" screen
    And I should see "Choose a Date" heading

  Scenario: User sees appointment confirmation in chat after booking
    Given I am on the IOPHA homepage
    When I click the "Find a doctor" chip
    And I click the "Book" button on a physician card
    And I select a date on the calendar
    And I select a time slot
    And I click the "Continue to Confirmation" button
    And I fill in the patient name field with "John Doe"
    And I fill in the patient email field with "john@example.com"
    And I fill in the patient phone field with "1234567890"
    And I click the "Confirm Appointment" button
    When I wait for 3 seconds
    Then I should see the appointment confirmation box in chat
