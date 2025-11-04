# 🗺️ Sitemap Generator - Quick Reference

## 🚀 Quick Commands

```bash
# Generate all SEO files (robots.txt + sitemaps)
npm run generate:seo

# Production with custom domain
npm run generate:seo -- --domain "https://mysite.com" --env production

# Python only (from backend/)
python generate_sitemap.py --domain "https://mysite.com" --config sitemap.config.json
```

## 📁 Generated Files

- ✅ `sitemap.xml` - Main sitemap index
- ✅ `sitemap-videos.xml` - Video sitemap with metadata
- ✅ `sitemap-categories.xml` - Categories from data.json
- ✅ `sitemap-main.xml` - Homepage and main pages
- ✅ `robots.txt` - SEO optimized robots file

## 🎯 Adult Content Features

- **Video metadata**: title, duration, thumbnails, views
- **Adult content flags**: `family_friendly="no"`
- **Content filtering**: min duration, views, exclude private
- **SEO optimization**: Google Video Search compatible

## 🔧 Configuration

Edit `sitemap.config.json`:
```json
{
  "domain": "https://yoursite.com",
  "adult_content": true,
  "content_filters": {
    "min_duration": 60,
    "min_views": 50
  }
}
```

## 📊 Your Current Stats

Last generation produced:
- **27MB** of video sitemap data
- **Thousands** of videos indexed
- **Multiple categories** organized
- **SEO optimized** for Google/Bing

## 🧪 Testing

```bash
# Preview before saving
python generate_sitemap.py --preview --type videos --limit 5

# Validate with Google Search Console
# https://search.google.com/search-console/sitemaps
```

Ready for maximum SEO! 🚀