import re
import pandas as pd
import json
import google.generativeai as genai

def preprocess_text(text: str) -> str:
    """
    Preprocesses the text by converting to lowercase and removing punctuation.
    """
    if isinstance(text, str):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()
    return ""

def process_text_with_gemini(text: str) -> dict:
    """
    Processes text with Gemini API and returns structured theme data.
    """
    model = genai.GenerativeModel("gemini-pro")
    prompt = """
    Analyze the following review and extract key themes and their specific sub-themes.
    Each subtheme must belong to exactly one theme.
    Return ONLY a valid JSON object with this exact structure:
    {
        "themes": {
            "theme1": {
                "reviews": [],
                "subthemes": {
                    "subtheme1": [],
                    "subtheme2": []
                }
            }
        }
    }
    
    Review text:
    """ + text

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up JSON response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
            
        return json.loads(response_text)
    except Exception as e:
        print(f"Error processing with Gemini: {str(e)}")
        return {"themes": {}}

"""
Prompt V2

Theming and Sub-Theming Process for Customer Feedback Analysis

Objective:

The system must analyze customer feedback data from various sources (reviews, support tickets, surveys, call transcripts, social media) and generate structured themes and sub-themes. These themes should allow customers to explore key insights, track trends, and understand their impact on overall business metrics.

Theme and Sub-Theme Creation Process:

Data Input: The system ingests customer feedback in textual form.

Theming Rules: The system processes the text and extracts themes based strictly on the provided feedback. It should not rely on external data for theme generation but can use background knowledge to infer intent.

Structure:

Generate top-level themes that summarize broad categories (e.g., "Customer Service").

Generate sub-themes that provide more detail (e.g., "Friendly and Welcoming," "Knowledgeable Staff").

Concept Matching:

Identify synonyms and related terms within the dataset (e.g., "helpful" also implies "attentive" and "welcoming").

Group similar concepts under appropriate sub-themes.

Descriptive and Actionable Tags:

Ensure the labels provide meaningful insight (e.g., instead of "Shopping Experience," use "Greeting and Welcome Experience" or "Store Crowdedness").

Avoid vague or generic labels that lack context.

Expected Output:

A structured list of themes and sub-themes extracted from the feedback.

Ability to drill down into specific themes to understand customer sentiment.

A tagging system that is accurate, interpretable, and useful for business analysis.

Example:

Customer Feedback: "I recently visited Missouri, and I had a great experience. The store has a wide selection of beautiful pieces. The staff was incredibly helpful and welcoming."

Generated Themes:

General Store Experience

Selection and Product Inventory

Customer Service

Friendly and Welcoming

Knowledgeable Staff

Product Quality

Beautiful Selection

Key Success Criteria:

Themes must be derived directly from the feedback data.

The system should provide clear, structured themes that enhance analysis.

Labels should be specific enough to provide business insights.

The goal of this process is to create better and more insightful themes than currently available, enabling businesses to understand customer sentiment at a granular level.

"""
    
def process_and_map_reviews(reviews: pd.Series) -> dict:
    """
    Processes multiple reviews and creates hierarchical theme-subtheme mappings.
    """
    theme_mapping = {}
    
    for i, review in enumerate(reviews):
        print(f"Processing review {i+1}/{len(reviews)}")
        try:
            # Preprocess the review
            processed_review = preprocess_text(review)
            if not processed_review:
                continue
                
            result = process_text_with_gemini(processed_review)
            
            if 'themes' in result:
                for theme, theme_data in result['themes'].items():
                    # Initialize theme if not exists
                    if theme not in theme_mapping:
                        theme_mapping[theme] = {
                            "reviews": [],
                            "subthemes": {}
                        }
                    
                    # Add review to theme
                    theme_mapping[theme]["reviews"].append(review)
                    
                    # Process subthemes
                    for subtheme, subtheme_reviews in theme_data.get("subthemes", {}).items():
                        if subtheme not in theme_mapping[theme]["subthemes"]:
                            theme_mapping[theme]["subthemes"][subtheme] = []
                        # Add the review to this subtheme
                        theme_mapping[theme]["subthemes"][subtheme].append(review)
        
        except Exception as e:
            print(f"Error processing review {i}: {e}")
            continue
    
    return theme_mapping

def analyze_reviews(df: pd.DataFrame, num_reviews: int = 10) -> dict:
    """
    Main function to analyze reviews from a DataFrame.
    """
    # Get the first n reviews
    reviews = df['Text'].head(num_reviews)
    
    if reviews.empty:
        print("Error: No reviews found in the DataFrame")
        return {}
    
    # Process the reviews and create mappings
    mappings = process_and_map_reviews(reviews)
    
    # Save results to JSON file
    try:
        with open("theme_buckets.json", "w", encoding='utf-8') as f:
            json.dump(mappings, f, indent=4, ensure_ascii=False)
        print("Results saved to theme_buckets.json")
    except Exception as e:
        print(f"Warning: Could not save to JSON file: {e}")
    
    return mappings

def print_theme_hierarchy(mappings: dict):
    """
    Prints themes and their subthemes with associated reviews.
    """
    for theme, theme_data in mappings.items():
        print(f"\nTheme: {theme}")
        print("Theme Reviews:")
        for review in theme_data["reviews"]:
            print(f"  - {review[:100]}...")  # Print first 100 chars
            
        print("\nSubthemes:")
        for subtheme, subtheme_reviews in theme_data["subthemes"].items():
            print(f"  {subtheme}")
            for review in subtheme_reviews:
                print(f"    - {review[:100]}...")  # Print first 100 chars

df = pd.read_csv("summarized_review.csv")
mappings = analyze_reviews(df, num_reviews=10)
print_theme_hierarchy(mappings)