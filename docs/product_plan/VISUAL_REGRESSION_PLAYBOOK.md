# Visual Regression Testing Best Practices Playbook
**For IOPHA Frontend (Cypress + Cucumber + React/Vite)**

## Overview
Visual regression testing guards against unintended UI changes, layout shifts, broken components, and styling regressions that functional tests miss. This guide is tailored for our Cypress setup with Cucumber BDD testing.

---

## 1. Ensure Consistent Rendering with Browser Launch Flags

Visual test failures often trace back to differences in screen resolution, scaling, or GPU rendering across environments. Normalize the rendering environment via browser flags in your Cypress configuration.

**Update `cypress.config.ts`:**
```typescript
export default defineConfig({
  e2e: {
    viewportWidth: 1280,
    viewportHeight: 720,
    setupNodeEvents(on, config) {
      on('before:browser:launch', (browser = {}, launchOptions) => {
        if (browser.name === 'chrome' || browser.name === 'chromium') {
          launchOptions.args.push('--force-device-scale-factor=1');
          launchOptions.args.push('--disable-gpu');
          launchOptions.args.push('--window-size=1280,720');
          launchOptions.args.push('--font-render-hinting=none');
        }
        return launchOptions;
      });
      // ... rest of your setup
    },
  },
});
```

---

## 2. Normalize Dynamic or Transient Content

Dynamic values such as timestamps, random IDs, or user-specific data produce false-positive diffs. Before taking a snapshot, intercept, mock, or mutate any DOM content that varies between sessions.

**In your Cucumber step definitions:**
```typescript
// Remove dynamic timestamps
cy.get('.timestamp, .date').invoke('text', '[DATE]');

// Normalize user-specific content
cy.get('.user-name').invoke('text', 'Test User');

// Mock API responses for consistent data
cy.intercept('/api/appointments', { 
  fixture: 'appointments-mock.json' 
});
```

---

## 3. Wait for All Visual Elements Before Snapshot

Snapshots taken before images, fonts, or SVGs finish loading produce inconsistent results. Assert that all critical visual components are present before capturing.

**Step definition example:**
```typescript
Then('the dashboard should look correct', () => {
  // Wait for critical visual elements
  cy.get('[data-testid="dashboard-main"]')
    .find('img, svg, .chart-container')
    .should('have.length.gt', 0);
  
  // Ensure fonts are loaded
  cy.get('body').should('have.css', 'font-family').and('not.be.empty');
  
  // Now take snapshot
  cy.get('[data-testid="dashboard-main"]')
    .matchImageSnapshot('dashboard-main-view');
});
```

---

## 4. Keep Snapshots Isolated and Scoped

**✅ DO: Target scoped, stable regions**
```gherkin
Then("the appointment form should render correctly")
  cy.get('[data-testid="appointment-form"]')
    .matchImageSnapshot('appointment-form-desktop');
```

**❌ DON'T: Full-page snapshots (too volatile)**
```typescript
// Avoid this - too many moving parts
cy.matchImageSnapshot(); 
```

**Use `data-testid` attributes for stability:**
```tsx
// In your React components
<div data-testid="booking-summary">
  {/* Content */}
</div>
```

---

## 5. Use Meaningful Snapshot Names

Vague names make debugging difficult. Use descriptive names that reflect the UI area and state.

**Good naming convention:**
```typescript
.matchImageSnapshot('checkout-form-desktop');
.matchImageSnapshot('header-logged-in');
.matchImageSnapshot('appointment-card-mobile');
```

**Add context with custom identifiers:**
```typescript
.matchImageSnapshot({
  customSnapshotIdentifier: 'booking-flow-step-2-desktop',
});
```

---

## 6. Commit Baseline Snapshots to Source Control

Track snapshot PNG files in version control to maintain historical traceability and make visual changes reviewable in pull requests.

**Store snapshots in:**
```text
IOPHA-frontend/cypress/snapshots/
```

**Update `.gitattributes`:**
```gitattributes
# Mark snapshots as binary
cypress/snapshots/**/*.png binary
cypress/screenshots/**/*.png binary
```

---

## 7. Review Diffs Carefully - Avoid Blind Updates

**NEVER commit `updateSnapshots: true`**. Treat snapshot failures as signals to investigate, not inconveniences to dismiss.

**Add ESLint rule to block accidental updates:**
```javascript
// .eslintrc.js
rules: {
  'no-restricted-syntax': [
    'error',
    {
      selector: "Property[key.name='updateSnapshots'][value.raw='true']",
      message: 'Do not commit updateSnapshots: true. Review visual diffs manually.',
    },
  ],
}
```

