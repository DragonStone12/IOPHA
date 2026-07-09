# SARIF for Security Analysis

## Why SARIF?

SARIF (Static Analysis Results Interchange Format) is the industry-standard format for representing static analysis tool output. Using SARIF for Bandit security analysis provides:

- **Native GitHub Integration**: SARIF files can be uploaded directly to GitHub Code Scanning, enabling security alerts to appear in the repository's Security tab.
- **Structured & Machine-Readable**: SARIF's JSON schema ensures consistent, parseable results that GitHub can index and track across commits.
- **Deduplication**: The `partialFingerprints` property allows GitHub to prevent duplicate alerts when the same issue is found across multiple runs.
- **Categorization**: Using the `category` input, multiple analyses for the same commit (e.g., different tools or language subsets) can be uploaded and reviewed independently.
- **Alert Management**: Security findings become actionable items in GitHub, assignable, labelable, and trackable within the repository workflow.

By uploading Bandit output as SARIF, we turn raw command-line findings into integrated, manageable security advisories in GitHub.
