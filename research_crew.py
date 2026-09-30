import os
import sys
import datetime
import re
from dotenv import load_dotenv
import litellm
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool, BaseTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from langchain_community.tools import DuckDuckGoSearchRun, TavilySearchResults

# Load environment variables (GROQ_API_KEY)
load_dotenv()

# Fix Windows terminal encoding for emojis/special characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# --- ADAPTIVE BRAIN: RESILIENT FAILOVER ENGINE ---
def get_resilient_llm(tier="strategy", primary_index=0, **kwargs):
    """
    Factory function that returns a standard LLM instance 
    with an injected failover loop in its call method.
    """
    hierarchy = STRATEGY_MODELS if tier == "strategy" else RESEARCH_MODELS
    config = hierarchy[primary_index % len(hierarchy)]
    
    # Initialize the base LLM
    llm = LLM(
        model=config["model"],
        base_url=config.get("api_base"),
        api_key=config.get("api_key") or os.getenv(f"{config['model'].split('/')[0].upper()}_API_KEY"),
        **kwargs
    )

    # Store state on the object
    llm._resilience_tier = tier
    llm._resilience_index = primary_index
    llm._hierarchy = hierarchy
    
    # Store the original method
    _original_call = llm.call

    class CleanResponseProxy:
        """A proxy object that satisfies CrewAI validators while stringifying as clean text."""
        def __init__(self, original_response):
            self.original = original_response
            self.choices = getattr(original_response, 'choices', [])
            self.usage = getattr(original_response, 'usage', None)
            self.id = getattr(original_response, 'id', None)
            self.model = getattr(original_response, 'model', None)
        
        def __str__(self):
            # Surgical extraction of text content if it exists
            try:
                content = self.original.choices[0].message.content
                if content is not None:
                    return str(content)
            except (AttributeError, IndexError):
                pass
            # Fallback to the original's string representation for tool calls/etc.
            return str(self.original)
        
        def __repr__(self):
            return self.__str__()

    def resilient_call(messages, **call_kwargs):
        """Stateless failover with sanitized parameters and clean proxy returns."""
        current_idx = llm._resilience_index
        last_error = None
        
        # List of standard LiteLLM/OpenAI parameters to allow
        ALLOWED_PARAMS = [
            "temperature", "max_tokens", "top_p", "n", "stream", 
            "stop", "presence_penalty", "frequency_penalty", 
            "logit_bias", "user", "response_format", "seed", 
            "tools", "tool_choice"
        ]
        sanitized_kwargs = {k: v for k, v in call_kwargs.items() if k in ALLOWED_PARAMS}

        for i in range(len(llm._hierarchy)):
            try:
                config = llm._hierarchy[(current_idx + i) % len(llm._hierarchy)]
                model = config["model"]
                api_base = config.get("api_base")
                api_key = config.get("api_key") or os.getenv(f"{model.split('/')[0].upper()}_API_KEY")
                
                print(f"## [Adaptive Brain] {model} Attempt...")
                
                # Perform the call directly via LiteLLM to ensure statelessness
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    api_base=api_base,
                    api_key=api_key,
                    **sanitized_kwargs
                )
                
                # RETURN THE PROXY to satisfy validators but stringify cleanly
                return CleanResponseProxy(response)
            
            except Exception as e:
                last_error = e
                err_msg = str(e).lower()
                if any(x in err_msg for x in ["rate_limit", "429", "503", "too many requests", "not found", "404", "timeout"]):
                    print(f"## [FAILOVER] {model} issue: {err_msg[:80]}... Switching.")
                    continue
                else:
                    raise e
        raise last_error

    # Patch the method
    llm.call = resilient_call
    return llm

# Specialized Hierarchies for Failover
RESEARCH_MODELS = [
    {"model": "groq/llama-3.1-8b-instant"},
    {"model": "mistral/mistral-small-latest"}
]

STRATEGY_MODELS = [
    {"model": "groq/llama-3.3-70b-versatile"},
    {"model": "mistral/mistral-large-latest"},
    {"model": "ollama/gpt-oss:120b", "api_base": os.getenv("OLLAMA_API_BASE"), "api_key": os.getenv("OLLAMA_API_KEY")}
]

# Initialize the Multi-LLM Swarm
research_llm  = get_resilient_llm(tier="research", primary_index=0) # Primary: Groq 8B
health_llm    = get_resilient_llm(tier="strategy", primary_index=1) # Primary: Mistral Large
insight_llm   = get_resilient_llm(tier="strategy", primary_index=0) # Primary: Groq 70B
rx_llm        = get_resilient_llm(tier="strategy", primary_index=2) # Primary: Ollama Cloud (gpt-oss)
financial_llm = get_resilient_llm(tier="strategy", primary_index=0) # Primary: Groq 70B (high-IQ fiscal modeling)

