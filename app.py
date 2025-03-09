# -*- coding: utf-8 -*-
"""movie_app

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1H6bvBO9a0cTKq-FrV8J_Zx2taSPGIrh7
"""

import streamlit as st
import requests
import plotly.express as px
import json
import re

# Backend URL
BACKEND_URL = "https://movie-reviews-frontend-h2rz.onrender.com"

# Streamlit UI
st.set_page_config(page_title="🎬 Movie Review Analyzer", layout="wide")

# Title with an Icon
st.markdown("""
<div style="text-align: center; font-size: 24px; font-weight: bold; color: #FF5733;">
🚀 Say Goodbye to Fake Reviews! 🎥
🔎 Get **Real & Unbiased** Movie Opinions from Reddit Discussions.
</div>
""", unsafe_allow_html=True)

# Function to fix malformed JSON
def fix_json(json_string):
    """Fix common JSON formatting issues"""
    # Add missing commas between key-value pairs
    json_string = re.sub(r'"\s*"', '","', json_string)

    # Ensure all keys are properly quoted
    json_string = re.sub(r'(\n\s*)(\w+):', r'\1"\2":', json_string)

    # Fix nested objects missing commas
    json_string = re.sub(r'}\s*{', '},{', json_string)

    # Add missing commas in arrays
    json_string = re.sub(r']\s*\[', '],[', json_string)

    return json_string

# User Input
st.markdown("### 🎥 Enter Movie Name")
movie_name = st.text_input("Movie Name", placeholder="e.g., Animal, Oppenheimer, Pathaan", label_visibility="collapsed")

# Debug section
st.sidebar.subheader("Debug Information")
debug_expander = st.sidebar.expander("Show Debug Info", expanded=False)

