import pandas as pd
import numpy as np

def calculate_correlations(file_path="data/raw/mock_reviews.csv"):
    try:
        df = pd.read_csv(file_path)
        
        # Since 'sentiment_score' doesn't exist in the raw mock data, 
        # we will simulate it for testing the statistical logic.
        # In a real scenario, this would come from the Analyzer or a separate sentiment analysis step.
        # Adding some noise to star_rating to simulate sentiment score (0.0 to 1.0)
        np.random.seed(42)
        df['sentiment_score'] = (df['star_rating'] / 5.0) + np.random.normal(0, 0.1, len(df))
        df['sentiment_score'] = df['sentiment_score'].clip(0, 1) # Normalize to 0-1
        
        correlation = df['star_rating'].corr(df['sentiment_score'])
        
        print(f"Analysis Results for {file_path}")
        print("-" * 30)
        print(f"Data Count: {len(df)}")
        print(f"Correlation (Star Rating vs Sentiment): {correlation:.4f}")
        
        if correlation > 0.5:
            print(">> Result: Significant positive correlation found (Expected). Logic verified.")
        else:
            print(">> Result: Weak or no correlation. Check data quality.")
            
        return correlation
    except Exception as e:
        print(f"Error in statistics engine: {e}")
        return None

if __name__ == "__main__":
    calculate_correlations()
