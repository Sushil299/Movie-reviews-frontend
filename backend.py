# -*- coding: utf-8 -*-
"""backend

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1TiA6-37RYxY1T4RB18XXJ009WhLO_oFm
"""

import os
import asyncpraw
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import json
import asyncio
from asyncio import sleep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API keys from environment variables
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize APIs
reddit = asyncpraw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="StockScraper"
)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

INDIAN_MOVIE_SUBREDDITS = [
    "bollywood", "IndianCinema", "tollywood", "kollywood", "MalayalamMovies",
    "Lollywood", "BollyBlindsNGossip", "bollywoodmemes", "India", "AskIndia",
    "movies", "moviecritic", "shittymoviedetails", "netflix", "boxoffice"
]

# FastAPI App
app = FastAPI()

# Add CORS middleware to allow requests from any origin (important for frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def home():
    return {"message": "Movie Review Backend is Running!"}

@app.get("/search_reddit")
async def search_reddit(movie_name: str, days: int = 60) -> Dict[str, Any]:
    comments, posts = [], []
    total_posts = 0
    time_threshold = datetime.utcnow() - timedelta(days=days)

    for subreddit_name in INDIAN_MOVIE_SUBREDDITS:
        try:
            # Add debug logging for authentication check
            logger.info(f"Searching subreddit: {subreddit_name} for movie: {movie_name}")

            # Create subreddit instance
            subreddit = await reddit.subreddit(subreddit_name)

            # Create search generator
            search_generator = subreddit.search(movie_name, time_filter="month", limit=10)

            # Collect search results into a list to verify we have data
            search_results = []
            async for result in search_generator:
                search_results.append(result)

            # Check if we found any results
            if not search_results:
                logger.info(f"No results found for {movie_name} in {subreddit_name}")
                continue

            # Process the results
            for post in search_results:
                post_time = datetime.fromtimestamp(post.created_utc)
                if post_time < time_threshold or post.score < 50:
                    continue

                total_posts += 1
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "url": f"https://www.reddit.com{post.permalink}",
                    "num_comments": post.num_comments
                })

                # Make sure to handle comments asynchronously
                try:
                    await post.comments.replace_more(limit=5)
                    # Get comment list ONLY if post.comments is not None
                    if post.comments is None:
                        logger.warning(f"No comments object for post in {subreddit_name}")
                        continue

                    # Safely get comments list - handle possible None cases
                    try:
                        comment_list = post.comments.list()
                        if comment_list is None:
                            logger.warning(f"Comment list is None for post in {subreddit_name}")
                            continue
                    except Exception as list_err:
                        logger.warning(f"Error getting comment list for post in {subreddit_name}: {str(list_err)}")
                        continue

                    # Now process comments safely
                    for comment in comment_list[:20]:
                        # Check if comment is valid and has required attributes
                        if (comment is not None and
                            hasattr(comment, 'body') and
                            hasattr(comment, 'score') and
                            hasattr(comment, 'author') and
                            hasattr(comment, 'permalink')):

                            if len(comment.body.strip()) > 30 and comment.score >= 20:
                                comments.append({
                                    "text": comment.body,
                                    "score": comment.score,
                                    "author": str(comment.author),
                                    "url": f"https://www.reddit.com{comment.permalink}"
                                })
                except Exception as comment_err:
                    logger.warning(f"Error processing comments for post in {subreddit_name}: {str(comment_err)}")
                    continue

        except Exception as e:
            logger.warning(f"Error searching subreddit {subreddit_name}: {str(e)}")
            # Add a delay between requests to avoid rate limiting
            await sleep(1)
            continue

        # Add a small delay between subreddit searches to avoid rate limiting
        await sleep(0.5)

    # Sort comments by score
    comments.sort(key=lambda x: x["score"], reverse=True)

    # Log the results for debugging
    logger.info(f"Found {len(posts)} posts and {len(comments)} comments for {movie_name}")

    return {"posts": posts, "comments": comments[:50], "total_posts": total_posts}

