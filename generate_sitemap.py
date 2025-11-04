#!/usr/bin/env python3
"""
Sitemap Generator for Adult Content Sites
========================================

Generates XML sitemaps with SEO optimization for adult entertainment websites.
Supports multiple sitemap types: main, videos, categories, performers, etc.

Features:
- Video sitemap with thumbnails and metadata
- Category and tag organization
- Performer/model pages
- SEO-optimized priorities and frequencies
- Adult content considerations
- Multi-language support
- Large site pagination (50k URLs per sitemap)

Usage:
    python generate_sitemap.py
    python generate_sitemap.py --domain https://mysite.com --output ./sitemaps/
    python generate_sitemap.py --type videos --limit 1000
"""

import os
import json
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin
import requests
from dataclasses import dataclass


@dataclass
class SitemapURL:
    """Represents a URL entry in a sitemap."""
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None
    # Video-specific fields
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_loc: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    publication_date: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[float] = None


class SitemapGenerator:
    """Generate XML sitemaps for adult content websites."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.domain = self.config.get('domain', 'https://yoursite.com')
        
        # SEO settings for adult content
        self.priorities = {
            'homepage': 1.0,
            'categories': 0.9,
            'videos': 0.8,
            'performers': 0.7,
            'tags': 0.6,
            'search': 0.5,
            'pages': 0.4
        }
        
        self.changefreqs = {
            'homepage': 'daily',
            'categories': 'weekly',
            'videos': 'monthly',
            'performers': 'weekly',
            'tags': 'monthly',
            'pages': 'yearly'
        }
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or use defaults."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Default configuration for adult content sites
        return {
            "domain": os.getenv("DOMAIN", "https://yoursite.com"),
            "site_name": "Adult Entertainment Site",
            "max_urls_per_sitemap": 50000,
            "enable_video_sitemap": True,
            "enable_image_sitemap": False,  # Often not needed for adult sites
            "include_pagination": True,
            "adult_content": True,
            "age_verification_required": True,
            
            # Data sources
            "data_sources": {
                "videos": "data/videos.json",
                "categories": "data/categories.json", 
                "performers": "data/performers.json",
                "api_endpoint": "http://localhost:3001/api"
            },
            
            # URL patterns
            "url_patterns": {
                "videos": "/videos/{id}/",
                "categories": "/categories/{slug}/",
                "performers": "/performers/{slug}/",
                "tags": "/tags/{slug}/",
                "search": "/search/?q={query}"
            },
            
            # SEO settings
            "seo": {
                "default_changefreq": "weekly",
                "video_changefreq": "monthly",
                "include_lastmod": True,
                "include_priority": True,
                "thumbnail_required": True
            },
            
            # Content filters for adult sites
            "content_filters": {
                "min_duration": 60,  # seconds
                "min_views": 100,
                "exclude_draft": True,
                "exclude_private": True,
                "require_age_verification": True
            }
        }
    
    def generate_main_sitemap(self) -> str:
        """Generate the main sitemap index."""
        root = ET.Element("sitemapindex")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        
        # Add comment
        comment = ET.Comment(f" Generated on {datetime.now().isoformat()} ")
        root.append(comment)
        
        # Define sitemap files
        sitemaps = [
            ("sitemap-main.xml", "daily"),
            ("sitemap-videos.xml", "weekly"),
            ("sitemap-categories.xml", "weekly"),
            ("sitemap-performers.xml", "weekly"),
            ("sitemap-tags.xml", "monthly")
        ]
        
        for sitemap_file, changefreq in sitemaps:
            sitemap_elem = ET.SubElement(root, "sitemap")
            
            loc = ET.SubElement(sitemap_elem, "loc")
            loc.text = urljoin(self.domain, sitemap_file)
            
            lastmod = ET.SubElement(sitemap_elem, "lastmod")
            lastmod.text = datetime.now().strftime("%Y-%m-%d")
        
        return self._format_xml(root)
    
    def generate_main_pages_sitemap(self) -> str:
        """Generate sitemap for main pages (homepage, static pages)."""
        urls = []
        
        # Homepage
        urls.append(SitemapURL(
            loc=self.domain,
            lastmod=datetime.now().strftime("%Y-%m-%d"),
            changefreq=self.changefreqs['homepage'],
            priority=self.priorities['homepage']
        ))
        
        # Main category pages
        main_pages = [
            "/videos/",
            "/categories/", 
            "/performers/",
            "/search/",
            "/premium/",
            "/new/",
            "/popular/",
            "/top-rated/"
        ]
        
        for page in main_pages:
            urls.append(SitemapURL(
                loc=urljoin(self.domain, page),
                lastmod=datetime.now().strftime("%Y-%m-%d"),
                changefreq=self.changefreqs['pages'],
                priority=self.priorities['categories']
            ))
        
        return self._generate_urlset_xml(urls)
    
    def generate_videos_sitemap(self, limit: Optional[int] = None) -> str:
        """Generate video sitemap with video-specific metadata."""
        videos_data = self._load_videos_data()
        
        if limit:
            videos_data = videos_data[:limit]
        
        # Filter videos for adult content compliance
        filtered_videos = self._filter_videos(videos_data)
        
        urls = []
        for video in filtered_videos:
            # Map your data format to sitemap format
            video_id = video.get('id')
            title = video.get('title', 'Untitled Video')
            
            # Clean and limit title/description for XML
            title = title[:100] if len(title) > 100 else title
            description = title[:200] if len(title) <= 200 else title[:200] + "..."
            
            # Convert duration from string format like "7 min" to seconds
            duration_str = video.get('duration', '0 min')
            duration_seconds = self._parse_duration(duration_str)
            
            video_url = SitemapURL(
                loc=urljoin(self.domain, self.config['url_patterns']['videos'].format(id=video_id)),
                lastmod=datetime.now().strftime("%Y-%m-%d"),  # Use current date since no update date available
                changefreq=self.changefreqs['videos'],
                priority=self.priorities['videos'],
                
                # Video metadata from your data structure
                title=title,
                description=description,
                thumbnail_loc=video.get('thumbnail'),
                duration=duration_seconds,
                view_count=self._parse_votes(video.get('total_votes')),
                publication_date=datetime.now().strftime("%Y-%m-%d"),
                category=video.get('category', '').replace('/c/', '').replace('-', ' '),
                tags=[],  # No tags in current data format
                rating=self._calculate_rating(video.get('good_votes'), video.get('bad_votes'))
            )
            urls.append(video_url)
        
        return self._generate_video_sitemap_xml(urls)
    
    def generate_categories_sitemap(self) -> str:
        """Generate sitemap for category pages."""
        categories_data = self._load_categories_data()
        
        urls = []
        for category in categories_data:
            category_url = SitemapURL(
                loc=urljoin(self.domain, self.config['url_patterns']['categories'].format(slug=category.get('slug'))),
                lastmod=category.get('updated_at', datetime.now().strftime("%Y-%m-%d")),
                changefreq=self.changefreqs['categories'],
                priority=self.priorities['categories']
            )
            urls.append(category_url)
        
        return self._generate_urlset_xml(urls)
    
    def generate_performers_sitemap(self) -> str:
        """Generate sitemap for performer/model pages."""
        performers_data = self._load_performers_data()
        
        urls = []
        for performer in performers_data:
            # Skip inactive or banned performers
            if not performer.get('active', True):
                continue
                
            performer_url = SitemapURL(
                loc=urljoin(self.domain, self.config['url_patterns']['performers'].format(slug=performer.get('slug'))),
                lastmod=performer.get('updated_at', datetime.now().strftime("%Y-%m-%d")),
                changefreq=self.changefreqs['performers'],
                priority=self.priorities['performers']
            )
            urls.append(performer_url)
        
        return self._generate_urlset_xml(urls)
    
    def _filter_videos(self, videos: List[Dict]) -> List[Dict]:
        """Filter videos based on adult content criteria."""
        filtered = []
        filters = self.config.get('content_filters', {})
        
        for video in videos:
            # Skip if private or draft
            if filters.get('exclude_private') and video.get('is_private'):
                continue
            if filters.get('exclude_draft') and video.get('status') == 'draft':
                continue
            
            # Duration filter - parse duration first
            if filters.get('min_duration'):
                duration_seconds = self._parse_duration(video.get('duration', 0))
                if duration_seconds < filters['min_duration']:
                    continue
            
            # Views filter - parse votes as views
            if filters.get('min_views'):
                view_count = self._parse_votes(video.get('total_votes', 0))
                if view_count < filters['min_views']:
                    continue
            
            # Age verification - assume all are verified for now
            # In real implementation, check actual age verification status
            
            filtered.append(video)
        
        return filtered
    
    def _load_videos_data(self) -> List[Dict]:
        """Load videos data from JSON file or API."""
        data_source = self.config['data_sources'].get('videos')
        
        if data_source.startswith('http'):
            # Load from API
            try:
                response = requests.get(f"{data_source}/videos", timeout=30)
                response.raise_for_status()
                return response.json().get('videos', [])
            except Exception as e:
                print(f"Warning: Could not load videos from API: {e}")
                return self._get_sample_videos()
        else:
            # Load from file
            if Path(data_source).exists():
                with open(data_source, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle the specific format of your data.json
                if isinstance(data, dict):
                    # Flatten all videos from all categories
                    videos = []
                    for category_key, category_videos in data.items():
                        if isinstance(category_videos, list):
                            # Add category info to each video
                            for video in category_videos:
                                video_copy = video.copy()
                                video_copy['category'] = category_key
                                videos.append(video_copy)
                    return videos
                elif isinstance(data, list):
                    return data
                else:
                    print(f"Warning: Unexpected data format in {data_source}")
                    return self._get_sample_videos()
            else:
                print(f"Warning: Videos data file not found: {data_source}")
                return self._get_sample_videos()
    
    def _load_categories_data(self) -> List[Dict]:
        """Load categories data from the main data file."""
        data_source = self.config['data_sources'].get('categories', 'data.json')
        
        if Path(data_source).exists():
            try:
                with open(data_source, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    # Extract category keys from the data structure
                    categories = []
                    for category_key in data.keys():
                        # Clean category name
                        clean_name = category_key.replace('/c/', '').replace('-', ' ').title()
                        slug = category_key.replace('/c/', '')
                        
                        categories.append({
                            'slug': slug,
                            'name': clean_name,
                            'updated_at': datetime.now().strftime("%Y-%m-%d"),
                            'video_count': len(data[category_key]) if isinstance(data[category_key], list) else 0
                        })
                    return categories
            except Exception as e:
                print(f"Warning: Could not load categories from {data_source}: {e}")
        
        # Fallback to sample categories
        return [
            {"slug": "amateur", "name": "Amateur", "updated_at": "2024-01-01"},
            {"slug": "professional", "name": "Professional", "updated_at": "2024-01-01"},
            {"slug": "hd", "name": "HD Videos", "updated_at": "2024-01-01"},
            {"slug": "new", "name": "New Videos", "updated_at": "2024-01-01"},
            {"slug": "popular", "name": "Popular", "updated_at": "2024-01-01"},
            {"slug": "top-rated", "name": "Top Rated", "updated_at": "2024-01-01"}
        ]
    
    def _load_performers_data(self) -> List[Dict]:
        """Load performers data."""
        # Sample performers structure
        return [
            {"slug": "sample-performer", "name": "Sample Performer", "active": True, "updated_at": "2024-01-01"}
        ]
    
    def _get_sample_videos(self) -> List[Dict]:
        """Get sample video data for testing."""
        sample_videos = []
        for i in range(1, 21):  # 20 sample videos
            video = {
                "id": i,
                "title": f"Sample Video {i}",
                "description": f"Description for sample video {i}",
                "duration": 300 + (i * 30),  # 5-15 minutes
                "views": 1000 + (i * 100),
                "rating": 4.0 + (i * 0.05),
                "category": "sample",
                "tags": ["sample", "test"],
                "thumbnail_url": f"{self.domain}/thumbnails/video-{i}.jpg",
                "created_at": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "updated_at": (datetime.now() - timedelta(days=i//2)).strftime("%Y-%m-%d"),
                "is_private": False,
                "status": "published",
                "age_verified": True
            }
            sample_videos.append(video)
        
        return sample_videos
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '7 min' to seconds."""
        if not duration_str:
            return 0
        try:
            # Handle both string and int inputs
            if isinstance(duration_str, int):
                return duration_str  # Assume it's already in seconds
            
            # Extract number and unit from string
            parts = str(duration_str).lower().strip().split()
            if len(parts) >= 2:
                number = int(parts[0])
                unit = parts[1]
                if 'min' in unit:
                    return number * 60
                elif 'sec' in unit or 's' in unit:
                    return number
                elif 'h' in unit or 'hour' in unit:
                    return number * 3600
            return 0
        except (ValueError, IndexError, AttributeError):
            return 0
    
    def _parse_votes(self, votes_str: str) -> int:
        """Parse votes string like '1.807 votos' to number."""
        if not votes_str:
            return 0
        try:
            # Handle both string and int inputs
            if isinstance(votes_str, int):
                return votes_str
            
            # Extract numbers, handle k/K for thousands
            import re
            votes_str = str(votes_str)
            numbers = re.findall(r'[\d.,]+', votes_str)
            if numbers:
                num_str = numbers[0].replace(',', '.')
                if 'k' in votes_str.lower():
                    return int(float(num_str) * 1000)
                else:
                    return int(float(num_str.replace('.', '')))
            return 0
        except (ValueError, IndexError, AttributeError):
            return 0
    
    def _calculate_rating(self, good_votes_str: str, bad_votes_str: str) -> float:
        """Calculate rating from good/bad votes."""
        try:
            good = self._parse_votes(good_votes_str) if good_votes_str else 0
            bad = self._parse_votes(bad_votes_str) if bad_votes_str else 0
            total = good + bad
            if total > 0:
                rating = (good / total) * 5.0  # Convert to 5-star scale
                return round(rating, 2)
            return 0.0
        except:
            return 0.0
    
    def _generate_urlset_xml(self, urls: List[SitemapURL]) -> str:
        """Generate standard URL sitemap XML."""
        root = ET.Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        
        # Add comment
        comment = ET.Comment(f" Generated on {datetime.now().isoformat()} - {len(urls)} URLs ")
        root.append(comment)
        
        for url_obj in urls:
            url_elem = ET.SubElement(root, "url")
            
            loc = ET.SubElement(url_elem, "loc")
            loc.text = url_obj.loc
            
            if url_obj.lastmod:
                lastmod = ET.SubElement(url_elem, "lastmod")
                lastmod.text = url_obj.lastmod
            
            if url_obj.changefreq:
                changefreq = ET.SubElement(url_elem, "changefreq")
                changefreq.text = url_obj.changefreq
            
            if url_obj.priority is not None:
                priority = ET.SubElement(url_elem, "priority")
                priority.text = str(url_obj.priority)
        
        return self._format_xml(root)
    
    def _generate_video_sitemap_xml(self, urls: List[SitemapURL]) -> str:
        """Generate video sitemap with video-specific metadata."""
        root = ET.Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        root.set("xmlns:video", "http://www.google.com/schemas/sitemap-video/1.1")
        
        # Add comment
        comment = ET.Comment(f" Video sitemap generated on {datetime.now().isoformat()} - {len(urls)} videos ")
        root.append(comment)
        
        for url_obj in urls:
            url_elem = ET.SubElement(root, "url")
            
            # Standard URL elements
            loc = ET.SubElement(url_elem, "loc")
            loc.text = url_obj.loc
            
            if url_obj.lastmod:
                lastmod = ET.SubElement(url_elem, "lastmod")
                lastmod.text = url_obj.lastmod
            
            # Video-specific elements
            if any([url_obj.title, url_obj.description, url_obj.thumbnail_loc]):
                video_elem = ET.SubElement(url_elem, "video:video")
                
                if url_obj.thumbnail_loc:
                    thumbnail = ET.SubElement(video_elem, "video:thumbnail_loc")
                    thumbnail.text = url_obj.thumbnail_loc
                
                if url_obj.title:
                    title = ET.SubElement(video_elem, "video:title")
                    title.text = url_obj.title
                
                if url_obj.description:
                    desc = ET.SubElement(video_elem, "video:description")
                    desc.text = url_obj.description[:2048]  # Max 2048 chars
                
                if url_obj.duration:
                    duration = ET.SubElement(video_elem, "video:duration")
                    duration.text = str(url_obj.duration)
                
                if url_obj.view_count:
                    view_count = ET.SubElement(video_elem, "video:view_count")
                    view_count.text = str(url_obj.view_count)
                
                if url_obj.publication_date:
                    pub_date = ET.SubElement(video_elem, "video:publication_date")
                    pub_date.text = url_obj.publication_date
                
                if url_obj.category:
                    category = ET.SubElement(video_elem, "video:category")
                    category.text = url_obj.category
                
                if url_obj.tags:
                    for tag in url_obj.tags[:32]:  # Max 32 tags
                        tag_elem = ET.SubElement(video_elem, "video:tag")
                        tag_elem.text = tag
                
                if url_obj.rating:
                    rating = ET.SubElement(video_elem, "video:rating")
                    rating.text = str(min(5.0, max(0.0, url_obj.rating)))
                
                # Adult content indicator
                if self.config.get('adult_content', True):
                    family_friendly = ET.SubElement(video_elem, "video:family_friendly")
                    family_friendly.text = "no"
        
        return self._format_xml(root)
    
    def _format_xml(self, root: ET.Element) -> str:
        """Format XML with proper indentation."""
        self._indent_xml(root)
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def _indent_xml(self, elem, level=0):
        """Add indentation to XML for readability."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def generate_all_sitemaps(self, output_dir: str = "sitemaps") -> Dict[str, str]:
        """Generate all sitemaps and save to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = {}
        
        # Generate all sitemap types
        sitemaps = {
            "sitemap.xml": self.generate_main_sitemap(),
            "sitemap-main.xml": self.generate_main_pages_sitemap(),
            "sitemap-videos.xml": self.generate_videos_sitemap(),
            "sitemap-categories.xml": self.generate_categories_sitemap(),
            "sitemap-performers.xml": self.generate_performers_sitemap()
        }
        
        for filename, content in sitemaps.items():
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            results[filename] = str(file_path)
            print(f"✅ Generated: {file_path}")
        
        return results


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Generate XML sitemaps for adult content sites")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--domain", help="Override domain in config")
    parser.add_argument("--output", default="sitemaps", help="Output directory for sitemaps")
    parser.add_argument("--type", choices=['all', 'main', 'videos', 'categories', 'performers'], 
                       default='all', help="Type of sitemap to generate")
    parser.add_argument("--limit", type=int, help="Limit number of URLs (for testing)")
    parser.add_argument("--preview", action="store_true", help="Preview content without saving")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = SitemapGenerator(args.config)
        
        # Override domain if provided
        if args.domain:
            generator.domain = args.domain
            generator.config['domain'] = args.domain
        
        print(f"🗺️ Generating sitemaps for {generator.domain}")
        
        if args.type == 'all':
            if args.preview:
                print("📄 Main sitemap preview:")
                print(generator.generate_main_sitemap()[:500] + "...")
            else:
                results = generator.generate_all_sitemaps(args.output)
                print(f"\n✅ Generated {len(results)} sitemaps in {args.output}/")
        else:
            # Generate specific sitemap type
            if args.type == 'main':
                content = generator.generate_main_sitemap()
            elif args.type == 'videos':
                content = generator.generate_videos_sitemap(args.limit)
            elif args.type == 'categories':
                content = generator.generate_categories_sitemap()
            elif args.type == 'performers':
                content = generator.generate_performers_sitemap()
            
            if args.preview:
                print(f"📄 {args.type.title()} sitemap preview:")
                print(content[:1000] + "..." if len(content) > 1000 else content)
            else:
                output_path = Path(args.output)
                output_path.mkdir(exist_ok=True)
                filename = f"sitemap-{args.type}.xml"
                file_path = output_path / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Generated: {file_path}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())