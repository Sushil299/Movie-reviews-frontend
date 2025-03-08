# -*- coding: utf-8 -*-
"""movie_app

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1H6bvBO9a0cTKq-FrV8J_Zx2taSPGIrh7
"""

import streamlit as st
import asyncio
import nest_asyncio
import json
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from backend import search_reddit, analyze_with_gemini  # Assuming backend code is in backend.py

# Apply nest_asyncio to fix event loop issues
nest_asyncio.apply()

# Set Page Config
st.set_page_config(page_title="🎬 Movie Review Analyzer", layout="wide")

# Title with an Icon
st.markdown("<h1 style='text-align: center;'>🎬 Movie Review Analyzer</h1>", unsafe_allow_html=True)

# ⭐ Value Proposition Section (Short & Impactful)
st.markdown("""
<div style="text-align: center; font-size: 18px; font-weight: bold; color: #FF5733;">
🚀 Say Goodbye to Fake Reviews!
🔎 Get **Real & Unbiased** Movie Opinions from Reddit Discussions.
</div>
""", unsafe_allow_html=True)


# Input Section
movie_name = st.text_input("🔎 Enter Movie Name", placeholder="e.g., Animal, Jawan, Kantara")
days = st.slider("⏳ Look back (days)", 7, 90, 30)

# Button to Fetch Analysis
if st.button("🎥 Analyze Movie"):
    if not movie_name:
        st.warning("⚠️ Please enter a movie name!")
    else:
        with st.spinner("⏳ Fetching and analyzing Reddit discussions..."):
            reddit_data = asyncio.run(search_reddit(movie_name, days))
            analysis_result = asyncio.run(analyze_with_gemini(movie_name, reddit_data))

        if not analysis_result:
            st.error("❌ Analysis failed! Try again later.")
        else:
            # Movie Poster GIF (Random from API or Static)
            st.image("https://media.giphy.com/media/3o6ZsYx1UcOSd3EmBO/giphy.gif", use_column_width=True)

            # Summary Section
            st.subheader("📌 TL;DR Summary")
            st.success(analysis_result.get("TL;DR Summary", "No summary available."))

            # Sentiment Analysis Visualization
            st.subheader("📊 Sentiment Analysis")
            sentiment = analysis_result.get("Overall Sentiment Analysis", {})
            if sentiment:
                labels = ["Positive", "Negative", "Neutral"]
                values = [sentiment.get("Positive", 0), sentiment.get("Negative", 0), sentiment.get("Neutral", 0)]
                fig = px.pie(names=labels, values=values, title="Sentiment Breakdown")
                st.plotly_chart(fig)

            # Audience Reactions
            st.subheader("🗣️ Audience Reactions")
            st.write(analysis_result.get("Summary of Audience Reactions", "No data available."))

            # Ratings Visualization
            st.subheader("🌟 Key Aspects Ratings")
            aspects = analysis_result.get("Key Aspects Discussed", {})
            if aspects:
                df = pd.DataFrame(list(aspects.items()), columns=["Aspect", "Rating"])
                fig = px.bar(df, x="Aspect", y="Rating", title="Movie Aspects Ratings", color="Rating", text_auto=True)
                st.plotly_chart(fig)

            # Praise & Complaints
            st.subheader("✅ Common Praise & ⚠️ Complaints")
            praise = analysis_result.get("Common Praise & Complaints", {}).get("praise", [])
            complaints = analysis_result.get("Common Praise & Complaints", {}).get("complaints", [])

            col1, col2 = st.columns(2)
            with col1:
                st.write("### ✅ Praise")
                for p in praise:
                    st.write(f"- {p}")

            with col2:
                st.write("### ⚠️ Complaints")
                for c in complaints:
                    st.write(f"- {c}")

            # Similar Movies
            st.subheader("🎬 Similar Movies You Might Like")
            similar_movies = analysis_result.get("Comparison with Similar Movies", {})
            if similar_movies:
                for movie in similar_movies:
                    st.write(f"🎥 **{movie['Title']} ({movie['Year']})** - {movie['Brief explanation']}")

            # Final Verdict
            st.subheader("🎭 Final Verdict")
            st.info(analysis_result.get("Final Verdict", "No verdict available."))