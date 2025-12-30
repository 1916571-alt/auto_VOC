import os
import yaml
import pandas as pd
import datetime
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

class VOCAnalyzer:
    def __init__(self, config_path="config/teams.yaml"):
        self._ensure_directories()
        self.config = self._load_config(config_path)
        
        # Security: Load API Key from environment variable only
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("CRITICAL WARNING: GOOGLE_API_KEY not found in environment variables.")
            print("Please create a .env file with GOOGLE_API_KEY='your_key' or set it in your system.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.0,
                google_api_key=api_key
            )

    def _ensure_directories(self):
        """Creates necessary directories if they don't exist."""
        dirs = ["data/raw", "data/processed", "data/logs"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def _log_trace(self, category, input_data, prompt_text, response_text):
        """Logs the analysis trace to a file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"data/logs/trace_{timestamp}_{category}.log"
        
        try:
            with open(log_filename, "w", encoding="utf-8") as f:
                f.write(f"=== [Step 1: Raw Input] ===\n")
                f.write(f"{input_data}\n\n")
                f.write(f"=== [Step 2: Constructed Prompt] ===\n")
                f.write(f"{prompt_text}\n\n")
                f.write(f"=== [Step 3: AI Raw Response] ===\n")
                f.write(f"{response_text}\n")
            print(f"Trace log saved: {log_filename}")
        except Exception as e:
            print(f"Failed to write log: {e}")

    def analyze_group(self, category_name, reviews_df):
        """
        Analyzes a group of reviews, logs the process, and returns the markdown format.
        """
        if not self.llm:
            return "Error: LLM not initialized due to missing API Key."

        count = len(reviews_df)
        
        # Concatenate texts for the prompt
        # Masking strictly sensitive info is complex without specific rules, 
        # but here we ensure we only pass the text column.
        combined_text = "\n".join(reviews_df['review_text'].head(20).tolist())
        
        prompt_template_str = """
        You are a VOC Analyst. specific output format is required.
        Analyze the following customer reviews for the category '{category_name}'.
        
        Reviews:
        {reviews}
        
        Strict Output Format (Markdown):
        ### N [{category_name}] [Main Issue] Ratio%, {count} cases
        - 이슈 요약 : (Summarize in Korean 'Eum-seum-che' style, max 30 chars)
        - 감정 : (1-2 keywords like 불만, 분노, 아쉬움)
        - | 불만 유형 | 비율 | 대표 예시 |
          | :--- | :--- | :--- |
          | (Type A) | (Approx %) | "(Example)" |
          | (Type B) | (Approx %) | "(Example)" |
        - 개선 방향 : (Actionable suggestion)
        
        Do not output anything else. Just the markdown.
        """
        
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["category_name", "reviews", "count"]
        )
        
        # Traceability: Capture the formatted prompt before sending
        formatted_prompt = prompt.format(category_name=category_name, reviews=combined_text, count=count)
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        try:
            result = chain.run(category_name=category_name, reviews=combined_text, count=count)
        except Exception as e:
            result = f"Error during LLM execution: {e}"

        # Log the full trace
        self._log_trace(category_name, combined_text, formatted_prompt, result)
        
        return result

    def generate_full_report(self, csv_path):
        if not os.path.exists(csv_path):
            return "Error: Data file not found."

        df = pd.read_csv(csv_path)
        report_sections = []
        total_reviews = len(df)
        
        for team, info in self.config.get('teams', {}).items():
            keywords = info.get('keywords', [])
            # Filter reviews containing any of the keywords
            team_reviews = df[df['review_text'].apply(lambda x: any(k in str(x) for k in keywords))]
            
            if not team_reviews.empty:
                print(f"Analyzing category: {team} ({len(team_reviews)} reviews)...")
                section = self.analyze_group(team, team_reviews)
                report_sections.append(section)
                time.sleep(1) # Slight delay to separate logs nicely
                
        return "\n\n".join(report_sections)

if __name__ == "__main__":
    analyzer = VOCAnalyzer()
    if os.path.exists("data/raw/mock_reviews.csv"):
        print(analyzer.generate_full_report("data/raw/mock_reviews.csv"))
    else:
        print("Mock data not found. Run generate_data.py first.")
