import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from serpapi import GoogleSearch
from dotenv import load_dotenv
# Initialize FastMCP server
load_dotenv()
mcp = FastMCP("KIVA")
SERP_API_KEY=os.getenv("SERP_API_KEY")
# https://serpapi.com/search?engine=google&q=shoes&location=United+States&hl=en&api_key=81a800686d78bc3bea4317876995f75043ae3219d64f4e45cbbe8940526cc3ee

@mcp.tool()
async def get_related_keywords(keyword: str, country: str = 'US', lang: str = 'en') -> str:
    """Get related keywords for a given keyword, country, and language.

    Args:
        keyword: The main keyword to find related keywords for
        country: Country code (default is 'US')
        lang: Language code (default is 'en')
    """

    print("-======coming here=========")
    params = {
    "engine": "google",
    "q": keyword,
    "hl": lang,
    "gl": country,
    "google_domain": "google.com",
    "num": "10",
    "start": "10",
    "safe": "active",
    "api_key": SERP_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results["related_searches"]

    print("========================organic_results========================",organic_results)
    related_queries = [item["query"] for item in organic_results]
    # Example usage of the parameters to avoid unused variable warnings
    return "\n---\n".join(related_queries)

# @mcp.tool()
# async def get_serp_intent(keyword: str, country: str = 'US', lang: str = 'en') -> str:
#     """Get SERP intent for a given keyword, country, and language.
#     Args:
#         keyword: The main keyword to find SERP intent for
#         country: Country code (default is 'US')
#         lang: Language code (default is 'en')
#     """
#     # First get the forecast grid endpoint

#     forecasts = []
#     for period in periods[:5]:  # Only show next 5 periods
#         forecast = f"""
#             {period['name']}:
#             Temperature: {period['temperature']}°{period['temperatureUnit']}
#             Wind: {period['windSpeed']} {period['windDirection']}
#             Forecast: {period['detailedForecast']}
#             """
#         forecasts.append(forecast)

#     return "\n---\n".join(forecasts)   
if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio') 