const fs = require('node:fs/promises');
const path = require('node:path');

const user = process.env.GITHUB_USER || 'DzCodeProgrammer';
const token = process.env.PROFILE_TOKEN || process.env.GITHUB_TOKEN;
const quickChartUrl = process.env.QT_API || 'https://quickchart.io/chart';
const assetsDir = path.resolve('assets');

const githubHeaders = {
  Accept: 'application/vnd.github+json',
  'User-Agent': 'DzCodeProgrammer-profile-automation',
  'X-GitHub-Api-Version': '2022-11-28',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.text();

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} from ${url}: ${body.slice(0, 300)}`);
  }

  try {
    return JSON.parse(body);
  } catch (error) {
    throw new Error(`Invalid JSON from ${url}: ${error.message}`);
  }
}

async function githubGraphql(query, variables) {
  const result = await fetchJson('https://api.github.com/graphql', {
    method: 'POST',
    headers: { ...githubHeaders, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
  });

  if (result.errors?.length) {
    throw new Error(`GitHub GraphQL error: ${result.errors.map((item) => item.message).join('; ')}`);
  }

  return result.data;
}

async function getContributionCalendar() {
  if (token) {
    try {
      const graphData = await githubGraphql(`
        query ContributionCalendar($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    date
                  }
                }
              }
            }
          }
        }
      `, { login: user });

      const calendar = graphData.user?.contributionsCollection?.contributionCalendar;
      if (!calendar) throw new Error(`No contribution calendar returned for ${user}`);
      return {
        calendar,
        dataAccess: process.env.PROFILE_TOKEN ? 'profile-token' : 'repository-token-public-fallback',
      };
    } catch (error) {
      console.warn(`GitHub GraphQL failed; using the public contribution page: ${error.message}`);
    }
  }

  const url = `https://github.com/users/${encodeURIComponent(user)}/contributions`;
  const response = await fetch(url, { headers: { 'User-Agent': githubHeaders['User-Agent'] } });
  if (!response.ok) {
    throw new Error(`Public contribution page failed with ${response.status}: ${(await response.text()).slice(0, 300)}`);
  }

  const html = await response.text();
  const totalMatch = html.match(/([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year/i);
  const matches = [...html.matchAll(/data-date="(\d{4}-\d{2}-\d{2})"[^>]*>[\s\S]*?<tool-tip[^>]*>(No|[\d,]+) contributions? on/gi)];
  const contributionDays = matches.map((match) => ({
    date: match[1],
    contributionCount: match[2].toLowerCase() === 'no' ? 0 : Number(match[2].replaceAll(',', '')),
  }));

  if (!totalMatch || contributionDays.length < 365) {
    throw new Error('Could not parse the public GitHub contribution calendar');
  }

  return {
    calendar: {
      totalContributions: Number(totalMatch[1].replaceAll(',', '')),
      weeks: [{ contributionDays }],
    },
    dataAccess: 'public-html-fallback',
  };
}

async function getRepositories() {
  let endpoint = `https://api.github.com/users/${encodeURIComponent(user)}/repos?per_page=100&sort=updated`;

  if (process.env.PROFILE_TOKEN) {
    try {
      const viewer = await fetchJson('https://api.github.com/user', { headers: githubHeaders });
      if (viewer.login?.toLowerCase() === user.toLowerCase()) {
        endpoint = 'https://api.github.com/user/repos?affiliation=owner&per_page=100&sort=updated';
      }
    } catch (error) {
      console.warn(`Could not resolve token owner; using public repositories: ${error.message}`);
    }
  }

  const repositories = [];
  for (let page = 1; page <= 10; page += 1) {
    const separator = endpoint.includes('?') ? '&' : '?';
    const batch = await fetchJson(`${endpoint}${separator}page=${page}`, { headers: githubHeaders });
    if (!Array.isArray(batch)) {
      throw new Error('GitHub repositories response was not an array');
    }
    repositories.push(...batch);
    if (batch.length < 100) break;
  }

  return repositories;
}

async function renderPng(filename, width, height, chart) {
  const response = await fetch(quickChartUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      width,
      height,
      format: 'png',
      backgroundColor: 'transparent',
      chart,
    }),
  });

  if (!response.ok) {
    throw new Error(`QuickChart failed with ${response.status}: ${(await response.text()).slice(0, 300)}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (!contentType.startsWith('image/png')) {
    throw new Error(`QuickChart returned unexpected content type: ${contentType}`);
  }

  await fs.writeFile(path.join(assetsDir, filename), Buffer.from(await response.arrayBuffer()));
}

function calculateStreak(days) {
  const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date));
  let index = sorted.length - 1;

  // A zero contribution today should not erase an active streak from yesterday.
  if (sorted[index]?.contributionCount === 0) index -= 1;

  let streak = 0;
  while (index >= 0 && sorted[index].contributionCount > 0) {
    streak += 1;
    index -= 1;
  }
  return streak;
}

function xmlEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function contributionCard(stats) {
  const accessLabel = stats.dataAccess === 'profile-token' ? 'authenticated profile data' : 'public fallback data';
  const items = [
    ['Total contributions', stats.totalContributions.toLocaleString('en-US')],
    ['Active days', stats.activeDays.toLocaleString('en-US')],
    ['Best day', stats.bestDay.toLocaleString('en-US')],
    ['Current streak', `${stats.currentStreak} ${stats.currentStreak === 1 ? 'day' : 'days'}`],
  ];

  const metrics = items.map(([label, value], index) => {
    const x = 42 + index * 208;
    return `
      <g transform="translate(${x} 72)">
        <text class="value" x="0" y="0">${xmlEscape(value)}</text>
        <text class="label" x="0" y="30">${xmlEscape(label)}</text>
      </g>`;
  }).join('');

  return `<svg xmlns="http://www.w3.org/2000/svg" width="880" height="150" viewBox="0 0 880 150" role="img" aria-label="GitHub contribution overview for ${xmlEscape(user)}">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#0d1117"/>
        <stop offset="1" stop-color="#19102e"/>
      </linearGradient>
    </defs>
    <style>
      .title { fill: #c9d1d9; font: 600 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .value { fill: #a371f7; font: 700 25px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .label { fill: #8b949e; font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    </style>
    <rect width="879" height="149" x="0.5" y="0.5" rx="10" fill="url(#bg)" stroke="#30363d"/>
    <text class="title" x="42" y="34">GitHub contribution overview · ${xmlEscape(accessLabel)}</text>
    ${metrics}
  </svg>`.replace(/^[ \t]+$/gm, '');
}

async function main() {
  await fs.mkdir(assetsDir, { recursive: true });

  const [repositories, contributionResult] = await Promise.all([
    getRepositories(),
    getContributionCalendar(),
  ]);

  const { calendar, dataAccess } = contributionResult;

  const languageCounts = new Map();
  repositories
    .filter((repository) => !repository.fork && repository.language)
    .forEach((repository) => {
      languageCounts.set(repository.language, (languageCounts.get(repository.language) || 0) + 1);
    });

  const languages = [...languageCounts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 6);

  await renderPng('top-langs.png', 700, 400, {
    type: 'doughnut',
    data: {
      labels: languages.map(([language]) => language),
      datasets: [{
        data: languages.map(([, count]) => count),
        backgroundColor: ['#a371f7', '#58a6ff', '#3fb950', '#d29922', '#f778ba', '#ff7b72'],
        borderColor: '#0d1117',
      }],
    },
    options: {
      plugins: {
        title: { display: true, text: 'Primary language by repository', color: '#c9d1d9' },
        legend: { position: 'bottom', labels: { color: '#c9d1d9' } },
      },
    },
  });

  const days = calendar.weeks.flatMap((week) => week.contributionDays)
    .sort((a, b) => a.date.localeCompare(b.date));
  const recentDays = days.slice(-30);

  await renderPng('commits-30days.png', 900, 300, {
    type: 'line',
    data: {
      labels: recentDays.map((day) => day.date.slice(5)),
      datasets: [{
        label: 'Contributions',
        data: recentDays.map((day) => day.contributionCount),
        borderColor: '#a371f7',
        backgroundColor: '#a371f733',
        pointBackgroundColor: '#3fb950',
        tension: 0.3,
        fill: true,
      }],
    },
    options: {
      scales: {
        x: { ticks: { color: '#8b949e', maxTicksLimit: 10 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: '#8b949e', precision: 0 }, grid: { color: '#30363d' } },
      },
      plugins: {
        title: { display: true, text: 'Contributions in the last 30 days', color: '#c9d1d9' },
        legend: { display: false },
      },
    },
  });

  const stats = {
    username: user,
    totalContributions: calendar.totalContributions,
    activeDays: days.filter((day) => day.contributionCount > 0).length,
    bestDay: Math.max(0, ...days.map((day) => day.contributionCount)),
    currentStreak: calculateStreak(days),
    generatedAt: new Date().toISOString(),
    dataAccess,
  };

  await Promise.all([
    fs.writeFile(path.join(assetsDir, 'contribution-overview.svg'), contributionCard(stats)),
    fs.writeFile(path.join(assetsDir, 'contribution-stats.json'), `${JSON.stringify(stats, null, 2)}\n`),
  ]);

  console.log(`Generated profile charts for ${user} (${stats.totalContributions} contributions).`);
  if (dataAccess !== 'profile-token') {
    console.warn('PROFILE_TOKEN is not configured; private contributions may be absent.');
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
