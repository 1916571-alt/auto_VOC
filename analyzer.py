import os
import yaml
import pandas as pd
import datetime
import time
import json
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()

class VOCAnalyzer:
    def __init__(self, config_path="config/teams.yaml", project_name="default_analysis"):
        self.project_name = project_name
        self._ensure_directories()
        self.config = self._load_config(config_path)
        self.rag_context = self._load_rag_documents()
        
        # Security: Robust Env Loading & Masked Logging
        # Explicitly check os.environ to ensure system env vars (like in GitHub Actions) are caught
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.mock_mode = False

        if not api_key:
            # Strict Mode Enforcement
            print(">> [CRITICAL] GOOGLE_API_KEY not found in environment variables.")
            print(">> Please ensure .env file exists and contains GOOGLE_API_KEY.")
            raise ValueError("API Key missing. Aborting Real-World Analysis.")
        else:
            # Masked Logging
            masked_key = f"{api_key[:3]}***{api_key[-3:]}" if len(api_key) > 6 else "***"
            print(f">> [INFO] API Key Loaded: {masked_key}")
            
            # --- Auto-Model Detection Logic ---
            selected_model = "gemini-1.5-flash" # Default fallback
            try:
                genai.configure(api_key=api_key)
                available = []
                print(">> [INFO] Checking available models...")
                
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        # Strip 'models/' prefix for cleaner comparison/usage if needed by LangChain
                        model_name = m.name.replace("models/", "")
                        available.append(model_name)
                
                # Log available models
                try:
                    log_path = f"data/logs/{self.project_name}/available_models.log"
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(available))
                    print(f">> [INFO] Available models logged to {log_path}: {available}")
                except Exception as e:
                    print(f">> [WARNING] Failed to log available models: {e}")

                # Priority: 1.5-flash -> 1.5-pro -> 1.0-pro (or others found)
                if "gemini-1.5-flash" in available:
                    selected_model = "gemini-1.5-flash"
                elif "gemini-1.5-pro" in available:
                    selected_model = "gemini-1.5-pro"
                elif "gemini-1.0-pro" in available:
                    selected_model = "gemini-1.0-pro"
                elif "gemini-pro" in available:
                    selected_model = "gemini-pro"
                else:
                    if available:
                        selected_model = available[0]
                
                print(f">> [INFO] Auto-Selected Model: {selected_model}")

            except Exception as e:
                print(f">> [WARNING] Model list failed ({e}). Defaulting to {selected_model}")

            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=selected_model,
                    temperature=0.0,
                    google_api_key=api_key
                )
            except Exception as e:
                 print(f">> [ERROR] Failed to initialize LLM: {e}.")
                 raise e

    def _ensure_directories(self):
        """Creates necessary directories if they don't exist."""
        # Clean project name to avoid path issues
        safe_project_name = "".join([c for c in self.project_name if c.isalnum() or c in ('-', '_')]).strip()
        if not safe_project_name:
            safe_project_name = "default_analysis"
        
        self.project_name = safe_project_name
        
        dirs = [
            "data/raw", 
            "data/docs",
            f"data/processed/{self.project_name}", 
            f"data/logs/{self.project_name}"
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        print(f">> [INFO] Project directories initialized for: {self.project_name}")

    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
            
    def _load_rag_documents(self):
        """Loads all .txt files from data/docs to form the RAG context."""
        context = []
        if os.path.exists("data/docs"):
            for file in os.listdir("data/docs"):
                if file.endswith(".txt"):
                    try:
                        with open(f"data/docs/{file}", "r", encoding="utf-8") as f:
                            context.append(f"[{file}]\n{f.read()}")
                    except Exception as e:
                        print(f"Failed to read doc {file}: {e}")
        return "\n\n".join(context)

    def _log_trace(self, category, input_data, prompt_text, response_text):
        """Logs the analysis trace to detailed files."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = f"data/logs/{self.project_name}"
        
        # 1. Main Trace Log (Summary)
        log_filename = f"{base_path}/trace_{timestamp}_{category}.log"
        try:
            with open(log_filename, "w", encoding="utf-8") as f:
                f.write(f"=== [Step 1: Raw Input] ===\n")
                f.write(f"{input_data}\n\n")
                f.write(f"=== [Step 2: Constructed Prompt Used] ===\n")
                f.write(f"(See {timestamp}_{category}_prompt.txt for full content)\n\n")
                f.write(f"=== [Step 3: AI Raw Response] ===\n")
                f.write(f"{response_text}\n")
        except Exception as e:
            print(f"Failed to write summary log: {e}")

        # 2. Detailed Prompt Log
        prompt_filename = f"{base_path}/{timestamp}_{category}_prompt.txt"
        try:
            with open(prompt_filename, "w", encoding="utf-8") as f:
                f.write(prompt_text)
        except Exception as e:
            print(f"Failed to write prompt log: {e}")

        # 3. Raw Response JSON
        res_filename = f"{base_path}/{timestamp}_{category}_raw_res.json"
        try:
            with open(res_filename, "w", encoding="utf-8") as f:
                json.dump({"category": category, "response": response_text}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to write response json: {e}")

    def _save_result(self, content, filename="final_report.md"):
        """Saves the final report to data/processed."""
        filepath = f"data/processed/{self.project_name}/{filename}"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Report saved to: {filepath}")

    def analyze_group(self, category_name, reviews_df):
        """
        Analyzes a group of reviews, logs the process, and returns the markdown format.
        """
        count = len(reviews_df)
        combined_text = "\n".join(reviews_df['review_text'].head(20).tolist())
        
        # RAG Context Injection
        rag_section = f"\n[Guideline & Context from Query]\n{self.rag_context}\n" if self.rag_context else ""
        
        prompt_template_str = """
        You are a VOC Analyst. STRICT adherence to output format and tone is required.
        
        [RAG Context]
        {rag_section}
        
        [Instructions]
        1. Classify the reviews strictly based on the context above.
        2. Tone: summarize the issue in 'Eum-seum-che' (Korean ending with noun or ~m/um). 
           Example: "결제 오류가 발생함" (O), "결제 오류가 발생했습니다" (X).
        3. Do not add any introductory or concluding remarks. Only the Markdown.
        
        [Input Data]
        Category: {category_name}
        Review Count: {count}
        Reviews:
        {reviews}
        
        [Strict Output Format (Markdown)]
        ### N [{category_name}] [Main Issue] Ratio%, {count} cases
        - 이슈 요약 : (Summarize in 'Eum-seum-che', max 30 chars)
        - 감정 : (1-2 keywords like 불만, 분노, 아쉬움)
        - | 불만 유형 | 비율 | 대표 예시 |
          | :--- | :--- | :--- |
          | (Type A) | (Approx %) | "(Example)" |
          | (Type B) | (Approx %) | "(Example)" |
        - 개선 방향 : (Actionable suggestion)
        """
        
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["category_name", "reviews", "count", "rag_section"]
        )
        
        # Traceability: Capture the formatted prompt
        formatted_prompt = prompt.format(
            category_name=category_name, 
            reviews=combined_text, 
            count=count,
            rag_section=rag_section
        )
        
        result = ""
        try:
            # Modern LCEL Pattern: prompt | llm | output_parser
            chain = prompt | self.llm | StrOutputParser()
            
            result = chain.invoke({
                "category_name": category_name, 
                "reviews": combined_text, 
                "count": count, 
                "rag_section": rag_section
            })
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
        
        print(f"Starting Analysis for Project: {self.project_name} ... (Mock Mode: {self.mock_mode})")
        if self.rag_context:
            print(f"RAG Context Loaded: {len(self.rag_context)} chars")
        else:
            print("RAG Context: None loaded.")
        
        for team, info in self.config.get('teams', {}).items():
            keywords = info.get('keywords', [])
            team_reviews = df[df['review_text'].apply(lambda x: any(k in str(x) for k in keywords))]
            
            if not team_reviews.empty:
                print(f"Analyzing category: {team} ({len(team_reviews)} reviews)...")
                section = self.analyze_group(team, team_reviews)
                report_sections.append(section)
                
        full_report = "\n\n".join(report_sections)
        
        # Save Result
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._save_result(full_report, f"report_{timestamp}.md")
        
        return full_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOC AI Analyzer")
    parser.add_argument("--project", type=str, default="default_analysis", help="Project name for output subdirectory")
    
    args = parser.parse_args()
    
    analyzer = VOCAnalyzer(project_name=args.project)
    
    if os.path.exists("data/raw/mock_reviews.csv"):
        analyzer.generate_full_report("data/raw/mock_reviews.csv")
    else:
        print("Mock data not found. Run generate_data.py first.")
