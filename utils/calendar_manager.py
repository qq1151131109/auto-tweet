"""Content calendar management tool"""
import os
import json
from datetime import datetime
from typing import Dict, Optional
from .file_lock import file_lock
from .json_parser import parse_calendar_json


class CalendarManager:
    """Content calendar manager"""

    def __init__(self, calendar_dir: str = "calendars"):
        """
        Initialize calendar manager

        Args:
            calendar_dir: Calendar file storage directory
        """
        self.calendar_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            calendar_dir
        )

        # Ensure directory exists
        os.makedirs(self.calendar_dir, exist_ok=True)

    def get_calendar_path(self, persona_name: str, year_month: str) -> str:
        """
        Get calendar file path

        Args:
            persona_name: Persona name
            year_month: Year-month, format YYYY-MM

        Returns:
            Calendar file path
        """
        filename = f"{persona_name}_{year_month}.json"
        return os.path.join(self.calendar_dir, filename)

    def calendar_exists(self, persona_name: str, year_month: str) -> bool:
        """
        Check if calendar file exists

        Args:
            persona_name: Persona name
            year_month: Year-month, format YYYY-MM

        Returns:
            Whether it exists
        """
        path = self.get_calendar_path(persona_name, year_month)
        return os.path.exists(path)

    def load_calendar(self, persona_name: str, year_month: str) -> Optional[Dict]:
        """
        Load calendar file (with file lock protection)

        Args:
            persona_name: Persona name
            year_month: Year-month, format YYYY-MM

        Returns:
            Calendar data, returns None if doesn't exist
        """
        path = self.get_calendar_path(persona_name, year_month)

        if not os.path.exists(path):
            return None

        try:
            # Protect read operation with file lock
            with file_lock(path, timeout=5.0):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except TimeoutError:
            print(f"[CalendarManager] Calendar load timeout (file locked): {path}")
            return None
        except Exception as e:
            print(f"[CalendarManager] Failed to load calendar: {e}")
            return None

    def save_calendar(self, persona_name: str, year_month: str, calendar_data: Dict) -> bool:
        """
        Save calendar file (with file lock protection)

        Args:
            persona_name: Persona name
            year_month: Year-month, format YYYY-MM
            calendar_data: Calendar data

        Returns:
            Whether save succeeded
        """
        path = self.get_calendar_path(persona_name, year_month)

        try:
            # Protect write operation with file lock
            with file_lock(path, timeout=10.0):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(calendar_data, f, ensure_ascii=False, indent=2)
            return True
        except TimeoutError:
            print(f"[CalendarManager] Calendar save timeout (file locked): {path}")
            return False
        except Exception as e:
            print(f"[CalendarManager] Failed to save calendar: {e}")
            return False

    def get_today_plan(self, persona_name: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Get operation plan for specified date

        Args:
            persona_name: Persona name
            date: Date, format YYYY-MM-DD, defaults to today

        Returns:
            Daily operation plan, returns None if doesn't exist
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        year_month = date[:7]  # YYYY-MM

        calendar = self.load_calendar(persona_name, year_month)
        if calendar is None:
            return None

        return calendar.get("calendar", {}).get(date)

    def generate_calendar_prompt(self, persona: Dict, year_month: str, days_to_generate: int = 15, start_date: str = None) -> str:
        """
        Generate LLM prompt for calendar generation

        Args:
            persona: Persona data
            year_month: Year-month, format YYYY-MM
            days_to_generate: Number of days to generate, default 15
            start_date: Start date for generation (format YYYY-MM-DD). If None, starts from month beginning

        Returns:
            LLM prompt
        """
        data = persona["data"]
        name = data.get("name", "Unknown")

        # Extract persona information
        description = data.get("description", "")
        personality = data.get("personality", "")

        # ⭐ Extract content_strategy from persona (if available)
        twitter_persona = data.get("twitter_persona", {})
        content_strategy = twitter_persona.get("content_strategy", {})

        # Build content type list and distribution info from persona's strategy
        content_types_list = []
        content_distribution_text = ""

        if content_strategy:
            # Persona has custom content strategy - use it!
            total_percentage = 0
            for content_type, info in content_strategy.items():
                if isinstance(info, dict):
                    percentage_str = info.get("percentage", "0%")
                    description_str = info.get("description", "")
                    # Parse percentage
                    percentage = float(percentage_str.rstrip("%"))
                    total_percentage += percentage
                    content_types_list.append(content_type)
                    content_distribution_text += f"   - {percentage:.0f}% {content_type} ({description_str})\n"

            content_types_str = "/".join(content_types_list)
            content_distribution_guide = f"""8. **Content Type Distribution Requirements** (from persona's content_strategy):
{content_distribution_text}
   Total: {total_percentage:.0f}%

   ⭐ Use the exact content types defined above. These are persona-specific types that match {name}'s unique style."""

        else:
            # Fallback to generic content types if persona has no content_strategy
            content_types_list = ["lifestyle_mundane", "personal_emotion", "interaction_bait", "visual_showcase", "cta_conversion"]
            content_types_str = "/".join(content_types_list)
            content_distribution_guide = """8. **Content Type Distribution Requirements** (generic fallback):
   - 50% lifestyle_mundane (mundane life/daily chatter, like "weather so hot today", "what to eat for lunch")
   - 20% personal_emotion (emotional sharing, like tired/lonely/happy/nostalgic)
   - 20% interaction_bait (interaction prompts: poll/question/choice/mild controversy)
   - 8% visual_showcase (OOTD, selfie, talent showcase)
   - 2% cta_conversion (traffic conversion, max 1-2 times per week)"""

        # Get month and days
        year, month = year_month.split("-")

        # Calculate days in month
        import calendar
        _, days_in_month = calendar.monthrange(int(year), int(month))

        # Determine start day
        if start_date:
            # Use provided start date
            start_day = int(start_date.split("-")[2])
        else:
            # Default to month beginning
            start_day = 1

        # Calculate how many days can be generated from start_day
        remaining_days_in_month = days_in_month - start_day + 1
        actual_days = min(days_to_generate, remaining_days_in_month)

        # ⭐ Get holidays based on persona's country code (Issue #4 fix)
        import holidays

        # Read country code from persona
        core_info = data.get("core_info") or data.get("extensions", {}).get("core_info", {})
        location = core_info.get("location", {})
        country_code = location.get("country_code", "US")

        # Use corresponding country's holidays
        try:
            country_holidays = holidays.country_holidays(country_code, years=int(year))
        except Exception:
            # If country code invalid, fallback to US
            country_holidays = holidays.country_holidays("US", years=int(year))

        month_holidays = []
        for i in range(start_day, start_day + actual_days):
            date = f"{year_month}-{i:02d}"
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            if date_obj in country_holidays:
                holiday_name = country_holidays.get(date_obj)
                month_holidays.append(f"{date}: {holiday_name}")

        holidays_info = "\n".join(month_holidays) if month_holidays else "No special holidays"

        # Format year-month display
        year_month_display = f"{month}/{year}"

        # Calculate end date
        end_day = start_day + actual_days - 1

        prompt = f"""You are a professional social media operations expert planning {name}'s tweet calendar for {year_month_display}.

Persona Information:
- Name: {name}
- Description: {description}
- Personality: {personality}

Operation Goals:
- Diversified content that matches persona
- Maintain authenticity and consistency
- Encourage fan engagement

Special dates in this period:
{holidays_info}

Requirements:
1. Plan {actual_days} days from {year_month}-{start_day:02d} to {year_month}-{end_day:02d}
2. Design weekly rhythm (Monday to Sunday content types) based on persona traits
3. Special themes for special dates (holidays, anniversaries)
4. Diversify content types, avoid 3 consecutive days of same type
5. topic_type should match persona traits (use the exact content types defined below)
6. suggested_scene should be described in natural English paragraphs, concise and clear
7. **Important**: suggested_scene must be a solo scene, only describe this character's own activities, don't involve other people (like grandpa, friends, family, etc.)

{content_distribution_guide}

9. **New - Recommend posting time slot for each day**:
   - early_morning (06:00-08:30): suitable for waking up complaints, tired content
   - morning (08:30-11:30): suitable for daily work/study, sunshine sharing
   - midday (11:30-14:00): suitable for polls, chatter, choice questions
   - afternoon (14:00-18:00): suitable for focused work/study, talent showcase
   - evening_prime (18:00-22:00): suitable for OOTD, selfies, visual content
   - late_night (22:00-02:00): suitable for insomnia, loneliness, emotional, traffic conversion

10. **New - Strategic Flaw Assignment** (optional):
    Randomly assign a strategic flaw to 2-3 days per week in the plan:
    - sleep_deprived (insomnia/tired)
    - clumsy (clumsy/spilling things)
    - tech_inept (tech malfunction/WiFi down)
    - forgetful (forgetful)

11. **CRITICAL**: ALL text output fields (theme, content_direction, keywords, outfit_direction) MUST be in English. Do not use any Chinese characters.

12. **CRITICAL**: Each day MUST include an outfit_direction field following the guidelines above. Never repeat outfit_direction across days.

Output format (strict JSON, no other explanatory text):
{{
  "{year_month}-{start_day:02d}": {{
    "weekday": "Monday",
    "topic_type": "{content_types_list[0] if content_types_list else 'lifestyle_mundane'}",  // Must be one of: {content_types_str}
    "tweet_format": "standard",  // standard/thread/poll/grwm
    "recommended_time": "morning",  // Recommended time slot: early_morning/morning/midday/afternoon/evening_prime/late_night
    "mood": "energetic",  // Mood matching time slot
    "theme": "Morning routine",  // MUST BE IN ENGLISH
    "content_direction": "Share morning routine, light and cheerful",  // MUST BE IN ENGLISH
    "outfit_direction": "loose dark fabric slipping off one shoulder, collar visible, minimal bottoms, vulnerable intimate state",  // MUST BE IN ENGLISH, semantic description (NOT specific items)
    "keywords": ["morning", "routine", "sunshine"],  // MUST BE IN ENGLISH
    "suggested_scene": "morning routine, sunlight, energetic mood...",  // MUST BE IN ENGLISH
    "special_event": null,
    "strategic_flaw": null  // Optional: sleep_deprived/clumsy/tech_inept/forgetful
  }},
  "{year_month}-{end_day:02d}": {{
    "weekday": "...",
    "topic_type": "...",  // Must be one of: {content_types_str}
    "tweet_format": "...",
    "recommended_time": "...",
    "mood": "...",
    "theme": "...",  // MUST BE IN ENGLISH
    "content_direction": "...",  // MUST BE IN ENGLISH
    "outfit_direction": "...",  // MUST BE IN ENGLISH, use different variation from day 1
    "keywords": [...],  // MUST BE IN ENGLISH
    "suggested_scene": "...",  // MUST BE IN ENGLISH
    "special_event": null,
    "strategic_flaw": null
  }}
}}

Important reminders:
- topic_type must strictly use the types defined in requirement 8: {content_types_str}
- Content distribution should follow the percentages specified in requirement 8
- recommended_time should reasonably match content type (e.g., late_night suitable for emotional content)
- strategic_flaw randomly assign 2-3 times per week, don't have it every day
- Maintain style consistency, match persona's language habits and behavioral traits
- **ALL OUTPUT FIELDS (theme, content_direction, keywords) MUST BE IN ENGLISH, NO CHINESE CHARACTERS**

Please output JSON directly, don't include any ```json markers or other explanatory text.
"""

        return prompt

    def parse_calendar_response(self, response: str, persona_name: str, year_month: str) -> Dict:
        """
        Parse LLM returned calendar data

        Args:
            response: LLM response
            persona_name: Persona name
            year_month: Year-month

        Returns:
            Complete calendar data structure
        """
        # 使用统一的JSON解析工具
        calendar_dict = parse_calendar_json(response, persona_name, year_month)

        # Build complete data structure
        # Calculate content distribution
        topic_counts = {}
        for date_data in calendar_dict.values():
            topic_type = date_data.get("topic_type", "daily sharing")
            topic_counts[topic_type] = topic_counts.get(topic_type, 0) + 1

        total = len(calendar_dict)
        content_ratio = {
            topic: round(count / total * 100, 1)
            for topic, count in topic_counts.items()
        }

        calendar_data = {
            "persona_name": persona_name,
            "month": year_month,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "calendar": calendar_dict,
            "monthly_strategy": {
                "content_ratio": content_ratio,
                "total_days": total
            }
        }

        return calendar_data
