Feature: Login functionality for e-Commerce website OPENCART

  As a user of the OpenCart website
  I want to be able to log in with my account
  So that I can access my account-related features and manage my orders

  Background:
    Given I am on the Opencart login page
  @login
  Scenario: Successful login with valid credentials
    Given I have entered a valid username and password
    When I click on the login screen
    Then I should be logged in successfully

  Scenario Outline: Unsuccessful login with invalid or empty credentials
    Given I have entered invalid "<username>" and "<password>"
    When I click on the login screen
    Then I should see an error message indicating '<error_message>'

    Examples:
    | username  | password    | error_message                                         |
    | yashpal   | abc@123     | Warning: No match for E-Mail Address and/or Password  |
    | ysharma   | invalid     | Warning: No match for E-Mail Address and/or Password  |

  Scenario: Navigating to the forgotten password page
    When I click on the Forgotten Password link
    Then I should be redirected to the password reset page