# Initialize the Search Tools
# Primary: Google Search (High-fidelity)
if os.getenv("SERPER_API_KEY"):
    search_tool = SerperDevTool()
    search_tool.name = "google_search"
    search_tool.description = "PRIMARY search tool. Use this first for high-fidelity technical data and medical breakthroughs."
else:
    print("WARNING: SERPER_API_KEY not found. Fallback enabled.")
    search_tool = None

# Primary: Tavily for agent-optimized search (Requires TAVILY_API_KEY)
class TavilySearch(BaseTool):
    name: str = "ai_research_search"
    description: str = "PRIMARY agent-optimized search. Use this for clean, synthesized research snippets."

    def _run(self, query: str) -> str:
        return TavilySearchResults().run(query)

if os.getenv("TAVILY_API_KEY"):
    tavily_tool = TavilySearch()
else:
    print("WARNING: TAVILY_API_KEY not found. Fallback enabled.")
    tavily_tool = None

# Drill-down: Scraper
scrape_tool = ScrapeWebsiteTool()
scrape_tool.name = "deep_website_scraper"

class DuckDuckGoSearch(BaseTool):
    name: str = "fallback_search"
    description: str = "Secondary fallback search. ONLY use this if google_search and ai_research_search fail to return clinical results."

    def _run(self, topic: str) -> str:
        return DuckDuckGoSearchRun().run(topic)

ddg_search = DuckDuckGoSearch()

# Create a final list of tools for the researcher
researcher_tools = [scrape_tool, ddg_search]
if search_tool:
    researcher_tools.append(search_tool)
if tavily_tool:
    researcher_tools.append(tavily_tool)

# Final primary search fallback
if not search_tool:
    search_tool = ddg_search

# --- THE OPTUM STRATEGIC CORE ---

