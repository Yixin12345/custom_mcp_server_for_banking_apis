package org.opencart.stepDefinition;

import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.PendingException;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import org.opencart.pages.LoginPage;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;

import java.time.Duration;

public class LoginPageStepDefinition {
    private WebDriver driver;
    private LoginPage loginPage;


    @Before
    public void setup(){
        driver = new ChromeDriver();
        loginPage = new LoginPage(driver);

    }

    @After
    public void tearDown(){
        if(driver!=null){
            driver.quit();
        }
    }

    @Given("I am on the Opencart login page")
    public void i_am_on_the_opencart_login_page() {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        loginPage.navigate_to_opencart_login_page();
    }

    @Given("I have entered a valid username and password")
    public void i_have_entered_a_valid_username_and_password() {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        loginPage.enter_email_address("yashtest@gmail.com");
        loginPage.enter_password("Test@123");
    }

    @When("I click on the login screen")
    public void i_click_on_the_login_screen() {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        loginPage.click_login_button();
    }

    @Then("I should be logged in successfully")
    public void i_should_be_logged_in_successfully() {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        String pageTitle = "My Account";

        String title = loginPage.getMyAccountPageTitle();
        System.out.println("Retrieved Page Title: " + title);
        Assert.assertEquals(title, pageTitle);
    }

    @Given("I have entered invalid {string} and {string}")
    public void i_have_entered_invalid_and(String username, String password) {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        loginPage.enter_email_address(username);
        loginPage.enter_password(password);
    }

    @Then("I should see an error message indicating {string}")
    public void i_should_see_an_error_message_indicating(String error_message) {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        String error = loginPage.validateLoginError();
//        Assert.assertEquals(error, error_message);
        System.out.println("********************* "+ error+ " *********************");
        Assert.assertTrue(error.contains("match"));
    }

    @Then("I should be redirected to the password reset page")
    public void i_should_be_redirected_to_the_password_reset_page() {
        // Write code here that turns the phrase above into concrete actions
//        throw new io.cucumber.java.PendingException();
        String url = loginPage.validateStringInLink();
        Assert.assertTrue(url.contains("account/forgotten"));

    }


    @When("I click on the Forgotten Password link")
    public void iClickOnTheForgottenPasswordLink() {
        // Write code here that turns the phrase above into concrete actions
//        throw new PendingException();
        loginPage.clickForgottenPasswordLink();

    }

}
