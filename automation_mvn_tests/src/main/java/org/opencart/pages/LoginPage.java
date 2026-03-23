package org.opencart.pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;

import java.time.Duration;

public class LoginPage {

    private WebDriver driver;

    private final By emailAddress = By.xpath("//input[@name='email']");
    private final By password = By.xpath("//input[@name='password']");
    private final By loginButton = By.cssSelector("[type='submit']");
    private final By MyAccountPageTitle = By.cssSelector("[title='My Account']");
    private final By loginErrorMessage = By.xpath("//div[@class='alert alert-danger alert-dismissible']");
    private final By forgottenPasswordLink = By.xpath("//a[text()='Forgotten Password']");


    public LoginPage(WebDriver driver) {
        this.driver = driver;
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
    }


    public void navigate_to_opencart_login_page() {
        String url = "https://naveenautomationlabs.com/opencart/index.php?route=account/login";
        driver.get(url);
    }

    public void enter_email_address(String email){
        driver.findElement(emailAddress).sendKeys(email);
    }

    public void enter_password(String pwd){
        driver.findElement(password).sendKeys(pwd);
    }

    public void click_login_button(){
        driver.findElement(loginButton).click();
    }

    public String getMyAccountPageTitle(){
        //        return page_title.equals(expectedPageTitle);
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        WebElement titleName = wait.until(ExpectedConditions.presenceOfElementLocated(MyAccountPageTitle));
        return titleName.getText();
    }

    public String validateLoginError(){
        return driver.findElement(loginErrorMessage).getText();
    }

    public void clickForgottenPasswordLink(){
        driver.findElement(forgottenPasswordLink).click();
    }

    public String validateStringInLink(){
        return driver.getCurrentUrl();
    }
}