@app.get("/analyze")
async def analyze_with_gemini(movie_name: str) -> Dict[str, Any]:
    try:
        # Get Reddit data
        reddit_data = await search_reddit(movie_name, days=60)

        # Log the data for debugging
        logger.info(f"Reddit data for {movie_name}: {len(reddit_data['posts'])} posts, {len(reddit_data['comments'])} comments")

        # Check if we have enough data to analyze
        if not reddit_data["posts"] and not reddit_data["comments"]:
            logger.warning(f"Insufficient data found for movie: {movie_name}")
            return {
                "title": f"{movie_name} Analysis (Insufficient Data)",
                "analysis": {
                    "1. TL;DR Summary": f"There isn't enough online discussion available to form an analysis of {movie_name}.",
                    "2. Overall Sentiment Analysis": {
                        "positivePercentage": 0,
                        "negativePercentage": 0,
                        "neutralPercentage": 0,
                        "keyPhrases": [],
                        "confidenceLevel": "low"
                    },
                    "3. Summary of Audience Reactions": "Insufficient data to summarize audience reactions.",
                    "4. Key Aspects Discussed": {
                        "Acting": {"score": "N/A", "explanation": "Insufficient data"},
                        "Story": {"score": "N/A", "explanation": "Insufficient data"},
                        "Direction": {"score": "N/A", "explanation": "Insufficient data"},
                        "Music": {"score": "N/A", "explanation": "Insufficient data"},
                        "Cinematography": {"score": "N/A", "explanation": "Insufficient data"},
                        "Special Effects": {"score": "N/A", "explanation": "Insufficient data"}
                    },
                    "5. Common Praise & Complaints": {
                        "praise": [],
                        "complaints": []
                    },
                    "6. Comparison with Similar Movies": [],
                    "7. Final Verdict": {
                        "whoWouldEnjoy": "Insufficient data",
                        "whoMightNotEnjoy": "Insufficient data",
                        "theaterOrStreaming": "Insufficient data"
                    }
                }
            }

        # Prepare text for analysis
        posts_text = "\n\n".join([f"Post: {p['title']}" for p in reddit_data["posts"]])
        comments_text = "\n\n".join([f"Comment: {c['text']}" for c in reddit_data["comments"][:30]])

        prompt = f"""
        Based on Reddit discussions and comments about the movie "{movie_name}", analyze the following data to help users decide whether to watch it.

        POSTS:
        {posts_text}

        COMMENTS:
        {comments_text}

        If limited data is available (fewer than 10 meaningful comments/posts), please note this limitation.

        Create a movie analysis in the exact JSON format below. Do not deviate from this structure:

        {{
          "title": "{movie_name} Movie Analysis Based on Reddit Discussions",
          "analysis": {{
            "1. TL;DR Summary": "A concise 1-2 sentence verdict on the movie.",
            "2. Overall Sentiment Analysis": {{
              "positivePercentage": 0,
              "negativePercentage": 0,
              "neutralPercentage": 0,
              "keyPhrases": [
                "key phrase 1",
                "key phrase 2",
                "key phrase 3",
                "key phrase 4",
                "key phrase 5"
              ],
              "confidenceLevel": "high/medium/low"
            }},
            "3. Summary of Audience Reactions": "A 5-7 sentence overview of common praises and criticisms. Indicate if opinions are polarized or generally consistent. Note if analysis contains potential spoilers.",
            "4. Key Aspects Discussed": {{
              "Acting": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }},
              "Story": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }},
              "Direction": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }},
              "Music": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }},
              "Cinematography": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }},
              "Special Effects": {{
                "score": 0,
                "explanation": "1-2 sentence explanation"
              }}
            }},
            "5. Common Praise & Complaints": {{
              "praise": [
                "praise 1",
                "praise 2",
                "praise 3",
                "praise 4",
                "praise 5"
              ],
              "complaints": [
                "complaint 1",
                "complaint 2",
                "complaint 3",
                "complaint 4",
                "complaint 5"
              ]
            }},
            "6. Comparison with Similar Movies": [
              {{
                "title": "Movie 1",
                "year": 0000,
                "similarity": "Brief explanation of similarity (theme, director, style, actors)",
                "rating": "Whether it's rated better/worse than the movie in question"
              }},
              {{
                "title": "Movie 2",
                "year": 0000,
                "similarity": "Brief explanation of similarity (theme, director, style, actors)",
                "rating": "Whether it's rated better/worse than the movie in question"
              }},
              {{
                "title": "Movie 3",
                "year": 0000,
                "similarity": "Brief explanation of similarity (theme, director, style, actors)",
                "rating": "Whether it's rated better/worse than the movie in question"
              }}
            ],
            "7. Final Verdict": {{
              "whoWouldEnjoy": "Description of who would enjoy this movie",
              "whoMightNotEnjoy": "Description of who might not enjoy it",
              "theaterOrStreaming": "Recommendation on whether to watch in theaters or via streaming"
            }}
          }}
        }}

        Provide scores as integers from 1-10. If a category doesn't have enough data, use "N/A" for the score.
        Replace all placeholders with actual analysis based on the provided data.
        Make sure the response is valid JSON with all properties exactly as shown.
        """

        # Generate analysis with Gemini
        logger.info(f"Sending request to Gemini for movie: {movie_name}")
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }

        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Parse the response
        try:
            response_text = response.text

            # Log the raw response for debugging
            logger.info(f"Raw Gemini response first 200 chars: {response_text[:200]}...")

            # Extract JSON from response
            json_content = ""

            # Try different methods to extract the JSON
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].split("```")[0].strip()
            else:
                # Try to find a JSON object in the text
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1:
                    json_content = response_text[start:end+1].strip()
                else:
                    json_content = response_text.strip()

            # Parse the JSON
            try:
                analysis_json = json.loads(json_content)
                return analysis_json
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decode error: {str(json_err)}")
                logger.error(f"Attempted to parse: {json_content[:500]}...")

                # Return a fallback response
                return {
                    "title": f"{movie_name} Analysis (JSON Parsing Error)",
                    "analysis": {
                        "1. TL;DR Summary": f"Unable to generate a proper analysis for {movie_name} due to technical issues.",
                        "2. Overall Sentiment Analysis": {
                            "positivePercentage": 0,
                            "negativePercentage": 0,
                            "neutralPercentage": 0,
                            "keyPhrases": ["error", "parsing", "technical issue"],
                            "confidenceLevel": "low"
                        },
                        "3. Summary of Audience Reactions": "Error parsing AI response. Raw response may contain valuable data but couldn't be structured properly.",
                        "4. Key Aspects Discussed": {
                            "Acting": {"score": "N/A", "explanation": "Error parsing response"},
                            "Story": {"score": "N/A", "explanation": "Error parsing response"},
                            "Direction": {"score": "N/A", "explanation": "Error parsing response"},
                            "Music": {"score": "N/A", "explanation": "Error parsing response"},
                            "Cinematography": {"score": "N/A", "explanation": "Error parsing response"},
                            "Special Effects": {"score": "N/A", "explanation": "Error parsing response"}
                        },
                        "5. Common Praise & Complaints": {
                            "praise": [],
                            "complaints": ["Unable to process response"]
                        },
                        "6. Comparison with Similar Movies": [],
                        "7. Final Verdict": {
                            "whoWouldEnjoy": "Error parsing response",
                            "whoMightNotEnjoy": "Error parsing response",
                            "theaterOrStreaming": "Error parsing response"
                        }
                    }
                }

        except Exception as parse_err:
            logger.error(f"Error parsing Gemini response: {str(parse_err)}")
            logger.error(f"Raw response: {response_text[:500]}...")  # Log first 500 chars

            # Return a fallback response
            return {
                "title": f"{movie_name} Analysis (Error)",
                "analysis": {
                    "1. TL;DR Summary": f"Unable to generate a proper analysis for {movie_name} due to technical issues.",
                    "2. Overall Sentiment Analysis": {
                        "positivePercentage": 0,
                        "negativePercentage": 0,
                        "neutralPercentage": 0,
                        "keyPhrases": [],
                        "confidenceLevel": "low"
                    },
                    "3. Summary of Audience Reactions": "Error processing AI response.",
                    "4. Key Aspects Discussed": {
                        "Acting": {"score": "N/A", "explanation": "Error processing response"},
                        "Story": {"score": "N/A", "explanation": "Error processing response"},
                        "Direction": {"score": "N/A", "explanation": "Error processing response"},
                        "Music": {"score": "N/A", "explanation": "Error processing response"},
                        "Cinematography": {"score": "N/A", "explanation": "Error processing response"},
                        "Special Effects": {"score": "N/A", "explanation": "Error processing response"}
                    },
                    "5. Common Praise & Complaints": {
                        "praise": [],
                        "complaints": []
                    },
                    "6. Comparison with Similar Movies": [],
                    "7. Final Verdict": {
                        "whoWouldEnjoy": "Error processing response",
                        "whoMightNotEnjoy": "Error processing response",
                        "theaterOrStreaming": "Error processing response"
                    }
                }
            }

    except Exception as e:
        logger.error(f"Error in analyze_with_gemini: {str(e)}")
        return {
            "title": f"{movie_name} Analysis (General Error)",
            "analysis": {
                "1. TL;DR Summary": f"An error occurred while analyzing {movie_name}.",
                "2. Overall Sentiment Analysis": {
                    "positivePercentage": 0,
                    "negativePercentage": 0,
                    "neutralPercentage": 0,
                    "keyPhrases": [],
                    "confidenceLevel": "low"
                },
                "3. Summary of Audience Reactions": f"Error: {str(e)}",
                "4. Key Aspects Discussed": {
                    "Acting": {"score": "N/A", "explanation": "Error occurred"},
                    "Story": {"score": "N/A", "explanation": "Error occurred"},
                    "Direction": {"score": "N/A", "explanation": "Error occurred"},
                    "Music": {"score": "N/A", "explanation": "Error occurred"},
                    "Cinematography": {"score": "N/A", "explanation": "Error occurred"},
                    "Special Effects": {"score": "N/A", "explanation": "Error occurred"}
                },
                "5. Common Praise & Complaints": {
                    "praise": [],
                    "complaints": []
                },
                "6. Comparison with Similar Movies": [],
                "7. Final Verdict": {
                    "whoWouldEnjoy": "Error occurred",
                    "whoMightNotEnjoy": "Error occurred",
                    "theaterOrStreaming": "Error occurred"
                }
            }
        }

# Run the app using `uvicorn backend:app --host 0.0.0.0 --port 8000`