**Add Husky pre-commit hook:**
```bash
#!/usr/bin/env sh
# .husky/pre-commit

if git diff --cached -U0 | grep -E '^\+.*updateSnapshots.*(true|=true)' | grep -qv '^---'; then
  echo ""
  echo "❌ Blocked: updateSnapshots=true detected in staged changes."
  echo "Review visual diffs before updating snapshot baselines."
  echo ""
  exit 1
fi
```

**If update is intentional:**
1. Review the diff image carefully
2. Run with update flag locally: `npm run cy:run -- --env updateSnapshots=true`
3. Commit snapshots in a separate commit with message:
   ```bash
   git commit -m "chore: update visual snapshots after booking UI redesign [snap-update]"
   ```

---

## 8. Use CI for Visual Testing with Fixed Environments

Your GitHub Actions workflow already provides a consistent environment. Visual tests run in CI against Ubuntu with headless Chrome, ensuring consistency.

**Current CI setup (ci-frontend.yml):**
```yaml
- name: Cypress Run
  uses: cypress-io/github-action@v7
  with:
    working-directory: IOPHA-frontend
    build: npm run build
    start: npm run dev
    wait-on: 'http://localhost:3000'
    command: npx cypress run --e2e --browser chrome
```

**Upload diff artifacts on failure:**
```yaml
- name: Upload visual diffs
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: visual-diffs-chrome
    path: IOPHA-frontend/cypress/snapshots/**/__diff_output__/*.png
    if-no-files-found: ignore
```

---

## 9. Threshold Configuration and Sensitivity Tuning

Pixel-by-pixel comparison is sensitive. Configure thresholds based on component criticality.

**In your test setup:**
```typescript
// For critical components (checkout, booking)
cy.get('[data-testid="checkout-form"]').matchImageSnapshot({
  failureThreshold: 0.005, // 0.5% tolerance
  failureThresholdType: 'percent',
  customDiffConfig: { threshold: 0.1 }, // Antialiasing fuzz
});

// For less critical areas
cy.get('[data-testid="footer"]').matchImageSnapshot({
  failureThreshold: 0.03, // 3% tolerance
  failureThresholdType: 'percent',
});
```

---

## 10. Responsive Design Testing

Test across multiple viewport sizes to catch responsive regressions.

**Cucumber scenario example:**
```gherkin
Scenario: Booking form renders correctly on mobile
  Given I set viewport to 375x667
  When I visit the booking page
  Then the booking form should look correct on mobile

Scenario: Booking form renders correctly on tablet
  Given I set viewport to 768x1024
  When I visit the booking page
  Then the booking form should look correct on tablet
```

**Step definition:**
```typescript
Given('I set viewport to {int}x{int}', (width: number, height: number) => {
  cy.viewport(width, height);
});

Then('the booking form should look correct on mobile', () => {
  cy.get('[data-testid="booking-form"]')
    .matchImageSnapshot('booking-form-mobile-375x667');
});
```

---

## 11. Handle Third-Party Content

Uncontrolled third-party content (maps, ads, embeds) produces inconsistent diffs. Mock or remove them before snapshotting.

```typescript
// Remove third-party widgets
cy.get('#analytics-widget').invoke('remove');

// Replace maps with placeholder
cy.get('#map-container').invoke('html', 
  '<div class="map-placeholder" style="height: 200px; background: #eee;"></div>'
);

// Block external requests
cy.intercept('https://maps.googleapis.com/**', { 
  statusCode: 204 
});
```

---

## 12. Component-Level vs Integration Testing

**Use component tests** (future: Storybook + Cypress Component Testing) for:
- Discrete UI states: Button:disabled, Card:hover, Form:loading
- Isolated validation
- Faster feedback

**Use integration tests** (current Cucumber E2E) for:
- Full page layouts
- Multi-component interactions
- End-to-end user flows

---

## 13. Performance Considerations

Visual tests add runtime and storage overhead.

**Optimizations:**
1. **Scope snapshots** to key regions, not full pages
2. **Use `.only()` locally** during development:
   ```gherkin
   Scenario.only("Critical checkout flow")
   ```
3. **Run full suite only in CI**
4. **Clean up old diffs regularly:**
   ```json
   // Add to package.json
   "scripts": {
     "cy:clean-diffs": "find cypress/snapshots -type f -name '*.diff.png' -delete"
   }
   ```

