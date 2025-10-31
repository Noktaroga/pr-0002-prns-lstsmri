import express from 'express';
import axios from 'axios';
import * as cheerio from 'cheerio';

const app = express();
const PORT = process.env.PORT || 4000;

app.use(express.json());

// Permitir CORS para desarrollo
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

app.post('/api/scrape-video-url', async (req, res) => {
  const { pageUrl } = req.body;
  if (!pageUrl) return res.status(400).json({ error: 'Missing pageUrl' });
  try {
    const { data: html } = await axios.get(pageUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
      }
    });
    const $ = cheerio.load(html);
    let videoUrl = null;
    $('script').each((i, el) => {
      const txt = $(el).html();
      if (txt) {
        const match = txt.match(/html5player\.setVideoUrlLow\('([^']+)'\)/);
        if (match) {
          videoUrl = match[1];
          return false;
        }
      }
    });
    if (videoUrl) {
      res.json({ videoUrl });
    } else {
      res.status(404).json({ error: 'No video url found' });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Scraper API running on port ${PORT}`);
});