if st.button("🔍 Analyze Movie"):
    if movie_name:
        with st.spinner("Fetching Reddit discussions..."):
            try:
                # Prepare request with proper headers
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }

                # Log the request details
                request_url = f"{BACKEND_URL}/analyze"
                params = {"movie_name": movie_name}

                with debug_expander:
                    st.write(f"Request URL: {request_url}")
                    st.write(f"Params: {params}")

                # Make the request
                response = requests.get(request_url, params=params, headers=headers, timeout=30)

                # Log the response
                with debug_expander:
                    st.write(f"Response Status: {response.status_code}")
                    st.write(f"Response Headers: {dict(response.headers)}")

                if response.status_code == 200:
                    try:
                        # Try to parse the JSON response directly
                        try:
                            api_data = response.json()
                        except json.JSONDecodeError:
                            # If parsing fails, try to fix the JSON
                            with debug_expander:
                                st.write("Original response text (malformed JSON):")
                                st.text(response.text)

                                fixed_json_text = fix_json(response.text)
                                st.write("Attempted to fix JSON:")
                                st.text(fixed_json_text)

                            try:
                                api_data = json.loads(fixed_json_text)
                            except json.JSONDecodeError as e:
                                st.error(f"Could not parse the API response as JSON. Error: {str(e)}")
                                st.error("Please contact the backend team to fix the JSON format.")
                                st.stop()

                        # Display raw response for debugging
                        with debug_expander:
                            st.write("Parsed API data:")
                            st.json(api_data)

                        # Handle the special JSON structure from your backend
                        if "analysis" in api_data:
                            analysis = api_data["analysis"]

                            # Convert analysis from dict with numbered keys to a proper structure
                            if isinstance(analysis, dict):
                                # Extract the data based on the structure seen in your response
                                tldr = analysis.get("1. TL;DR Summary", "No summary available.")
                                overall_sentiment = analysis.get("2. Overall Sentiment Analysis", {})
                                audience_reactions = analysis.get("3. Summary of Audience Reactions", "")
                                key_aspects = analysis.get("4. Key Aspects Discussed", {})
                                common_items = analysis.get("5. Common Praise & Complaints", {})
                                similar_movies = analysis.get("6. Comparison with Similar Movies", [])
                                final_verdict = analysis.get("7. Final Verdict", {})

                                # Display Results
                                st.subheader("📢 TL;DR Summary")
                                st.success(tldr)

                                # Sentiment Analysis Visualization
                                st.subheader("📊 Sentiment Analysis")
                                if isinstance(overall_sentiment, dict):
                                    labels = ["Positive", "Negative", "Neutral"]
                                    values = [
                                        overall_sentiment.get("positivePercentage", 0),
                                        overall_sentiment.get("negativePercentage", 0),
                                        overall_sentiment.get("neutralPercentage", 0),
                                    ]
                                    if sum(values) > 0:
                                        fig = px.pie(
                                            names=labels,
                                            values=values,
                                            title="Sentiment Breakdown",
                                            color=labels,
                                            color_discrete_map={"Positive": "green", "Negative": "red", "Neutral": "gray"},
                                        )
                                        st.plotly_chart(fig)
                                    else:
                                        st.warning("No sentiment data available.")

                                    # Display key phrases if available
                                    if "keyPhrases" in overall_sentiment and overall_sentiment["keyPhrases"]:
                                        st.write("**Key Phrases:**")
                                        phrases = overall_sentiment["keyPhrases"]
                                        if isinstance(phrases, dict):
                                            phrases = list(phrases.values())
                                        elif isinstance(phrases, list):
                                            phrases = phrases
                                        else:
                                            phrases = []

                                        for phrase in phrases:
                                            st.write(f"- {phrase}")
                                else:
                                    st.warning("No sentiment data available.")

                                # Audience Reactions
                                st.subheader("💬 Audience Reactions")
                                st.write(audience_reactions)

                                # Key Aspects Ratings
                                st.subheader("🎭 Key Aspects Ratings")
                                if isinstance(key_aspects, dict):
                                    aspect_labels = []
                                    aspect_values = []
                                    aspect_explanations = []

                                    for aspect, data in key_aspects.items():
                                        if isinstance(data, dict):
                                            score = data.get("score")
                                            if score and score != "N/A":
                                                try:
                                                    score_val = float(score)
                                                    aspect_labels.append(aspect)
                                                    aspect_values.append(score_val)
                                                    aspect_explanations.append(data.get("explanation", ""))
                                                except (ValueError, TypeError):
                                                    pass

                                    if aspect_labels and aspect_values:
                                        fig = px.bar(
                                            x=aspect_labels,
                                            y=aspect_values,
                                            title="Key Aspects Ratings",
                                            labels={"x": "Aspect", "y": "Rating"},
                                            color=aspect_values,
                                            color_continuous_scale="Viridis"
                                        )
                                        st.plotly_chart(fig)

                                        # Display explanations for each aspect
                                        for i, aspect in enumerate(aspect_labels):
                                            if i < len(aspect_explanations):
                                                st.write(f"**{aspect}:** {aspect_explanations[i]}")
                                    else:
                                        st.warning("No valid aspect ratings to display.")
                                else:
                                    st.warning("No key aspect ratings available.")

                                # Common Praises & Complaints
                                st.subheader("👍 Common Praise & 👎 Complaints")
                                if isinstance(common_items, dict):
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.write("**✅ Praise:**")
                                        praises = common_items.get("praise", [])
                                        if isinstance(praises, dict):
                                            praises = list(praises.values())

                                        if praises:
                                            for praise in praises:
                                                st.write(f"- {praise}")
                                        else:
                                            st.write("No praise data available.")

                                    with col2:
                                        st.write("**❌ Complaints:**")
                                        complaints = common_items.get("complaints", [])
                                        if isinstance(complaints, dict):
                                            complaints = list(complaints.values())

                                        if complaints:
                                            for complaint in complaints:
                                                st.write(f"- {complaint}")
                                        else:
                                            st.write("No complaints data available.")
                                else:
                                    st.warning("No praise or complaints data available.")

                                # Similar Movies
                                st.subheader("🎬 Similar Movies")
                                if similar_movies:
                                    # Handle both list and dict formats
                                    if isinstance(similar_movies, dict):
                                        similar_movies = list(similar_movies.values())

                                    for movie in similar_movies:
                                        if isinstance(movie, dict):
                                            title = movie.get("title", "Unknown")
                                            year = movie.get("year", "N/A")
                                            similarity = movie.get("similarity", "")
                                            st.write(f"🎞️ **{title} ({year})** - {similarity}")
                                else:
                                    st.write("No similar movies data available.")

                                # Final Verdict
                                st.subheader("🏆 Final Verdict")
                                if isinstance(final_verdict, dict):
                                    st.write("**Who Would Enjoy:**", final_verdict.get("whoWouldEnjoy", "Not available."))
                                    st.write("**Who Might Not Enjoy:**", final_verdict.get("whoMightNotEnjoy", "Not available."))
                                    st.write("**Theater vs Streaming:**", final_verdict.get("theaterOrStreaming", "Not available."))
                                else:
                                    st.write("No final verdict data available.")
                            else:
                                st.error("The analysis data is not in the expected format.")
                        else:
                            st.error("The API response did not contain analysis data.")

                    except Exception as e:
                        st.error(f"Error processing API response: {str(e)}")
                        with debug_expander:
                            st.exception(e)
                else:
                    st.error(f"🚨 Error fetching movie analysis. Status code: {response.status_code}")
                    with debug_expander:
                        st.write("Response content:")
                        st.text(response.text[:500] + "..." if len(response.text) > 500 else response.text)

            except requests.exceptions.RequestException as e:
                st.error(f"🚨 Network error: {str(e)}")
                with debug_expander:
                    st.exception(e)
            except Exception as e:
                st.error(f"🚨 Unexpected error: {str(e)}")
                with debug_expander:
                    st.exception(e)
    else:
        st.warning("⚠️ Please enter a movie name.")