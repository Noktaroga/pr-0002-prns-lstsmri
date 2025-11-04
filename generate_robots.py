#!/usr/bin/env python3
"""
Robots.txt Generator for Adult Content Sites
============================================

Generates robots.txt files with appropriate restrictions for adult content sites.
Includes environment-specific rules and SEO optimization.

Usage:
    python generate_robots.py
    python generate_robots.py --env production --domain https://mysite.com
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class RobotsGenerator:
    """Generate robots.txt files with custom configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or use defaults."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "domain": os.getenv("DOMAIN", "https://yoursite.com"),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "seo": {
                "allowGoogleBot": True,
                "allowBingBot": True,
                "allowYandexBot": False,  # Privacy consideration for adult content
                "allowOtherBots": False,
                "includeSitemap": True,
                "crawlDelay": 1
            },
            "paths": {
                "allow": [
                    "/",
                    "/videos/",
                    "/categories/",
                    "/search/",
                    "/tags/",
                    "/performers/"
                ],
                "disallow": [
                    "/admin/",
                    "/api/",
                    "/private/",
                    "/user/",
                    "/auth/",
                    "/payment/",
                    "/temp/",
                    "/cache/",
                    "/backend/",
                    "*.json",
                    "*.xml",
                    "*.log",
                    "/preview/",
                    "/draft/"
                ]
            },
            "customRules": [
                {
                    "userAgent": "Googlebot",
                    "allow": ["/videos/", "/categories/", "/search/"],
                    "disallow": ["/user/", "/private/", "/admin/"],
                    "crawlDelay": 1
                },
                {
                    "userAgent": "Bingbot",
                    "allow": ["/videos/", "/categories/"],
                    "disallow": ["/user/", "/private/", "/admin/", "/search/"],
                    "crawlDelay": 2
                }
            ],
            "comments": {
                "header": "Adult content site - Age verification required",
                "footer": "For questions about this robots.txt, contact: webmaster@yoursite.com"
            }
        }
    
    def generate_content(self) -> str:
        """Generate robots.txt content based on configuration."""
        content = []
        
        # Add header
        content.append(f"# Robots.txt for {self.config['domain']}")
        content.append(f"# Generated on: {datetime.now().isoformat()}")
        content.append(f"# Environment: {self.config['environment']}")
        
        if "header" in self.config.get("comments", {}):
            content.append(f"# {self.config['comments']['header']}")
        
        content.append("")
        
        # Handle development/staging environments
        if self.config["environment"] in ["development", "staging"]:
            content.extend([
                "# Development/Staging - Block all crawlers",
                "User-agent: *",
                "Disallow: /",
                ""
            ])
            return "\n".join(content)
        
        # Production rules
        seo_config = self.config["seo"]
        
        # Google Bot rules
        if seo_config.get("allowGoogleBot", False):
            content.append("# Google Bot - Primary search engine")
            content.append("User-agent: Googlebot")
            
            google_rules = next(
                (rule for rule in self.config.get("customRules", []) 
                 if rule["userAgent"] == "Googlebot"), 
                None
            )
            
            if google_rules:
                self._add_bot_rules(content, google_rules)
            else:
                self._add_default_rules(content)
            
            content.append("")
        
        # Bing Bot rules
        if seo_config.get("allowBingBot", False):
            content.append("# Bing Bot - Secondary search engine")
            content.append("User-agent: Bingbot")
            
            bing_rules = next(
                (rule for rule in self.config.get("customRules", []) 
                 if rule["userAgent"] == "Bingbot"), 
                None
            )
            
            if bing_rules:
                self._add_bot_rules(content, bing_rules)
            else:
                self._add_default_rules(content)
            
            content.append("")
        
        # Yandex Bot rules (usually blocked for adult content)
        if seo_config.get("allowYandexBot", False):
            content.append("# Yandex Bot")
            content.append("User-agent: YandexBot")
            self._add_default_rules(content)
            content.append("")
        
        # Block all other bots if not allowed
        if not seo_config.get("allowOtherBots", False):
            content.extend([
                "# Block all other bots and crawlers",
                "User-agent: *",
                "Disallow: /",
                ""
            ])
        
        # Add sitemap references
        if seo_config.get("includeSitemap", False):
            content.extend([
                "# Sitemaps",
                f"Sitemap: {self.config['domain']}/sitemap.xml",
                f"Sitemap: {self.config['domain']}/sitemap-videos.xml",
                f"Sitemap: {self.config['domain']}/sitemap-categories.xml"
            ])
        
        # Add footer comment
        if "footer" in self.config.get("comments", {}):
            content.extend([
                "",
                f"# {self.config['comments']['footer']}"
            ])
        
        return "\n".join(content)
    
    def _add_bot_rules(self, content: List[str], rules: Dict):
        """Add custom rules for a specific bot."""
        for path in rules.get("allow", []):
            content.append(f"Allow: {path}")
        
        for path in rules.get("disallow", []):
            content.append(f"Disallow: {path}")
        
        if "crawlDelay" in rules:
            content.append(f"Crawl-delay: {rules['crawlDelay']}")
    
    def _add_default_rules(self, content: List[str]):
        """Add default allow/disallow rules."""
        paths = self.config.get("paths", {})
        
        for path in paths.get("allow", []):
            content.append(f"Allow: {path}")
        
        for path in paths.get("disallow", []):
            content.append(f"Disallow: {path}")
        
        crawl_delay = self.config["seo"].get("crawlDelay")
        if crawl_delay:
            content.append(f"Crawl-delay: {crawl_delay}")
    
    def generate_file(self, output_path: str = None) -> str:
        """Generate robots.txt file."""
        if output_path is None:
            # Default to parent directory's public folder (for frontend)
            current_dir = Path(__file__).parent
            output_path = current_dir.parent / "frontend" / "public" / "robots.txt"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.generate_content()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output_path)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Generate robots.txt for adult content sites")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--output", help="Output path for robots.txt")
    parser.add_argument("--domain", help="Override domain in config")
    parser.add_argument("--env", help="Override environment (development, staging, production)")
    parser.add_argument("--preview", action="store_true", help="Preview content without saving")
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = RobotsGenerator(args.config)
        
        # Override config with CLI arguments
        if args.domain:
            generator.config["domain"] = args.domain
        if args.env:
            generator.config["environment"] = args.env
        
        # Generate content
        if args.preview:
            print("📄 Robots.txt Preview:")
            print("=" * 50)
            print(generator.generate_content())
            print("=" * 50)
        else:
            output_path = generator.generate_file(args.output)
            print(f"✅ robots.txt generated successfully!")
            print(f"📁 Location: {output_path}")
            print(f"🌐 Domain: {generator.config['domain']}")
            print(f"🔧 Environment: {generator.config['environment']}")
            
            # Show preview
            print(f"\n📄 Content Preview:")
            print("-" * 30)
            content_lines = generator.generate_content().split('\n')
            for line in content_lines[:15]:
                print(line)
            if len(content_lines) > 15:
                print("...")
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())