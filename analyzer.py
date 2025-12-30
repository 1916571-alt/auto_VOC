import os
import yaml
import pandas as pd
# Use langchain-google-genai as agreed in plan, despite prompt copy-paste mentioning openai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class VOCAnalyzer:
    def __init__(self, config_path="config/teams.yaml"):
        self.config = self._load_config(config_path)
        
        # Initialize Gemini
        if "GOOGLE_API_KEY" not in os.environ:
             print("Warning: GOOGLE_API_KEY is missing.")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.0
        )

    def _load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {}

    def analyze_group(self, category_name, reviews_df):
        """
        Analyzes a group of reviews and returns the strict markdown format.
        """
        count = len(reviews_df)
        ratio = 0 # This would be calculated in the full report context
        
        # Concatenate texts for the prompt (limit length if needed)
        combined_text = "\n".join(reviews_df['review_text'].head(20).tolist())
        
        prompt_template = """
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
            template=prompt_template,
            input_variables=["category_name", "reviews", "count"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(category_name=category_name, reviews=combined_text, count=count)
        return result

    def generate_full_report(self, csv_path):
        df = pd.read_csv(csv_path)
        
        # Simple keyword-based clustering to simulate "RAG Classification" grouping
        # In a full RAG system, we would embed all reviews and cluster them.
        # For this prototype, we use the team keywords from config.
        
        report_sections = []
        total_reviews = len(df)
        
        for team, info in self.config.get('teams', {}).items():
            keywords = info.get('keywords', [])
            # Filter reviews containing any of the keywords
            team_reviews = df[df['review_text'].apply(lambda x: any(k in str(x) for k in keywords))]
            
            if not team_reviews.empty:
                ratio = (len(team_reviews) / total_reviews) * 100
                # Generate section using LLM
                section = self.analyze_group(team, team_reviews)
                # Inject the real ratio if LLM didn't get it right (clean up header)
                # For now, trust the LLM or post-process.
                # Let's simple format the header with Python to be accurate on numbers
                
                # We ask LLM for the content, but we can overwrite the header.
                report_sections.append(section)
                
        return "\n\n".join(report_sections)

if __name__ == "__main__":
    analyzer = VOCAnalyzer()
    if os.path.exists("data/raw/mock_reviews.csv"):
        print(analyzer.generate_full_report("data/raw/mock_reviews.csv"))
    else:
        print("Mock data not found.")
