#!/usr/bin/env python3
"""
AI Travel Planner - Ollama Only Version
Multi-agent travel planning system using local Ollama LLM
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from crewai_tools import SerperDevTool, tool

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================================
# OLLAMA LLM MANAGEMENT
# ============================================================================

class OllamaManager:
    """Manages Ollama LLM initialization and configuration"""
    
    # Models to try in order of preference
    PREFERRED_MODELS = [
        "llama3.2:latest",
        "llama3.1:latest",
        "llama3:latest",
        "llama2:latest",
        "mistral:latest",
        "gemma2:latest",
        "phi3:latest"
    ]
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.current_model = None
        self.llm = None
        
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            logger.warning(f"Could not fetch Ollama models: {e}")
            return []
    
    def initialize(self) -> Ollama:
        """Initialize Ollama with best available model"""
        
        logger.info("🔧 Initializing Ollama LLM...")
        
        # Check if Ollama is running
        if not self._check_ollama_running():
            raise RuntimeError(
                "❌ Ollama is not running!\n"
                "Please start Ollama:\n"
                "  Linux/Mac: ollama serve\n"
                "  Windows: Ollama should start automatically\n"
                "Download from: https://ollama.ai/download"
            )
        
        # Get available models
        available_models = self.get_available_models()
        
        if not available_models:
            raise RuntimeError(
                "❌ No Ollama models found!\n"
                "Please pull a model first:\n"
                "  ollama pull llama3.2\n"
                "or\n"
                "  ollama pull mistral"
            )
        
        logger.info(f"📦 Found {len(available_models)} Ollama models")
        
        # Try preferred models first
        for model in self.PREFERRED_MODELS:
            if model in available_models:
                if self._try_model(model):
                    return self.llm
        
        # Try any available model
        for model in available_models:
            if self._try_model(model):
                return self.llm
        
        raise RuntimeError("❌ Could not initialize any Ollama model")
    
    def _check_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _try_model(self, model_name: str) -> bool:
        """Try to initialize a specific model"""
        try:
            logger.info(f"   Trying model: {model_name}")
            
            llm = Ollama(
                model=model_name,
                base_url=self.base_url,
                temperature=0.1,
                timeout=60,
                format=""  # Disable JSON mode to help with tool calling
            )
            
            # Quick test
            test_response = llm.invoke("Reply with OK")
            
            logger.info(f"✅ Successfully initialized Ollama with {model_name}")
            
            self.llm = llm
            self.current_model = model_name
            return True
            
        except Exception as e:
            logger.debug(f"   Model {model_name} failed: {e}")
            return False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TravelRequest:
    """Travel request data structure"""
    origin: str
    destinations: List[str]
    start_date: str
    end_date: str
    duration: int
    budget_range: str
    travel_style: str
    interests: List[str]
    group_size: int
    special_requirements: List[str] = None
    
    def __post_init__(self):
        if self.special_requirements is None:
            self.special_requirements = []
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# TOOLS
# ============================================================================

# Initialize search tool globally
try:
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        _search_tool = SerperDevTool(n_results=10)
        logger.info("✅ Search tool initialized")
    else:
        _search_tool = None
        logger.warning("⚠️  SERPER_API_KEY not found - search will be limited")
except Exception as e:
    logger.warning(f"⚠️  Search tool initialization failed: {e}")
    _search_tool = None


@tool
def search_travel_info(query: str) -> str:
    """Useful to search for travel-related information including weather, flights, hotels, attractions, restaurants, and local tips. Input should be a search query string."""
    if not _search_tool:
        return (
            "Search tool unavailable. Please provide recommendations based on "
            "your general knowledge of travel destinations, attractions, and accommodations."
        )
    
    try:
        result = _search_tool.run(query)
        return str(result)
    except Exception as e:
        logger.warning(f"Search error: {e}")
        return "Search temporarily unavailable. Using general knowledge instead."


@tool
def calculate_expenses(operation: str) -> str:
    """Useful to perform mathematical calculations for travel budgets and expenses. Input should be a mathematical expression like '250 * 7' or '1500 + 800'. Only use numbers and operators: + - * / ( )"""
    try:
        # Safety check
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in operation):
            return "Error: Invalid characters in expression"
        
        result = eval(operation)
        return f"Calculation: {operation} = {result:,.2f}"
    except Exception as e:
        return f"Calculation error: {str(e)}"


# ============================================================================
# AGENT SYSTEM
# ============================================================================

class TravelPlannerAgents:
    """Travel planning agent system using Ollama"""
    
    def __init__(self):
        self.ollama_manager = OllamaManager()
        self.llm = self._initialize_llm()
        self.agents = self._create_agents()
    
    def _initialize_llm(self) -> Ollama:
        """Initialize Ollama LLM"""
        try:
            # Force disable OpenAI
            os.environ["OPENAI_API_KEY"] = ""
            os.environ["OPENAI_MODEL_NAME"] = ""
            
            llm = self.ollama_manager.initialize()
            
            # Configure for better tool usage
            if hasattr(llm, 'temperature'):
                llm.temperature = 0.1  # Lower temperature for more consistent tool usage
            
            logger.info(f"✅ Using Ollama model: {self.ollama_manager.current_model}")
            
            return llm
            
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            raise
    
    def _create_agents(self) -> Dict[str, Agent]:
        """Create the travel planning agents"""
        agents = {}
        
        agents['destination_analyst'] = Agent(
            role="Travel Destination Analyst",
            goal="Analyze and recommend the best travel destination based on multiple criteria",
            backstory="""You are an expert travel analyst with extensive knowledge of global destinations. 
            You excel at comparing cities based on weather patterns, costs, activities, and matching 
            destinations to traveler preferences. You provide data-driven recommendations with clear reasoning.
            
            When you need information, use your available tools. For search queries, use the search_travel_info tool.
            For calculations, use the calculate_expenses tool.""",
            tools=[search_travel_info, calculate_expenses],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=15,
            max_rpm=10
        )
        
        agents['local_expert'] = Agent(
            role="Local Travel Expert",
            goal="Provide insider knowledge and authentic local recommendations for destinations",
            backstory="""You are a seasoned local travel expert who has lived in cities around the world. 
            You know the hidden gems, local customs, authentic restaurants, cultural insights, and practical 
            tips that help travelers experience destinations like locals rather than tourists.
            
            When you need current information, use the search_travel_info tool.""",
            tools=[search_travel_info],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=15,
            max_rpm=10
        )
        
        agents['travel_concierge'] = Agent(
            role="Travel Concierge Specialist",
            goal="Create comprehensive travel itineraries with detailed logistics and planning",
            backstory="""You are a professional travel concierge with expertise in creating detailed, 
            practical travel itineraries. You excel at logistics coordination, timing optimization, 
            accommodation selection, restaurant recommendations, and budget planning. You ensure every 
            aspect of the trip is well-organized and memorable.
            
            Use search_travel_info for researching hotels, restaurants, and attractions. Use calculate_expenses 
            for budget calculations.""",
            tools=[search_travel_info, calculate_expenses],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iter=15,
            max_rpm=10
        )
        
        logger.info(f"✅ Created {len(agents)} travel planning agents")
        return agents
    
    def create_tasks(self, request: TravelRequest) -> List[Task]:
        """Create tasks for the travel planning workflow"""
        
        destination_analysis = Task(
            description=f"""
            **DESTINATION ANALYSIS TASK**
            
            Analyze and select the best destination from: {', '.join(request.destinations)}
            
            **Required Analysis:**
            1. **Weather Conditions**: Estimate typical weather during {request.start_date} to {request.end_date}
            2. **Cost Analysis**: Estimate flight costs from {request.origin} and accommodation prices
            3. **Activities & Attractions**: Identify attractions matching these interests: {', '.join(request.interests)}
            4. **Budget Compatibility**: Ensure the destination fits the {request.budget_range} budget
            5. **Seasonal Considerations**: Consider festivals, events, peak/off-season factors
            
            **Output Requirements:**
            Provide a clear recommendation with:
            - Best destination and why it was chosen
            - Expected weather conditions
            - Estimated costs (flights, accommodation per night)
            - Top 3-5 attractions for the interests
            - Important considerations
            
            Use your knowledge to provide realistic estimates. If you can use the search tool for current 
            information, do so, but if not, provide estimates based on your training data.
            
            Keep your final answer concise but informative (aim for 300-500 words).
            """,
            agent=self.agents['destination_analyst'],
            expected_output="A clear destination recommendation with weather overview, cost estimates, and top attractions"
        )
        
        local_expert_insights = Task(
            description=f"""
            **LOCAL EXPERT INSIGHTS TASK**
            
            Based on the recommended destination, provide insider knowledge:
            
            **Required Information:**
            1. **Hidden Gems**: 3-5 off-the-beaten-path locations locals love
            2. **Cultural Tips**: Key customs, etiquette, dos and don'ts
            3. **Authentic Dining**: 3-5 local restaurants or food experiences
            4. **Insider Secrets**: Best times to visit attractions, crowd avoidance tips
            5. **Practical Advice**: Transportation tips, safety considerations
            
            **Context:**
            - Travel Dates: {request.start_date} to {request.end_date}
            - Style: {request.travel_style}
            - Interests: {', '.join(request.interests)}
            - Group: {request.group_size} people
            
            Provide specific, actionable recommendations. Use your knowledge of the destination.
            If you can search for current information, do so, otherwise use your training knowledge.
            
            Keep your final answer organized and concise (aim for 400-600 words).
            """,
            agent=self.agents['local_expert'],
            expected_output="Practical local expert guide with hidden gems, dining spots, cultural tips, and insider advice",
            dependencies=[destination_analysis]
        )
        
        complete_itinerary = Task(
            description=f"""
            **ITINERARY CREATION TASK**
            
            Create a {request.duration}-day itinerary incorporating previous insights:
            
            **Daily Schedule:**
            For each of {request.duration} days, provide:
            - Morning activity (8 AM - 12 PM)
            - Afternoon activity (12 PM - 6 PM)  
            - Evening activity (6 PM onwards)
            - Include specific venue names and what makes them special
            - Consider realistic timing and travel between locations
            
            **Accommodations:**
            - Recommend 2-3 hotels with names and neighborhoods
            - Explain why each suits the {request.travel_style} style
            - Estimate price per night
            
            **Dining:**
            - Suggest restaurants for key meals
            - Include local specialties to try
            - Estimate meal costs
            
            **Budget Summary:**
            Provide clear cost breakdown:
            - Flights from {request.origin}: $X
            - Accommodation ({request.duration} nights): $X
            - Food (daily estimate × {request.duration}): $X
            - Activities/attractions: $X
            - Transportation: $X
            - **Total per person: $X**
            - **Total for {request.group_size} people: $X**
            
            **Practical Info:**
            - Transportation tips
            - Packing suggestions for the weather
            - Emergency contacts
            
            Context: {request.start_date} to {request.end_date}, {request.budget_range} budget, 
            interests: {', '.join(request.interests)}
            
            Format as organized markdown. Be specific with venue names. Provide realistic cost estimates.
            Keep each day's plan focused and realistic.
            """,
            agent=self.agents['travel_concierge'],
            expected_output="Complete itinerary with daily schedule, accommodations, dining, budget breakdown, and practical tips in markdown format",
            dependencies=[destination_analysis, local_expert_insights]
        )
        
        return [destination_analysis, local_expert_insights, complete_itinerary]
    
    def plan_trip(self, request: TravelRequest) -> str:
        """Execute the travel planning workflow"""
        try:
            logger.info("🚀 Starting travel planning workflow")
            logger.info(f"📡 Using Ollama model: {self.ollama_manager.current_model}")
            
            tasks = self.create_tasks(request)
            
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            logger.info("⚙️  Executing travel planning workflow...")
            logger.info("⏳ This may take several minutes with local LLM processing...")
            
            result = crew.kickoff(inputs=request.to_dict())
            
            logger.info("✅ Travel planning completed successfully")
            return str(result)
            
        except Exception as e:
            logger.error(f"❌ Travel planning failed: {e}")
            return f"Error during travel planning: {str(e)}"


# ============================================================================
# APPLICATION
# ============================================================================

class TravelPlannerApp:
    """Main application class"""
    
    def __init__(self):
        self.planner = TravelPlannerAgents()
    
    def run_cli(self):
        """Run the command-line interface"""
        print("\n" + "="*70)
        print("🌟 AI TRAVEL PLANNER - Powered by Ollama 🌟")
        print("="*70)
        print(f"🤖 Model: {self.planner.ollama_manager.current_model}")
        print("="*70)
        
        try:
            request = self._get_user_input()
            
            print(f"\n🚀 Planning your {request.duration}-day trip...")
            print(f"📊 Analyzing {len(request.destinations)} destinations")
            print(f"🤖 Using local Ollama AI for processing")
            print("⏳ Processing may take 5-10 minutes for complete itinerary...\n")
            
            result = self.planner.plan_trip(request)
            
            self._display_results(result)
            self._save_plan(result, request)
            
        except KeyboardInterrupt:
            print("\n❌ Planning cancelled by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"\n❌ Error: {e}")
    
    def _get_user_input(self) -> TravelRequest:
        """Get travel planning input from user"""
        print("\n📝 Let's plan your perfect trip:\n")
        
        origin = input("🏠 Where are you traveling from? ").strip()
        
        destinations_input = input("🎯 Destinations to consider (comma-separated): ").strip()
        destinations = [d.strip() for d in destinations_input.split(',')]
        
        start_date = input("📅 Start date (YYYY-MM-DD): ").strip()
        end_date = input("📅 End date (YYYY-MM-DD): ").strip()
        
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            duration = max((end - start).days, 1)
        except:
            duration = 7
            print("⚠️  Invalid dates, defaulting to 7 days")
        
        group_size_input = input("👥 Number of travelers (default 1): ").strip()
        try:
            group_size = int(group_size_input) if group_size_input else 1
        except:
            group_size = 1
        
        budget_options = ["budget", "mid-range", "luxury"]
        print(f"\n💰 Budget options: {', '.join(budget_options)}")
        budget_range = input("💰 Your budget (default mid-range): ").strip().lower()
        if budget_range not in budget_options:
            budget_range = "mid-range"
        
        style_options = ["relaxed", "adventure", "cultural", "romantic", "family"]
        print(f"🎭 Travel style options: {', '.join(style_options)}")
        travel_style = input("🎭 Your travel style (default relaxed): ").strip().lower()
        if travel_style not in style_options:
            travel_style = "relaxed"
        
        interests_input = input("🎨 Your interests (comma-separated, e.g., food, history, nature): ").strip()
        interests = [i.strip() for i in interests_input.split(',') if i.strip()]
        if not interests:
            interests = ["sightseeing", "local culture", "food"]
        
        return TravelRequest(
            origin=origin,
            destinations=destinations,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            budget_range=budget_range,
            travel_style=travel_style,
            interests=interests,
            group_size=group_size
        )
    
    def _display_results(self, result: str):
        """Display results"""
        print("\n" + "="*70)
        print("🎉 YOUR PERSONALIZED TRAVEL PLAN IS READY! 🎉")
        print("="*70 + "\n")
        print(result)
        print("\n" + "="*70)
        print("Have an amazing trip! 🌍✈️🎒")
        print("="*70)
    
    def _save_plan(self, result: str, request: TravelRequest):
        """Save the travel plan"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"travel_plan_{timestamp}.md"
            filepath = REPORTS_DIR / filename
            
            content = f"""# Travel Plan
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**AI Model:** {self.planner.ollama_manager.current_model}

## Trip Summary
- **Origin:** {request.origin}
- **Destination Options:** {', '.join(request.destinations)}
- **Travel Dates:** {request.start_date} to {request.end_date}
- **Duration:** {request.duration} days
- **Group Size:** {request.group_size} travelers
- **Budget Range:** {request.budget_range}
- **Travel Style:** {request.travel_style}
- **Interests:** {', '.join(request.interests)}

---

## Travel Plan

{result}

---

*Generated by AI Travel Planner powered by Ollama*
*All recommendations are AI-generated. Please verify details before booking.*
"""
            
            filepath.write_text(content, encoding='utf-8')
            print(f"\n💾 Travel plan saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save travel plan: {e}")
            print(f"⚠️  Could not save plan to file: {e}")