---

## 14. Handling Flaky Tests

Common causes: animations, delayed rendering, third-party content.

**Stabilization techniques:**
```typescript
// Disable CSS transitions
cy.document().then((doc) => {
  const style = doc.createElement('style');
  style.innerHTML = '* { transition: none !important; animation: none !important; }';
  doc.head.appendChild(style);
});

// Wait for network idle
cy.intercept('GET', '/api/**').as('apiCall');
cy.wait('@apiCall');

// Assert visibility before snapshot
cy.get('[data-testid="modal"]')
  .should('be.visible')
  .matchImageSnapshot('modal-open');
```

---

## 15. Accessibility Integration

Visual testing extends to accessibility validation.

**Test high contrast mode:**
```typescript
Then('the form should be accessible in high contrast mode', () => {
  cy.document().then((doc) => {
    const style = doc.createElement('style');
    style.innerHTML = `
      * { 
        background-color: black !important; 
        color: yellow !important; 
        border-color: white !important; 
      }
    `;
    doc.head.appendChild(style);
  });
  
  cy.get('[data-testid="appointment-form"]')
    .matchImageSnapshot('form-high-contrast');
});
```

**Test large fonts:**
```typescript
cy.document().then((doc) => {
  doc.body.style.fontSize = '1.5em';
});
cy.get('[data-testid="settings"]').matchImageSnapshot('settings-large-font');
```

---

## 16. Reporting and Analytics

**Track visual regression metrics:**
- Number of failing snapshots per build
- Most volatile UI components
- Time-to-review on diffs
- Percentage of PRs with snapshot updates

**Upload diff artifacts in CI:**
```yaml
- name: Upload visual diffs
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: visual-regression-diffs
    path: IOPHA-frontend/cypress/snapshots/**/__diff_output__/
```

**Tag snapshots for tracking:**
```typescript
.matchImageSnapshot('checkout|critical|mobile');
.matchImageSnapshot('header|low-priority|desktop');
```

---

## 17. Maintenance and Cleanup

**Prevent snapshot bloat:**
1. **Remove orphaned snapshots** when components are deleted
2. **Version baselines** with meaningful tags:
   ```bash
   git tag v1.2.0-booking-ui-refresh
   ```
3. **Document major visual changes** in PR descriptions

**Add cleanup script:**
```json
{
  "scripts": {
    "cy:clean-snapshots": "find cypress/snapshots -name '*.diff.png' -delete",
    "cy:clean-unused": "node scripts/cleanup-unused-snapshots.js"
  }
}
```

---

## 18. Installation and Setup

**Install cypress-image-snapshot:**
```bash
cd IOPHA-frontend
npm install --save-dev cypress-image-snapshot
```

**Add to `cypress/support/e2e.ts`:**
```typescript
import { addMatchImageSnapshotCommand } from 'cypress-image-snapshot/command';

addMatchImageSnapshotCommand({
  failureThreshold: 0.01,
  failureThresholdType: 'percent',
  customDiffConfig: { threshold: 0.1 },
  capture: 'viewport',
});
```

**Configure in `cypress.config.ts`:**
```typescript
import { configureMatchImageSnapshot } from 'cypress-image-snapshot/plugin';

export default defineConfig({
  e2e: {
    async setupNodeEvents(on, config) {
      configureMatchImageSnapshot(on, config);
      // ... rest of your setup
      return config;
    },
  },
});
```

---

## Quick Reference Card

| **Do** | **Don't** |
|--------|-----------|
| Use `data-testid` selectors | Use full-page snapshots |
| Wait for elements to load | Use `cy.wait()` arbitrarily |
| Scope to stable regions | Blindly update snapshots |
| Use meaningful names | Ignore diff reviews |
| Run in CI consistently | Run visual tests locally only |
| Commit baselines to Git | Store snapshots only locally |
| Mock dynamic content | Test with live unpredictable data |

---

## Next Steps

1. **Install cypress-image-snapshot** in IOPHA-frontend
2. **Add visual test scenarios** to critical user flows (booking, checkout)
3. **Configure browser launch flags** in cypress.config.ts
4. **Add ESLint rule** to block `updateSnapshots: true`
5. **Update Husky pre-commit hook** to check for snapshot updates
6. **Create baseline snapshots** for current UI state
7. **Add diff artifact upload** to ci-frontend.yml

---

**Remember:** Visual regression testing is about catching unintended changes, not preventing intentional ones. Review every diff, understand every failure, and update baselines deliberately.
