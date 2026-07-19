const log = require("git-log-parser");
const through2 = require("through2");
const { writeFile } = require("fs");
const { promisify } = require("util");

const writeFileAsync = promisify(writeFile);

// Configuration
const REPO_OWNER = "DragonStone12";
const REPO_NAME = "IOPHA";
const BASE_GITHUB_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}`;
const COMMIT_URL_BASE = `${BASE_GITHUB_URL}/commit`;

// Inputs from GitHub Actions Environment (or defaults).
// The workflow is the single source of truth for sanitization: it derives a
// clean tag (strips the "release/" prefix, removes illegal chars) and passes
// it here as RELEASE_VERSION. The script only applies a minimal safety net so
// a missing/empty value still yields a valid filename.
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

    const commitLink = createCommitLink(commit.commit.short);

    // Format: - Subject (CommitHash)
    const formattedMessage = `- ${commit.subject} (${commitLink})`;

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