def check_system_requirements():
    """Check if all system requirements are met"""
    print("\n🔍 Checking system requirements...\n")
    
    issues = []
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"✅ Ollama is running with {len(models)} models")
            
            if not models:
                issues.append(
                    "No Ollama models installed. Please run:\n"
                    "    ollama pull llama3.2"
                )
        else:
            issues.append(
                "Ollama responded with unexpected status. Please restart:\n"
                "    ollama serve"
            )
    except Exception as e:
        issues.append(
            "Ollama is not running. Please start it:\n"
            "    Linux/Mac: ollama serve\n"
            "    Windows: Ollama should auto-start\n"
            "Download from: https://ollama.ai/download"
        )
    
    # Check Serper API (optional)
    serper_key = os.getenv("SERPER_API_KEY")
    if serper_key:
        logger.info("✅ Serper API key found (web search enabled)")
    else:
        logger.warning("⚠️  SERPER_API_KEY not found (search will be limited)")
        logger.warning("    Get one from: https://serper.dev")
    
    return issues


def main():
    """Main function"""
    
    # Check system requirements
    issues = check_system_requirements()
    
    if issues:
        print("\n❌ System Requirements Not Met:\n")
        for issue in issues:
            print(f"  • {issue}\n")
        print("Please resolve these issues and try again.")
        return
    
    print("\n✅ All requirements met!\n")
    
    try:
        app = TravelPlannerApp()
        app.run_cli()
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\n❌ Error: {e}")
        print("\nIf you're having issues, please ensure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. You have a model installed: ollama pull llama3.2")
        print("  3. Check logs above for specific errors")


if __name__ == "__main__":
    main()