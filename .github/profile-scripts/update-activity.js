const fs = require('node:fs/promises');

const user = process.env.GITHUB_USER || 'DzCodeProgrammer';
const token = process.env.GITHUB_TOKEN;
const startMarker = '<!--START_SECTION:activity-->';
const endMarker = '<!--END_SECTION:activity-->';

const headers = {
  Accept: 'application/vnd.github+json',
  'User-Agent': 'DzCodeProgrammer-profile-automation',
  'X-GitHub-Api-Version': '2022-11-28',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
};

function repoLink(repo) {
  return `[${repo}](https://github.com/${repo})`;
}

function issueLink(repo, issue) {
  return `[#${issue.number}](https://github.com/${repo}/issues/${issue.number})`;
}

function pullLink(repo, pull) {
  return `[#${pull.number}](https://github.com/${repo}/pull/${pull.number})`;
}

function formatEvent(event) {
  const repo = event.repo.name;
  const payload = event.payload;

  switch (event.type) {
    case 'PushEvent':
      return `💻 Pushed ${payload.size || payload.commits?.length || 0} commit(s) to ${repoLink(repo)}`;
    case 'PullRequestEvent':
      return `🔀 ${payload.action} pull request ${pullLink(repo, payload.pull_request)} in ${repoLink(repo)}`;
    case 'IssuesEvent':
      return `❗ ${payload.action} issue ${issueLink(repo, payload.issue)} in ${repoLink(repo)}`;
    case 'IssueCommentEvent':
      return `💬 Commented on ${issueLink(repo, payload.issue)} in ${repoLink(repo)}`;
    case 'CreateEvent':
      return `🆕 Created ${payload.ref_type}${payload.ref ? ` \`${payload.ref}\`` : ''} in ${repoLink(repo)}`;
    case 'ForkEvent':
      return `🍴 Forked ${repoLink(repo)}`;
    case 'ReleaseEvent':
      return `🚀 ${payload.action} release [${payload.release.tag_name}](${payload.release.html_url}) in ${repoLink(repo)}`;
    case 'WatchEvent':
      return `⭐ Starred ${repoLink(repo)}`;
    default:
      return null;
  }
}

async function main() {
  const response = await fetch(`https://api.github.com/users/${encodeURIComponent(user)}/events/public?per_page=100`, { headers });
  if (!response.ok) {
    throw new Error(`GitHub events request failed: ${response.status} ${(await response.text()).slice(0, 300)}`);
  }

  const events = await response.json();
  if (!Array.isArray(events)) throw new Error('GitHub events response was not an array');

  const activity = events.map(formatEvent).filter(Boolean).slice(0, 5);
  if (!activity.length) {
    console.log('No supported public activity was found; README was not changed.');
    return;
  }

  const readme = await fs.readFile('README.md', 'utf8');
  const start = readme.indexOf(startMarker);
  const end = readme.indexOf(endMarker);
  if (start === -1 || end === -1 || end <= start) {
    throw new Error('README activity markers are missing or out of order');
  }

  const numberedActivity = activity.map((item, index) => `${index + 1}. ${item}`).join('\n\n');
  const replacement = `${startMarker}\n\n${numberedActivity}\n\n${endMarker}`;
  const updated = `${readme.slice(0, start)}${replacement}${readme.slice(end + endMarker.length)}`;

  if (updated === readme) {
    console.log('Public activity is already current.');
    return;
  }

  await fs.writeFile('README.md', updated);
  console.log(`Updated README with ${activity.length} public activities.`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
