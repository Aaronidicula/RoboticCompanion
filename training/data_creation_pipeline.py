import json
import pandas as pd
import random
import re
from typing import List, Dict, Tuple
import os
from datetime import datetime
import csv

class TrainingDataGenerator:
    """Generate comprehensive training data for household assistant"""
    
    def __init__(self):
        self.conversations = []
        
    def create_cleaning_data(self) -> List[Dict]:
        """Generate cleaning-related conversations"""
        
        cleaning_data = [
            # Kitchen cleaning
            {
                "user": "How do I clean burnt food from a pan?",
                "assistant": "For burnt pans: 1) Fill with water and add 2 tbsp baking soda. 2) Bring to a boil and simmer 15 minutes. 3) Let cool, then scrub with a non-abrasive sponge. 4) For stubborn residue, make a paste with baking soda and water, let sit overnight. 5) For stainless steel, use white vinegar instead of baking soda."
            },
            {
                "user": "What's the best way to clean windows without streaks?",
                "assistant": "For streak-free windows: 1) Use distilled water mixed with white vinegar (1:1 ratio). 2) Clean on cloudy days to prevent quick drying. 3) Use a squeegee in overlapping strokes from top to bottom. 4) Dry edges with lint-free cloth. 5) For outside windows, rinse with hose first to remove dirt."
            },
            {
                "user": "How often should I deep clean my house?",
                "assistant": "Deep cleaning schedule: **Monthly**: baseboards, light fixtures, inside appliances. **Quarterly**: windows, ceiling fans, under furniture, carpets. **Bi-annually**: inside cabinets, closet organization, mattress cleaning. **Annually**: deep carpet cleaning, wall washing, garage/basement. Create a rotating schedule so you're not overwhelmed doing everything at once."
            },
            
            # Bathroom cleaning
            {
                "user": "How do I remove soap scum from shower doors?",
                "assistant": "Remove soap scum effectively: 1) Mix equal parts white vinegar and dish soap in spray bottle. 2) Spray generously and let sit 30 minutes. 3) Scrub with soft brush or sponge. 4) Rinse thoroughly with hot water. 5) For prevention, squeegee after each shower and apply car wax monthly for easier cleaning."
            },
            {
                "user": "What's the best way to clean toilet stains?",
                "assistant": "For toilet bowl stains: 1) Pour 1 cup white vinegar around rim and let sit 1 hour. 2) Sprinkle baking soda and scrub with toilet brush. 3) For hard water rings, use pumice stone (wet first). 4) For tough stains, use borax overnight. 5) Clean weekly to prevent buildup. Always use toilet-specific cleaners and good ventilation."
            }
        ]
        
        return cleaning_data
    
    def create_organization_data(self) -> List[Dict]:
        """Generate organization and decluttering conversations"""
        
        organization_data = [
            {
                "user": "Help me organize my bedroom closet",
                "assistant": "Let's organize your closet step by step: 1) **Empty completely** - remove everything to assess space. 2) **Sort by category** - group shirts, pants, dresses, shoes. 3) **Declutter** - donate items unworn for 12+ months. 4) **Install organizers** - shelf dividers, hanging organizers, shoe racks. 5) **Arrange strategically** - daily items at eye level, seasonal items higher. 6) **Maintain** - spend 5 minutes weekly keeping it organized."
            },
            {
                "user": "How do I organize paperwork and bills?",
                "assistant": "Create an efficient paper management system: 1) **Categories**: Action needed, to file, to shred. 2) **Filing system**: Use hanging folders by category (taxes, insurance, utilities). 3) **Digital copies**: Scan important documents and store securely. 4) **Bill organization**: Use accordion folder with monthly sections or go paperless. 5) **Shred safely**: Old statements, receipts over 7 years. 6) **Review monthly** to prevent buildup."
            },
            {
                "user": "What's the best way to organize kitchen cabinets?",
                "assistant": "Organize kitchen cabinets for maximum efficiency: 1) **Group by function** - baking supplies together, cooking oils near stove. 2) **Use vertical space** - shelf risers, door organizers. 3) **Clear containers** - for cereals, snacks, baking ingredients. 4) **Heavy items low** - pots, appliances in lower cabinets. 5) **Label everything** - especially in pantry areas. 6) **Purge regularly** - check expiration dates monthly."
            }
        ]
        
        return organization_data
    
    def create_cooking_data(self) -> List[Dict]:
        """Generate cooking and meal planning conversations"""
        
        cooking_data = [
            {
                "user": "Help me plan meals for a busy week",
                "assistant": "Here's a strategy for busy week meal planning: **Sunday prep**: Cook rice/quinoa in bulk, chop vegetables, marinate proteins. **Quick meals**: Stir-fries, sheet pan dinners, slow cooker meals. **15-minute options**: Pasta with pre-made sauce, quesadillas, salad with protein. **Batch cooking**: Make double portions for leftovers. **Emergency meals**: Keep frozen vegetables, canned beans, pasta on hand. Plan 4-5 meals and repeat favorites."
            },
            {
                "user": "What are some healthy snack ideas I can prep ahead?",
                "assistant": "Healthy make-ahead snacks: **Protein-rich**: Hard-boiled eggs, Greek yogurt parfaits, hummus with veggies. **Energy bites**: Oats, peanut butter, honey, chia seeds rolled into balls. **Fruits**: Apple slices with almond butter, berries in portioned containers. **Vegetables**: Cut carrots, bell peppers, cucumbers with various dips. **Nuts/seeds**: Portioned trail mix, roasted chickpeas. Prep on Sunday for the entire week."
            },
            {
                "user": "How do I properly store leftovers?",
                "assistant": "Safe leftover storage guidelines: **Cool quickly** - refrigerate within 2 hours of cooking. **Proper containers** - airtight, food-safe materials. **Label with date** - use within 3-4 days. **Portion control** - store in meal-sized containers. **Freezer storage** - up to 3 months for most foods. **Reheating** - to 165°F internal temperature. **Never refreeze** previously frozen and thawed foods."
            }
        ]
        
        return cooking_data
    
    def create_maintenance_data(self) -> List[Dict]:
        """Generate home maintenance conversations"""
        
        maintenance_data = [
            {
                "user": "When should I change my air filter?",
                "assistant": "Air filter replacement schedule: **Basic filters**: Every 30-60 days. **Pleated filters**: Every 90 days. **High-efficiency filters**: Every 6-12 months. **Factors affecting frequency**: Pets (+monthly), allergies (+monthly), dusty environment (+monthly). **Check monthly**: Hold to light - if you can't see through it, replace it. Mark calendar reminders and buy filters in bulk to save money."
            },
            {
                "user": "How do I prevent clogged drains?",
                "assistant": "Prevent drain clogs with these habits: **Kitchen**: Never pour grease down drain, use strainer for food particles, run cold water when using disposal. **Bathroom**: Use hair catchers, avoid flushing non-toilet items, clean monthly with baking soda and vinegar. **All drains**: Hot water flush weekly, enzyme cleaners monthly. **Professional cleaning**: Annually for main lines. Prevention is much cheaper than repairs!"
            },
            {
                "user": "What tools should every homeowner have?",
                "assistant": "Essential homeowner toolkit: **Basic tools**: Hammer, screwdriver set (Phillips and flathead), adjustable wrench, pliers, level, measuring tape. **Power tools**: Cordless drill, circular saw (for projects). **Safety**: Work gloves, safety glasses, first aid kit. **Supplies**: Screws/nails variety pack, duct tape, electrical tape, wall anchors. **Seasonal**: Caulk gun, weatherstripping. Store in labeled toolbox with inventory list."
            }
        ]
        
        return maintenance_data
    
    def create_variations(self, base_conversations: List[Dict]) -> List[Dict]:
        """Create variations of existing conversations for data augmentation"""
        
        variations = []
        
        # Different ways to ask the same question
        question_variants = {
            "How do I": ["What's the best way to", "Can you help me", "I need help with", "What should I do to"],
            "What's the best": ["How do I best", "What's the most effective way to", "How should I"],
            "Help me": ["I need assistance with", "Can you guide me through", "Show me how to"]
        }
        
        for conv in base_conversations:
            original_user = conv["user"]
            
            # Create 2-3 variations per conversation
            for i in range(2):
                new_user = original_user
                
                # Replace question starters
                for original, replacements in question_variants.items():
                    if original in new_user:
                        new_user = new_user.replace(original, random.choice(replacements))
                        break
                
                # Add variation if it's different
                if new_user != original_user:
                    variations.append({
                        "user": new_user,
                        "assistant": conv["assistant"]
                    })
        
        return variations
    
    def create_conversational_data(self) -> List[Dict]:
        """Create more conversational, contextual exchanges"""
        
        conversational_data = [
            {
                "user": "I'm overwhelmed with household chores. Where do I start?",
                "assistant": "I understand feeling overwhelmed! Let's break this down into manageable steps: 1) **Start small** - pick one room or one type of task. 2) **15-minute rule** - set a timer and work for just 15 minutes. 3) **Priority list** - health/safety first (clean dishes, trash), then comfort items. 4) **One task at a time** - don't try to do everything at once. 5) **Celebrate progress** - acknowledge what you accomplish. What area of your home bothers you most right now?"
            },
            {
                "user": "My kitchen always looks messy even after I clean it",
                "assistant": "This is a common challenge! The issue might be organization rather than cleaning: 1) **Clear counters** - designate homes for appliances and only keep daily-use items out. 2) **Clean as you cook** - wash items immediately after use. 3) **10-minute pickup** - quick tidy every evening after dinner. 4) **Storage solutions** - drawer organizers, cabinet door hooks. 5) **Daily habits** - make bed, do dishes, wipe counters. What specific areas stay messy in your kitchen?"
            },
            {
                "user": "I want to be more eco-friendly with my cleaning products",
                "assistant": "Great goal! Here are eco-friendly cleaning alternatives: **All-purpose cleaner**: White vinegar + water (1:1 ratio). **Scrubbing paste**: Baking soda + water. **Glass cleaner**: Vinegar + water + drop of dish soap. **Disinfectant**: Hydrogen peroxide or rubbing alcohol. **Air freshener**: Essential oils in water. **Benefits**: Safer for family, pets, environment, and often cheaper. **Tip**: Reuse spray bottles and label clearly. Start with one recipe and expand gradually."
            }
        ]
        
        return conversational_data
    
    def save_training_data(self, filename: str = None):
        """Save all generated data to files"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_data_{timestamp}"
        
        # Collect all data
        all_data = []
        all_data.extend(self.create_cleaning_data())
        all_data.extend(self.create_organization_data())
        all_data.extend(self.create_cooking_data())
        all_data.extend(self.create_maintenance_data())
        all_data.extend(self.create_conversational_data())
        
        # Add variations
        variations = self.create_variations(all_data)
        all_data.extend(variations)
        
        # Shuffle data
        random.shuffle(all_data)
        
        # Save as JSON
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        # Save as CSV for easy viewing/editing
        df = pd.DataFrame(all_data)
        df.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
        
        # Save as text format for manual review
        with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
            for i, conv in enumerate(all_data, 1):
                f.write(f"--- Conversation {i} ---\n")
                f.write(f"User: {conv['user']}\n")
                f.write(f"Assistant: {conv['assistant']}\n\n")
        
        print(f"✅ Saved {len(all_data)} conversations to:")
        print(f"   📄 {filename}.json (for training)")
        print(f"   📊 {filename}.csv (for spreadsheet editing)")
        print(f"   📝 {filename}.txt (for manual review)")
        
        return all_data
    
    def load_existing_data(self, filename: str) -> List[Dict]:
        """Load existing training data"""
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    return json.load(f)
                elif filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                    return df.to_dict('records')
        except FileNotFoundError:
            print(f"File {filename} not found.")
            return []
    
    def validate_data(self, conversations: List[Dict]) -> Dict:
        """Validate training data quality"""
        
        stats = {
            "total_conversations": len(conversations),
            "avg_user_length": 0,
            "avg_assistant_length": 0,
            "empty_responses": 0,
            "very_short_responses": 0,
            "very_long_responses": 0
        }
        
        user_lengths = []
        assistant_lengths = []
        
        for conv in conversations:
            user_len = len(conv["user"])
            assistant_len = len(conv["assistant"])
            
            user_lengths.append(user_len)
            assistant_lengths.append(assistant_len)
            
            if not conv["assistant"].strip():
                stats["empty_responses"] += 1
            elif assistant_len < 50:
                stats["very_short_responses"] += 1
            elif assistant_len > 1000:
                stats["very_long_responses"] += 1
        
        stats["avg_user_length"] = sum(user_lengths) / len(user_lengths)
        stats["avg_assistant_length"] = sum(assistant_lengths) / len(assistant_lengths)
        
        # Print validation report
        print("📊 Data Validation Report:")
        print(f"   Total conversations: {stats['total_conversations']}")
        print(f"   Average user message length: {stats['avg_user_length']:.1f} chars")
        print(f"   Average assistant response length: {stats['avg_assistant_length']:.1f} chars")
        print(f"   Empty responses: {stats['empty_responses']}")
        print(f"   Very short responses (<50 chars): {stats['very_short_responses']}")
        print(f"   Very long responses (>1000 chars): {stats['very_long_responses']}")
        
        return stats

def main():
    """Generate comprehensive training data"""
    
    print("🏠 Household Assistant Training Data Generator")
    print("=" * 50)
    
    generator = TrainingDataGenerator()
    
    # Generate and save data
    conversations = generator.save_training_data()
    
    # Validate data quality
    stats = generator.validate_data(conversations)
    
    print("\n🎯 Next Steps:")
    print("1. Review the generated .txt file to check quality")
    print("2. Edit the .csv file to add more conversations")
    print("3. Use the .json file for training your model")
    print("4. Consider adding domain-specific conversations")
    
    print(f"\n💡 Tips for expanding your dataset:")
    print("- Add real conversations from family/friends")
    print("- Include error handling scenarios")
    print("- Add seasonal content (holiday cleaning, etc.)")
    print("- Include regional variations (metric vs imperial)")

if __name__ == "__main__":
    main()
