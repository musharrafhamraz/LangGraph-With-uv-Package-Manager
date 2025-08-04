from mcp.server.fastmcp import FastMCP
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp=FastMCP("Weather")

@mcp.tool()
async def get_weather(location:str)->str:
    """Get the current weather for a location.
    
    Args:
        location: The city name and optionally the country code, e.g., 'London,UK' or 'New York'
        
    Returns:
        A string with the current weather information
    """
    logger.info(f"get_weather called with location: {location}")
    try:
        # Using OpenWeatherMap API with a free API key
        # You should replace this with your own API key for production use
        api_key = "4ef33a4b0d7b7b4f95e3ce9c90639d79"  # This is a sample key, replace with your own
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        
        logger.info(f"Making API request to: {url}")
        try:
            response = requests.get(url, timeout=10)  # Add a 10-second timeout
            logger.info(f"API response status code: {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error("Request timed out when connecting to OpenWeatherMap API")
            return provide_fallback_weather(location)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error when connecting to OpenWeatherMap API")
            return provide_fallback_weather(location)
        
        data = response.json()
        logger.debug(f"API response data: {data}")
        
        if response.status_code == 200:
            # Extract relevant weather information
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            # Format the response
            weather_info = f"Current weather in {location}:\n"
            weather_info += f"- Condition: {weather_description}\n"
            weather_info += f"- Temperature: {temperature}°C\n"
            weather_info += f"- Feels like: {feels_like}°C\n"
            weather_info += f"- Humidity: {humidity}%\n"
            weather_info += f"- Wind speed: {wind_speed} m/s"
            
            logger.info(f"Successfully retrieved weather for {location}")
            return weather_info
        else:
            error_msg = f"Error getting weather data: {data.get('message', 'Unknown error')}"
            logger.error(error_msg)
            return provide_fallback_weather(location)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.exception(f"Exception in get_weather: {error_msg}")
        return provide_fallback_weather(location)

def provide_fallback_weather(location):
    """Provide a fallback response when the weather API is unavailable."""
    logger.info(f"Providing fallback weather information for {location}")
    
    # Dictionary of common locations and their typical weather patterns
    fallback_info = {
        "london": "London typically has a temperate oceanic climate with cool winters and mild summers. It's known for its frequent rainfall throughout the year.",
        "new york": "New York has a humid continental climate with hot summers and cold winters. It experiences all four seasons distinctly.",
        "tokyo": "Tokyo has a humid subtropical climate with hot summers and mild winters. It has a rainy season in early summer.",
        "sydney": "Sydney has a temperate climate with warm summers and mild winters. It rarely experiences extreme temperatures.",
        "paris": "Paris has a temperate climate with mild summers and cool winters. Rainfall is moderate and fairly evenly distributed throughout the year.",
        "cairo": "Cairo has a hot desert climate with extremely hot summers and mild winters. Rainfall is rare.",
        "moscow": "Moscow has a humid continental climate with warm summers and very cold winters with significant snowfall.",
        "los angeles": "Los Angeles has a Mediterranean climate with warm, dry summers and mild, wet winters.",
        "mumbai": "Mumbai has a tropical climate with hot, humid summers and mild winters. It experiences heavy rainfall during the monsoon season.",
        "rio de janeiro": "Rio de Janeiro has a tropical savanna climate with hot, humid summers and mild, dry winters."
    }
    
    # Clean the location string for matching
    clean_location = location.lower().split(',')[0].strip()
    
    # Return specific information if available, or a generic message
    if clean_location in fallback_info:
        return f"Unable to retrieve real-time weather data for {location}. Here's some general information:\n\n{fallback_info[clean_location]}\n\nPlease try again later for current weather conditions."
    else:
        return f"Unable to retrieve weather data for {location}. The weather service is currently unavailable. Please try again later."

@mcp.tool()
async def get_forecast(location:str, days:int=3)->str:
    """Get the weather forecast for a location.
    
    Args:
        location: The city name and optionally the country code, e.g., 'London,UK'
        days: Number of days for the forecast (1-5)
        
    Returns:
        A string with the forecast information
    """
    logger.info(f"get_forecast called with location: {location}, days: {days}")
    try:
        # Limit days to a reasonable range
        days = min(max(1, days), 5)
        logger.info(f"Adjusted days parameter to: {days}")
        
        # Using OpenWeatherMap API with a free API key
        api_key = "4ef33a4b0d7b7b4f95e3ce9c90639d79"  # This is a sample key, replace with your own
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric&cnt={days*8}"
        
        logger.info(f"Making API request to: {url}")
        try:
            response = requests.get(url, timeout=10)  # Add a 10-second timeout
            logger.info(f"API response status code: {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error("Request timed out when connecting to OpenWeatherMap API")
            return "Unable to retrieve forecast data: connection timed out. Please try again later."
        except requests.exceptions.ConnectionError:
            logger.error("Connection error when connecting to OpenWeatherMap API")
            return "Unable to retrieve forecast data: connection error. Please check your internet connection and try again."
        
        data = response.json()
        logger.debug(f"API response data: {data}")
        
        if response.status_code == 200:
            forecast_info = f"Weather forecast for {location}:\n\n"
            
            # Group forecast by day
            current_day = ""
            day_forecasts = {}
            
            for item in data['list']:
                date = item['dt_txt'].split()[0]
                if date not in day_forecasts:
                    day_forecasts[date] = []
                day_forecasts[date].append(item)
            
            logger.info(f"Processed forecast data for {len(day_forecasts)} days")
            
            # Format each day's forecast
            for date, items in list(day_forecasts.items())[:days]:
                forecast_info += f"Date: {date}\n"
                
                # Get average values for the day
                temps = [item['main']['temp'] for item in items]
                avg_temp = sum(temps) / len(temps)
                
                # Get the most common weather condition
                conditions = [item['weather'][0]['description'] for item in items]
                most_common = max(set(conditions), key=conditions.count)
                
                forecast_info += f"- Average temperature: {avg_temp:.1f}°C\n"
                forecast_info += f"- Conditions: {most_common}\n\n"
            
            logger.info(f"Successfully retrieved forecast for {location}")
            return forecast_info
        else:
            error_msg = f"Error getting forecast data: {data.get('message', 'Unknown error')}"
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.exception(f"Exception in get_forecast: {error_msg}")
        return error_msg

if __name__=="__main__":
    mcp.run(transport="streamable-http")