class OptumStrategicCrew:
    def __init__(self, topic: str):
        self.topic = topic

    def kickoff(self):
        # 1. Initialize Agents
        healthcare_researcher = Agent(
            role='Healthcare Data Researcher',
            goal=f'Uncover raw clinical facts and newest breakthroughs in {self.topic}',
            backstory=(
                "You are a meticulous data-driven researcher. Your job is to find the ground truth: "
                "clinical trial results, FDA filings, and technical specifications."
            ),
            tools=researcher_tools,
            llm=research_llm,
            verbose=True,
            allow_delegation=False
        )

        optum_health_strategist = Agent(
            role='OptumHealth Strategist',
            goal=f'Analyze {self.topic} for impact on Value-Based Care and Patient Outcomes',
            backstory="You represent OptumHealth. Your mission is to improve the care delivery model.",
            llm=health_llm,
            verbose=True,
            allow_delegation=False
        )

        optum_insight_analyst = Agent(
            role='OptumInsight Technology Consultant',
            goal=f'Analyze {self.topic} for Data/AI integration and administrative efficiency',
            backstory="You represent OptumInsight. Your focus is technology and analytics as a service.",
            llm=insight_llm,
            verbose=True,
            allow_delegation=False
        )

        optum_rx_specialist = Agent(
            role='OptumRx Pharmacy specialist',
            goal=f'Analyze {self.topic} for Pharmacy Benefit Management (PBM) and Specialty Drug Spend',
            backstory="You represent OptumRx. Your world is pharmacy spend and formulary optimization.",
            llm=rx_llm,
            verbose=True,
            allow_delegation=False
        )

        optum_financial_analyst = Agent(
            role='Optum Financial Analyst',
            goal=(
                f'Analyze the financial impact of {self.topic} on Optum. '
                'Project ROI, Medical Loss Ratio (MLR) impact, and investment thresholds. '
                'Consider both short-term cost reduction and long-term strategic return.'
            ),
            backstory=(
                "You are the CFO's strategic advisor. You speak in IRR, NPV, MLR basis points, "
                "and break-even timelines. You translate clinical breakthroughs into hard fiscal "
                "realities: budget impact, risk-adjusted ROI, and capital allocation recommendations."
            ),
            llm=financial_llm,
            verbose=True,
            allow_delegation=False
        )

        # 2. Define Tasks
        research_task = Task(
            description=(
                f"Search for the 5 most significant clinical or technical developments in {self.topic} "
                "from the last 12 months. PROVIDE CONCISE DATA POINTS. Use bullet points. "
                "MAX 500 WORDS TOTAL."
            ),
            expected_output="A summarized report of raw clinical facts (Max 500 words).",
            agent=healthcare_researcher
        )

        health_strategy_task = Task(
            description=(
                f"Using the condensed research data, assess clinical viability for OptumHealth. "
                "Identify 3 ways this breakthrough helps. DO NOT REPEAT THE RESEARCH DATA. "
                "Focus ONLY on the strategic delta."
            ),
            expected_output="A concise Value-Based Care assessment (Bullet points only).",
            agent=optum_health_strategist
        )

        insight_technology_task = Task(
            description=(
                f"Identify 'Data-as-a-Service' or 'AI Workflow' opportunities in {self.topic}. "
                "Focus on productization. BE EXTREMELY BRIEF."
            ),
            expected_output="A brief tech roadmap (Bullet points only).",
            agent=optum_insight_analyst
        )

        rx_pharmacy_task = Task(
            description=(
                "Analyze the impact on pharmacy benefit management. "
                "Focus on spend and formulary. MAX 200 WORDS."
            ),
            expected_output="A brief pharmacy impact report.",
            agent=optum_rx_specialist
        )

        financial_strategy_task = Task(
            description=(
                f"Using the clinical research data on {self.topic}, deliver a fiscal impact assessment. "
                "Cover ALL of the following: "
                "1) Estimated ROI over 3-5 years if Optum invests in this technology/therapy. "
                "2) Medical Loss Ratio (MLR) impact — will this reduce or increase claims spend? "
                "3) Break-even timeline for adoption. "
                "4) Capital allocation recommendation (invest / watch / avoid). "
                "BE CONCISE. Use numbers and percentages where possible. MAX 250 WORDS."
            ),
            expected_output="A fiscal impact brief with ROI projection, MLR delta, and investment recommendation.",
            agent=optum_financial_analyst,
            context=[research_task]
        )

        synthesis_task = Task(
            description=(
                "Synthesize ALL reports — clinical, health strategy, technology, pharmacy, AND financial — "
                "into one final 'Optum Strategic Alpha' document. "
                "Structure it as: Executive Summary | Clinical Context | Care Delivery | Tech & AI | "
                "Pharmacy & PBM | Financial Impact | Strategic Recommendation. "
                "MAX 900 WORDS TOTAL FOR THE FINAL DOCUMENT."
            ),
            expected_output="A high-fidelity, 5-stream strategic report with financial impact section.",
            agent=optum_insight_analyst,
            context=[research_task, health_strategy_task, insight_technology_task, rx_pharmacy_task, financial_strategy_task]
        )

        # 3. Assemble and Run the Crew (5-Stream Intelligence Swarm)
        crew = Crew(
            agents=[
                healthcare_researcher,
                optum_health_strategist,
                optum_insight_analyst,
                optum_rx_specialist,
                optum_financial_analyst
            ],
            tasks=[
                research_task,
                health_strategy_task,
                insight_technology_task,
                rx_pharmacy_task,
                financial_strategy_task,
                synthesis_task
            ],
            process=Process.sequential,
            verbose=True
        )

        return crew.kickoff(inputs={'topic': self.topic})

def extract_clean_content(result):
    """Extracts raw strategic text from CrewOutput or ModelResponse objects."""
    # Handle CrewOutput (raw attribute)
    if hasattr(result, 'raw'):
        result = result.raw
    # Handle LiteLLM ModelResponse
    if hasattr(result, 'choices'):
        return result.choices[0].message.content
    return str(result)

if __name__ == "__main__":
    print("## Starting the Optum 3-Stream Strategic Crew")
    user_topic = input("Enter the research topic (e.g., 'Advancements in Heart Valve Replacements'): ")
    
    # Instantiate the crew class
    strategic_crew = OptumStrategicCrew(user_topic)
    raw_result = strategic_crew.kickoff()
    
    # Clean the result for the report
    clean_report = extract_clean_content(raw_result)
    
    print("\n" + "="*50)
    print("FINAL REPORT PREVIEW:")
    print("="*50)
    print(clean_report[:1000] + "...") # Show preview

    # --- PERSISTENCE LAYER: Save the report to the reports/ directory ---
    # Sanitize the topic for a safe filename
    safe_topic = re.sub(r'[^\w\s-]', '', user_topic).strip().replace(' ', '_')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"Strategic_Alpha_{safe_topic}_{timestamp}.md"
    filepath = os.path.join("reports", filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Optum Strategic Alpha Report: {user_topic}\n")
            f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(clean_report)
        print(f"\n[SUCCESS] Final Strategic Alpha Report saved to: {filepath}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save report to file: {e}")
