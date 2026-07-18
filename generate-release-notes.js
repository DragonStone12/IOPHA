const log = require("git-log-parser");
const through2 = require("through2");
const { writeFile } = require("fs");
const { promisify } = require("util");

const writeFileAsync = promisify(writeFile);

// Configuration
const REPO_OWNER = "DragonStone12";
const REPO_NAME = "IOPHA";
const BASE_GITHUB_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}`;
const ISSUE_URL_BASE = `${BASE_GITHUB_URL}/issues`;
const PULL_URL_BASE = `${BASE_GITHUB_URL}/pull`;
const COMMIT_URL_BASE = `${BASE_GITHUB_URL}/commit`;

// Inputs from GitHub Actions Environment (or defaults)
const VERSION = process.env.RELEASE_VERSION || "1.0.0";
const OUTPUT_FILE = `release-notes-${VERSION}.md`;

// Start of the release window: the repository's first commit (root commit).
// Falls back to SINCE_DAYS (default 7) when git is unavailable.
const SINCE_DAYS = parseInt(process.env.SINCE_DAYS || "7", 10);

const execGit = (cmd) => {
  const { execSync } = require("child_process");
  return execSync(cmd, { encoding: "utf8" }).trim();
};

const getFirstCommitDate = () => {
  try {
    const hash = execGit("git rev-list --max-parents=0 HEAD");
    return new Date(execGit(`git show -s --format=%aI ${hash}`));
  } catch {
    return null;
  }
};

const firstCommitDate = getFirstCommitDate();
const since = firstCommitDate || new Date(Date.now() - SINCE_DAYS * 24 * 60 * 60 * 1000);
const until = new Date();

/**
 * Extracts GitHub issue numbers from a commit message.
 * Matches patterns like #123, fixes #123, closes #123
 */
const extractIssueNumbers = (message) => {
  const regex = /#(\d+)/g;
  const matches = [...message.matchAll(regex)];
  return matches.map((match) => match[1]);
};

/**
 * Constructs the markdown link for an issue
 */
const createIssueLink = (issueNumber) => {
  return `[#${issueNumber}](${ISSUE_URL_BASE}/${issueNumber})`;
};

/**
 * Constructs the markdown link for a commit
 */
const createCommitLink = (shortHash) => {
  return `[${shortHash}](${COMMIT_URL_BASE}/${shortHash})`;
};

/**
 * Categorizes a commit based on its subject line
 */
const categorizeCommit = (subject) => {
  if (/merge/i.test(subject)) return "Merge Commit";
  if (/^(feat|add)/i.test(subject)) return "Features";
  if (/^(fix|bug)/i.test(subject)) return "Bug Fixes";
  return "Other";
};

/**
 * Main processing function
 */
const generateReleaseNotes = async () => {
  const commits = [];

  // Stream git logs
  await new Promise((resolve, reject) => {
    log
      .parse({ since, until })
      .pipe(
        through2.obj((chunk, _, callback) => {
          commits.push(chunk);
          callback();
        }),
      )
      .on("finish", resolve)
      .on("error", reject);
  });

  // Organize commits by category
  const headingsAndMessages = {
    Features: [],
    "Bug Fixes": [],
    "Merge Commit": [],
    Other: [],
  };

  commits.forEach((commit) => {
    const category = categorizeCommit(commit.subject);
    const issueNumbers = extractIssueNumbers(
      `${commit.subject} ${commit.body || ""}`,
    );

    // Build hyperlinked issue links from the commit message (#123, fixes #123).
    const issueLinks =
      issueNumbers.length > 0
        ? ` (${issueNumbers.map((num) => createIssueLink(num)).join(", ")})`
        : "";

    const commitLink = createCommitLink(commit.commit.short);

    // Format: - Subject (CommitHash) (#Issue1, #Issue2)
    const formattedMessage = `- ${commit.subject} (${commitLink})${issueLinks}`;

    if (headingsAndMessages[category]) {
      headingsAndMessages[category].push(formattedMessage);
    } else {
      headingsAndMessages["Other"].push(formattedMessage);
    }
  });

  // Construct Markdown
  let markdownContent = `# IOPHA Release [${VERSION}](${BASE_GITHUB_URL}/releases/tag/v${VERSION})\n\n`;
  markdownContent += `*Release Date: ${
    new Date().toISOString().split("T")[0]
  }*\n\n`;

  Object.entries(headingsAndMessages).forEach(([heading, messages]) => {
    if (messages.length > 0) {
      markdownContent += `## ${heading}\n\n`;
      messages.forEach((msg) => {
        markdownContent += `${msg}\n`;
      });
      markdownContent += "\n";
    }
  });

  // Append the version to the end of the content
  const contentWithVersion = `${markdownContent}\n${VERSION}\n`;

  // Write the versioned release notes file (e.g. release-notes-1.0.0.md)
  try {
    await writeFileAsync(OUTPUT_FILE, contentWithVersion);
    console.log(`Successfully generated ${OUTPUT_FILE}`);
  } catch (error) {
    console.error("Failed to create release notes file", error);
    process.exit(1);
  }
};

// Execute
generateReleaseNotes();
