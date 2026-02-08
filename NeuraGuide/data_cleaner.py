#!/usr/bin/env python3
"""
Data Cleaner and Merger for AI Tools Database
Cleans, deduplicates, and merges data from multiple sources
"""

import csv
import json
import re
from collections import defaultdict
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIToolsDataCleaner:
    def __init__(self):
        self.tools_data = []
        self.seen_names = set()
        self.seen_domains = set()
        
    def normalize_text(self, text):
        """Normalize text for comparison"""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def are_similar_tools(self, tool1, tool2):
        """Check if two tools are similar"""
        name1_norm = self.normalize_text(tool1["Tool Name"])
        name2_norm = self.normalize_text(tool2["Tool Name"])
        
        # Exact name match
        if name1_norm == name2_norm:
            return True
        
        # Check if one name contains the other
        if name1_norm in name2_norm or name2_norm in name1_norm:
            return True
        
        # Check domain similarity
        domain1 = self.extract_domain(tool1.get("Website", ""))
        domain2 = self.extract_domain(tool2.get("Website", ""))
        
        if domain1 and domain2 and domain1 == domain2:
            return True
        
        return False
    
    def merge_tools(self, tools):
        """Merge similar tools"""
        if not tools:
            return None
        
        # Use the tool with the most complete data as base
        best_tool = max(tools, key=lambda t: sum(1 for v in t.values() if v and v != "Unknown"))
        
        # Merge data from other tools
        for tool in tools:
            if tool == best_tool:
                continue
                
            for field, value in tool.items():
                if not best_tool.get(field) or best_tool[field] == "Unknown":
                    best_tool[field] = value
                elif field == "Description" and len(value) > len(best_tool[field]):
                    best_tool[field] = value
                elif field == "Key Features" and value != "See website":
                    if best_tool[field] == "See website":
                        best_tool[field] = value
                    else:
                        best_tool[field] = f"{best_tool[field]}, {value}"
        
        return best_tool
    
    def load_data_from_files(self):
        """Load data from multiple CSV files"""
        files = [
            "ai_tools_database.csv",
            "comprehensive_ai_tools.csv", 
            "advanced_ai_tools.csv"
        ]
        
        total_loaded = 0
        
        for filename in files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Validate required fields
                        if not row.get("Tool Name"):
                            continue
                        
                        self.tools_data.append(row)
                        total_loaded += 1
                
                logger.info(f"Loaded {total_loaded} tools from {filename}")
                
            except FileNotFoundError:
                logger.warning(f"File {filename} not found")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        logger.info(f"Total tools loaded: {len(self.tools_data)}")
    
    def clean_data(self):
        """Clean and standardize data"""
        logger.info("Cleaning data...")
        
        cleaned_tools = []
        
        for tool in self.tools_data:
            cleaned_tool = {}
            
            # Clean and standardize each field
            for field, value in tool.items():
                if field == "Tool Name":
                    cleaned_tool[field] = value.strip().title() if value else ""
                elif field == "Website":
                    cleaned_tool[field] = value.strip() if value and value.startswith('http') else ""
                elif field == "Description":
                    cleaned_tool[field] = value.strip() if value else ""
                elif field == "Category":
                    cleaned_tool[field] = value.strip().title() if value else "General"
                elif field == "Primary Function":
                    cleaned_tool[field] = value.strip().title() if value else cleaned_tool.get("Category", "General")
                elif field == "Pricing Model":
                    pricing = value.strip().lower() if value else "unknown"
                    if "free" in pricing and "trial" in pricing:
                        cleaned_tool[field] = "Freemium"
                    elif "free" in pricing:
                        cleaned_tool[field] = "Free"
                    elif "subscription" in pricing or "monthly" in pricing:
                        cleaned_tool[field] = "Subscription"
                    elif "pay" in pricing:
                        cleaned_tool[field] = "Pay-per-use"
                    else:
                        cleaned_tool[field] = value.title() if value else "Unknown"
                elif field == "Launch Year":
                    # Extract year from string
                    year_match = re.search(r'\b(20\d{2})\b', str(value))
                    cleaned_tool[field] = year_match.group(1) if year_match else "Unknown"
                else:
                    cleaned_tool[field] = value.strip() if value else "Unknown"
            
            # Validate tool has minimum required data
            if cleaned_tool.get("Tool Name") and cleaned_tool.get("Tool Name") != "":
                cleaned_tools.append(cleaned_tool)
        
        self.tools_data = cleaned_tools
        logger.info(f"Cleaned data: {len(self.tools_data)} tools remaining")
    
    def deduplicate_data(self):
        """Remove duplicate tools"""
        logger.info("Deduplicating data...")
        
        # Group similar tools
        tool_groups = []
        processed_indices = set()
        
        for i, tool1 in enumerate(self.tools_data):
            if i in processed_indices:
                continue
                
            similar_tools = [tool1]
            processed_indices.add(i)
            
            for j, tool2 in enumerate(self.tools_data[i+1:], i+1):
                if j in processed_indices:
                    continue
                    
                if self.are_similar_tools(tool1, tool2):
                    similar_tools.append(tool2)
                    processed_indices.add(j)
            
            tool_groups.append(similar_tools)
        
        # Merge each group
        merged_tools = []
        for group in tool_groups:
            merged_tool = self.merge_tools(group)
            if merged_tool:
                merged_tools.append(merged_tool)
        
        self.tools_data = merged_tools
        logger.info(f"After deduplication: {len(self.tools_data)} unique tools")
    
    def categorize_uncategorized_tools(self):
        """Categorize tools that are marked as General"""
        logger.info("Categorizing uncategorized tools...")
        
        categories = {
            "Image Generation": ["image", "art", "design", "visual", "photo", "drawing", "midjourney", "dall-e", "stable diffusion", "canva"],
            "Text Generation": ["text", "writing", "content", "copy", "article", "blog", "chatgpt", "claude", "jasper", "writer"],
            "Code Assistant": ["code", "programming", "developer", "github", "copilot", "coding", "python", "javascript"],
            "Video Generation": ["video", "animation", "movie", "film", "motion", "youtube", "tiktok"],
            "Audio Generation": ["audio", "music", "sound", "voice", "speech", "podcast", "spotify"],
            "Productivity": ["productivity", "automation", "workflow", "task", "management", "notion", "trello"],
            "Marketing": ["marketing", "seo", "advertising", "social media", "email", "campaign"],
            "Data Analysis": ["data", "analytics", "analysis", "insights", "dashboard", "tableau", "power bi"],
            "Research": ["research", "academic", "paper", "study", "scholar", "science"],
            "Translation": ["translation", "language", "translate", "multilingual", "google translate"],
            "Customer Service": ["customer", "support", "chatbot", "help desk", "zendesk"],
            "Education": ["education", "learning", "teaching", "course", "tutorial", "coursera"],
            "Health": ["health", "medical", "healthcare", "fitness", "wellness", "hospital"],
            "Finance": ["finance", "financial", "trading", "investment", "budget", "quickbooks"]
        }
        
        categorized_count = 0
        
        for tool in self.tools_data:
            if tool.get("Category") == "General" or tool.get("Primary Function") == "General":
                text = (tool.get("Tool Name", "") + " " + tool.get("Description", "")).lower()
                
                for category, keywords in categories.items():
                    if any(keyword in text for keyword in keywords):
                        tool["Category"] = category
                        tool["Primary Function"] = category
                        categorized_count += 1
                        break
        
        logger.info(f"Recategorized {categorized_count} tools")
    
    def enhance_data(self):
        """Enhance data with additional information"""
        logger.info("Enhancing data...")
        
        for tool in self.tools_data:
            # Add key features based on category
            if tool.get("Key Features") == "See website" or not tool.get("Key Features"):
                category = tool.get("Category", "").lower()
                
                features_map = {
                    "image generation": "AI-powered image creation, Style transfer, High-resolution output",
                    "text generation": "Natural language processing, Content creation, Multiple languages",
                    "code assistant": "Code completion, Syntax highlighting, Multiple programming languages",
                    "video generation": "AI video creation, Template library, Export options",
                    "audio generation": "Music generation, Voice synthesis, Audio editing",
                    "productivity": "Task automation, Workflow optimization, Integration capabilities",
                    "marketing": "Campaign optimization, Analytics, A/B testing",
                    "data analysis": "Data visualization, Predictive analytics, Reporting"
                }
                
                for cat, features in features_map.items():
                    if cat in category:
                        tool["Key Features"] = features
                        break
            
            # Improve target users based on category
            if tool.get("Target Users") == "General":
                category = tool.get("Category", "").lower()
                
                if "code" in category or "developer" in category:
                    tool["Target Users"] = "Developers"
                elif "business" in category or "marketing" in category:
                    tool["Target Users"] = "Business Professionals"
                elif "education" in category:
                    tool["Target Users"] = "Educators and Students"
                elif "health" in category:
                    tool["Target Users"] = "Healthcare Professionals"
                elif "finance" in category:
                    tool["Target Users"] = "Financial Professionals"
    
    def save_cleaned_data(self, filename="final_ai_tools_database.csv"):
        """Save cleaned data to CSV"""
        fieldnames = ["Tool Name", "Category", "Primary Function", "Description", "Website", 
                     "Pricing Model", "Key Features", "Target Users", "Launch Year", "Company"]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.tools_data)
        
        logger.info(f"Saved {len(self.tools_data)} cleaned tools to {filename}")
    
    def generate_statistics(self):
        """Generate statistics about the cleaned dataset"""
        stats = {
            "total_tools": len(self.tools_data),
            "categories": defaultdict(int),
            "pricing_models": defaultdict(int),
            "target_users": defaultdict(int),
            "launch_years": defaultdict(int)
        }
        
        for tool in self.tools_data:
            stats["categories"][tool.get("Category", "Unknown")] += 1
            stats["pricing_models"][tool.get("Pricing Model", "Unknown")] += 1
            stats["target_users"][tool.get("Target Users", "Unknown")] += 1
            
            year = tool.get("Launch Year", "Unknown")
            if year != "Unknown":
                stats["launch_years"][year] += 1
        
        logger.info("Dataset Statistics:")
        logger.info(f"Total Tools: {stats['total_tools']}")
        logger.info("Top Categories:")
        for cat, count in sorted(stats["categories"].items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {cat}: {count}")
        
        logger.info("Pricing Models:")
        for model, count in sorted(stats["pricing_models"].items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {model}: {count}")
        
        return stats
    
    def run_cleaning_process(self):
        """Run the complete data cleaning process"""
        logger.info("Starting data cleaning process...")
        
        # Load data from all sources
        self.load_data_from_files()
        
        # Clean and standardize data
        self.clean_data()
        
        # Remove duplicates
        self.deduplicate_data()
        
        # Categorize uncategorized tools
        self.categorize_uncategorized_tools()
        
        # Enhance data
        self.enhance_data()
        
        # Generate statistics
        stats = self.generate_statistics()
        
        # Save cleaned data
        self.save_cleaned_data()
        
        return len(self.tools_data), stats

if __name__ == "__main__":
    cleaner = AIToolsDataCleaner()
    total_tools, stats = cleaner.run_cleaning_process()
    print(f"Data cleaning completed! Final database contains {total_tools} unique AI tools")
