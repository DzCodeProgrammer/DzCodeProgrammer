// generate-charts.js
// Node script: fetch some GitHub data and request quickchart images, save to assets/*.png
const https = require('https');
const fs = require('fs');

const user = process.env.GITHUB_USER || 'DzCodeProgrammer';
const quickchart = process.env.QT_API || 'https://quickchart.io/chart';

// helper: simple GET
function getJson(url) {
  return new Promise((res, rej) => {
    https.get(url, {headers: {'User-Agent':'Node'}} , r => {
      let data='';
      r.on('data', c=>data+=c);
      r.on('end', ()=> {
        try{ res(JSON.parse(data)); } catch(e){ rej(e) }
      });
    }).on('error', rej);
  });
}

// helper: download image from quickchart URL
function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, r => {
      r.pipe(file);
      file.on('finish', () => file.close(resolve));
    }).on('error', err => {
      fs.unlink(dest, ()=>reject(err));
    });
  });
}

(async () => {
  try {
    // 1) Get user's repos (public) to compute language breakdown (simple approach)
    const repos = await getJson(`https://api.github.com/users/${user}/repos?per_page=100`);
    const langCount = {};
    repos.forEach(r => {
      if (r.language) langCount[r.language] = (langCount[r.language]||0) + 1;
    });
    const langs = Object.keys(langCount).slice(0,6);
    const langValues = langs.map(l => langCount[l]);

    // QuickChart donut for languages
    const langChart = {
      type: 'doughnut',
      data: { labels: langs, datasets: [{ data: langValues }] },
      options: { plugins:{ legend:{ position:'bottom' } } }
    };
    const langUrl = `${quickchart}?w=700&h=400&c=${encodeURIComponent(JSON.stringify(langChart))}`;
    await download(langUrl, 'assets/top-langs.png');

    // 2) Commits per day for last 30 days (approx via events endpoint)
    const events = await getJson(`https://api.github.com/users/${user}/events?per_page=100`);
    // simple aggregation: count PushEvent created_at by date (UTC)
    const days = Array.from({length:30}, (_,i) => {
      const d = new Date(); d.setDate(d.getDate() - (29 - i));
      return d.toISOString().slice(0,10);
    });
    const commitsMap = {};
    events.forEach(ev => {
      if (ev.type === 'PushEvent') {
        const date = ev.created_at.slice(0,10);
        commitsMap[date] = (commitsMap[date]||0) + ev.payload.commits.length;
      }
    });
    const commitValues = days.map(d => commitsMap[d]||0);

    const commitsChart = {
      type:'line',
      data: {
        labels: days,
        datasets: [{ label:'Commits', data:commitValues, fill:false }]
      },
      options: { scales:{ x:{ display:false } }, plugins:{ legend:{ display:false } } }
    };
    const commitsUrl = `${quickchart}?w=900&h=300&c=${encodeURIComponent(JSON.stringify(commitsChart))}`;
    await download(commitsUrl, 'assets/commits-30days.png');

    console.log('Charts generated.');
  } catch (e) {
    console.error('Error generating charts', e);
    process.exit(1);
  }
})();
