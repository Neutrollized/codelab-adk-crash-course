"""This module provides tools for weather and time related information."""
import httpx
import json


#-------------------
# settings
#-------------------
# SSL verification for requests
verify=True

#-------------------
# function tools
#-------------------
async def get_geocoding(city: str, country: str) -> dict:
    """Find geographical location given city and country
    Args:
        city: A string representing the name of the city.
        country: A string representing the name or country code of the country.
        verify: A boolean indicating whether to verify SSL certificates. Defaults to True.

    Returns:
        dict: Latitude and longitude of the city, country.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    # https://geocoding-api.open-meteo.com/v1/search?name={city}"
    query_params = {"name": city}

    try:
        # https://github.com/encode/httpx/issues/1028#issuecomment-645964226
        async with httpx.AsyncClient(verify=verify) as client:
            response = await client.get(url, params=query_params, timeout=10.0) # Added a timeout for robustness
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except httpx.TimeoutException as e:
        print(f"Timeout error: {e}")
        return None
    except httpx.RequestError as e:
        print(f"Error during request: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None

    try:
        json_data = response.json()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

    try:
        if "results" in json_data:
            for entry in json_data["results"]:
                if "country" in entry and entry["country"].lower() == country.lower():
                    return {"latitude": entry["latitude"], "longitude": entry["longitude"]}
                # "admin1" is usually the province/state/larger area that the city is in
                elif entry["admin1"].lower() == country.lower():
                    return {"latitude": entry["latitude"], "longitude": entry["longitude"]}
        return None  # If "results" key is missing or no matching country is found
    except KeyError as e:
        print(f"KeyError in parsing response: {e}")
        return None
    except TypeError as e: # Handle cases where entry might not be a dictionary
        print(f"TypeError in parsing response: {e}")
        return None


async def find_current_weather(latitude: float, longitude: float, verify: bool=True) -> float:
    """Find weather given geographical location
    Args:
        latitude: A float representing the latitude of a geographical location.
        longitude: A float representing the longitude of a geographical location.
        verify: A boolean indicating whether to verify SSL certificates. Defaults to True.

    Returns:
        float: Current temperature in Celsius, or None if an error occurs.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    # https://api.open-meteo.com/v1/forcast?latitude={latitude}&longitude={longitude}&current=temperature_2m"
    # Use 'params' for cleaner and safer URL query building
    query_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m"
    }

    try:
        # https://github.com/encode/httpx/issues/1028#issuecomment-645964226
        async with httpx.AsyncClient(verify=verify) as client:
            response = await client.get(url, params=query_params, timeout=10.0) # Added a timeout for robustness
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except httpx.TimeoutException as e:
        print(f"Timeout error: {e}")
        return None
    except httpx.RequestError as e:
        print(f"Error during HTTP request: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None

    try:
        json_data = response.json() # httpx response objects have a .json() method
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

    try:
        # Safely access nested dictionary keys
        return json_data["current"]["temperature_2m"]
    except KeyError as e:
        print(f"KeyError in parsing weather data: Missing key {e}")
        return None
    except TypeError as e:
        print(f"TypeError in parsing weather data: {e}")
        return None


async def convert_c2f(c_temp: float) -> float:
    """Convert Celsius to Fahrenheit
    Args:
        c_temp: A float representing the temp in Celsius

    Returns:
        float: Temperature in Fahrenheit
    """
    f_temp = (c_temp * 9/5) + 32
    return f_temp


async def convert_f2c(f_temp: float) -> float:
    """Convert Fahrenheit to Celsius
    Args:
        f_temp: A float representing the temp in Fahrenheit

    Returns:
        float: Temperature in Celsius
    """
    c_temp = (f_temp - 32) * (5/9)
    return c_temp
