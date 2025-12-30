import os
import yaml
import pandas as pd
import datetime
import time
import json
import argparse
import glob
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
        self.start_time = time.time()
        self.analyzed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.selected_model = "unknown"
        self.analysis_stats = []  # Store execution stats per category
        
        # Security: Robust Env Loading & Masked Logging
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.mock_mode = False

    def initialize(self, use_mock=False):
        self.mock_mode = use_mock
        api_key = os.environ.get("GOOGLE_API_KEY")

        if self.mock_mode:
            print(">> [INFO] Running in MOCK MODE. No API Key required.")
            self.selected_model = "mock-model"
            return

        if not api_key:
            print(">> [CRITICAL] GOOGLE_API_KEY not found in environment variables.")
            print(">> Please ensure .env file exists and contains GOOGLE_API_KEY.")
            raise ValueError("API Key missing. Aborting Real-World Analysis.")
        else:
            masked_key = f"{api_key[:3]}***{api_key[-3:]}" if len(api_key) > 6 else "***"
            print(f">> [INFO] API Key Loaded: {masked_key}")
            
            # --- Auto-Model Detection Logic ---
            self.selected_model = "gemini-1.5-flash" # Default fallback
            try:
                genai.configure(api_key=api_key)
                available = []
                print(">> [INFO] Checking available models...")
                
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
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

                if "gemini-1.5-flash" in available:
                    self.selected_model = "gemini-1.5-flash"
                elif "gemini-1.5-pro" in available:
                    self.selected_model = "gemini-1.5-pro"
                elif "gemini-1.0-pro" in available:
                    self.selected_model = "gemini-1.0-pro"
                elif "gemini-pro" in available:
                    self.selected_model = "gemini-pro"
                else:
                    if available:
                        self.selected_model = available[0]
                
                print(f">> [INFO] Auto-Selected Model: {self.selected_model}")

            except Exception as e:
                print(f">> [WARNING] Model list failed ({e}). Defaulting to {self.selected_model}")

            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=self.selected_model,
                    temperature=0.0,
                    google_api_key=api_key
                )
            except Exception as e:
                 print(f">> [ERROR] Failed to initialize LLM: {e}.")
                 raise e

    def _ensure_directories(self):
        """Creates necessary directories if they don't exist."""
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
        return filepath

    def _generate_stats_table(self):
        """Generates a markdown table row for each analyzed category."""
        rows = []
        for stat in self.analysis_stats:
            rows.append(f"| {stat['Category']} | {stat['Status']} | {stat['Timestamp']} | [Logs](../../logs/{self.project_name}) |")
        return "\n".join(rows) if rows else "| No data | - | - | - |"

    def _generate_verification_trail(self):
        """Generates collapsible verification sections."""
        trail = []
        for stat in self.analysis_stats:
            trail.append(f"""
<details>
<summary><strong>🔍 Verify: {stat['Category']}</strong> (Click to Expand)</summary>

#### 1. Input Data Snippet
```text
{stat.get('InputSnippet', 'N/A')}
```

#### 2. Actual Prompt Used
```text
{stat.get('PromptSnippet', 'N/A')}
```

#### 3. Raw AI Response
```markdown
{stat.get('ResultUtils', 'N/A')}
```
</details>
<hr>
""")
        return "\n".join(trail)

    def generate_log_report(self):
        """(Deprecated) Generates a summary log report."""
        pass # Now merged into main report


    def update_readme(self, report_path):
        """Updates README.md to link to the latest analysis."""
        readme_path = "README.md"
        if not os.path.exists(readme_path):
            print(">> [WARNING] README.md not found. Skipping sync.")
            return

        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            # Create a summary (first 10 lines of report)
            summary_lines = report_content.split('\n')[:15]
            summary = "\n".join(summary_lines)
            
            # Construct the injection block (Prettier Format)
            injection = f"""<!-- LATEST_ANALYSIS_START -->
---
### 🚀 Latest VOC Analysis
> **Update**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} | **Project**: `{self.project_name}` | **Model**: `{self.selected_model}`

**Methodology**:
- **RAG Context**: {len(self.rag_context)} chars loaded.
- **Analysis Count**: {self.analyzed_count} categories processed.

**Quick Preview**:
```markdown
{summary}
...
```

👉 **[📄 Click Here to View Full Report]({report_path})** 
*(Includes detailed verification trail & logs)*
---
<!-- LATEST_ANALYSIS_END -->"""

            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace logic
            start_marker = "<!-- LATEST_ANALYSIS_START -->"
            end_marker = "<!-- LATEST_ANALYSIS_END -->"
            
            if start_marker in content and end_marker in content:
                # Replace existing block
                new_content = content.split(start_marker)[0] + injection + content.split(end_marker)[1]
            else:
                # Append to end if markers don't exist
                new_content = content + "\n\n" + injection
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f">> [INFO] README.md updated with latest analysis.")
            
        except Exception as e:
            print(f">> [ERROR] Failed to update README: {e}")

    def analyze_group(self, category_name, reviews_df):
        count = len(reviews_df)
        combined_text = "\n".join(reviews_df['review_text'].head(20).tolist())
        rag_section = f"\n[Guideline & Context from Query]\n{self.rag_context}\n" if self.rag_context else ""
        
        prompt_template_str = """
        You are a VOC Analyst. STRICT adherence to output format and tone is required.
        [RAG Context]
        {rag_section}
        [Instructions]
        1. Classify the reviews strictly based on the context above.
        2. Tone: summarize the issue in 'Eum-seum-che'.
        3. Do not add any introductory or concluding remarks. Only the Markdown.
        [Input Data]
        Category: {category_name}
        Review Count: {count}
        Reviews:
        {reviews}
        [Strict Output Format (Markdown)]
        ### N [{category_name}] [Main Issue] Ratio%, {count} cases
        - 이슈 요약 : (Summarize in 'Eum-seum-che', max 30 chars)
        - 감정 : (1-2 keywords)
        - | 불만 유형 | 비율 | 대표 예시 |
          | :--- | :--- | :--- |
          | (Type A) | (Approx %) | "(Example)" |
        - 개선 방향 : (Actionable suggestion)
        """
        
        prompt = PromptTemplate(
            template=prompt_template_str,
            input_variables=["category_name", "reviews", "count", "rag_section"]
        )
        
        formatted_prompt = prompt.format(
            category_name=category_name, 
            reviews=combined_text, 
            count=count,
            rag_section=rag_section
        )
        
        result = ""
        try:
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({
                "category_name": category_name, 
                "reviews": combined_text, 
                "count": count, 
                "rag_section": rag_section
            })
            self.success_count += 1
        except Exception as e:
            result = f"Error during LLM execution: {e}"
            self.fail_count += 1
        
        self.analyzed_count += 1
        
        # Record Stats
        # Record Stats & Verification Data
        self.analysis_stats.append({
            "Category": category_name,
            "Status": "Success" if result and "Error" not in result[:20] else "Failed",
            "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            "InputSnippet": combined_text[:200] + "..." if len(combined_text) > 200 else combined_text,
            "PromptSnippet": formatted_prompt,
            "ResultUtils": result
        })
        
        self._log_trace(category_name, combined_text, formatted_prompt, result)
        

        
        return result

    def _mock_analyze_group(self, category_name):
        """Returns a dummy analysis result for testing."""
        return f"""### N [{category_name}] [Main Issue] Mock Analysis Result
- 이슈 요약 : This is a mock summary for testing.
- 감정 : Mock Emotion
- | 불만 유형 | 비율 | 대표 예시 |
  | :--- | :--- | :--- |
  | Mock Type A | 50% | "Mock Example 1" |
- 개선 방향 : Mock Action Item"""

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
            if not team_reviews.empty:
                print(f"Analyzing category: {team} ({len(team_reviews)} reviews)...")
                if self.mock_mode:
                    section = self._mock_analyze_group(team)
                    # Manually add stats for mock
                    self.analysis_stats.append({
                        "Category": team,
                        "Status": "Success (Mock)",
                        "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "InputSnippet": "(Mock Data) Review 1...",
                        "PromptSnippet": "(Mock Prompt) ...",
                        "ResultUtils": section
                    })
                else:
                    section = self.analyze_group(team, team_reviews)
                report_sections.append(section)
                
        full_report = "\n\n".join(report_sections)
        
        # Merge Verification Trail (Unified Report)
        unified_report = f"""
{full_report}

---
# 🔍 Verification Center (Detailed Logs)

## 📝 Execution Stats
| Category | Status | Timestamp | Log Link |
| :--- | :--- | :--- | :--- |
{self._generate_stats_table()}

## 🔍 Verification Trail (Input -> Prompt -> Output)
{self._generate_verification_trail()}
"""
        
        # Save Result
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{timestamp}.md"
        saved_path = self._save_result(unified_report, report_filename)
        
        # Sync README (No separate log report)
        self.update_readme(saved_path)
        
        return unified_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOC AI Analyzer")
    parser.add_argument("--project", type=str, default="default_analysis", help="Project name for output subdirectory")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without API calls")
    
    args = parser.parse_args()
    
    analyzer = VOCAnalyzer(project_name=args.project)
    analyzer.initialize(use_mock=args.mock)
    
    if os.path.exists("data/raw/mock_reviews.csv"):
        analyzer.generate_full_report("data/raw/mock_reviews.csv")
    else:
        print("Mock data not found. Run generate_data.py first.")
