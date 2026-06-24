import { Given, When, Then, And } from "@badeball/cypress-cucumber-preprocessor/steps";
import app from '../Pages/AppPage.cy';

Given('I am on the IOPHA homepage', () => {
  app.visit();
});

When('I view the page', () => {
  app.verifyPageLoaded();
});

Then('I should see the title {string}', (expectedTitle: string) => {
  app.verifyTitle(expectedTitle);
});