# Get weather data from various online sources
# -*- coding: utf-8 -*-

import requests
from wrappers import *


@plugin
class yweather:
    @command("weather")
    def weather(self, message):
        """Get the current condition in a given location, from the Yahoo! Weather Service
        """
        w = self.get_yahoo_weather(message.data)
        if isinstance(w, dict):
            return message.reply(data=w, 
                text="Weather for {0[city]}, {0[country]}: {0[condition]}, {0[temperature]}. Wind Speed: {0[wind_speed]} ({0[wind_direction]}), Wind Chill: {0[wind_chill]}. Visibility {0[visibility]}. High Temp: {0[high]}°C, Low Temp: {0[low]}°C. Sunrise: {0[sunrise]}, Sunset: {0[sunset]}.".format(w)
            )
        else:
            return message.reply(data=w, text=w)

    @command("forecast")
    def forecast(self, message):
        """Get the 5 day forcast for a given location, from the Yahoo! Weather Service
        """
        w = self.get_yahoo_weather(message.data)
        if isinstance(w, dict):
            return message.reply(data=w['forecast'], text="; ".join(["{0[day]}: {0[condition]}. High: {0[high]}, Low: {0[low]}.".format(x) for x in w['forecast']]))
        else:
            return message.reply(data=w, text=w)

    def get_yahoo_weather(self, place):
        if not place:
            raise Exception("You must provide a place name.")
        # Use Yahoo's yql to build the query
        url = 'https://query.yahooapis.com/v1/public/yql?q=select * from weather.forecast where woeid in(select woeid from geo.places(1) where text="' + place  + '") and u="c"&format=json'

        # Fetch the results
        r = requests.get(url)
        json = r.json()
        result = json['query']['results']
        if not result:
            return "No weather could be found for " + place + "."

        # Read the pertinant parts of the result, and format them nicely.
        channel     = result['channel']
        city        = channel['location']['city'] 
        country     = channel['location']['country']
        region      = channel['location']['region']

        high        = channel['item']['forecast'][0]['high']
        low         = channel['item']['forecast'][0]['low']

        windChill   = "{0}°{1}".format(channel['wind']['chill'], channel['units']['temperature'])
        windDir     = "{0:03d}deg".format(int(channel['wind']['direction']))
        windSpeed   = "{0} {1}".format(channel['wind']['speed'], channel['units']['speed'])

        humidity    = "{0}%".format(channel['atmosphere']['humidity'])
        pressure    = "{0}{1}".format(channel['atmosphere']['pressure'], channel['units']['pressure'])
        rising      = channel['atmosphere']['rising']
        visibility  = "{0}{1}".format(channel['atmosphere']['visibility'], channel['units']['distance'])

        sunrise     = channel['astronomy']['sunrise']
        sunset      = channel['astronomy']['sunset']

        condition   = channel['item']['condition']['text']
        temperature = "{0}°{1}".format(channel['item']['condition']['temp'], channel['units']['temperature'])

        forecast   = []
        for pred in channel['item']['forecast']:
            c = {"day": pred['day'],
                 "condition": pred['text'],
                 "high": "{0}°{1}".format(pred['high'], channel['units']['temperature']),
                 "low": "{0}°{1}".format(pred['low'], channel['units']['temperature'])}
            forecast.append(c)
        return {"city":city,
                "country":country,
                "region":region,
                "high":high,
                "low":low,
                "temperature": temperature,
                "wind_chill":windChill,
                "wind_direction":windDir,
                "wind_speed":windSpeed,
                "humidity":humidity,
                "pressure":pressure,
                "rising":rising,
                "visibility":visibility,
                "sunrise":sunrise,
                "sunset":sunset,
                "condition":condition,
                "forecast":forecast
                }

@plugin
class pollen:
    @command("pollen")
    def pollen(self, message):
        """Get the pollen index for a given location
        """
        if not message:
            raise Exception("You must provide a place name.")
        # Use Yahoo's yql to build the query
        yurl = 'https://query.yahooapis.com/v1/public/yql?q=select woeid from geo.places(1) where text = "' + message.data + '"&format=json'

        # Fetch the results
        r = requests.get(yurl)
        json = r.json()

        if not json['query']['results']:
            return "Could not find " + place + "."
        
        woeid = json['query']['results']['place']['woeid']
        print(woeid)

        purl = "https://pollencheck.p.mashape.com/api/1/forecasts/" + woeid
        headers = {
            "X-Mashape-Key": "O6cwEp209Jmsh614NhNE6DpXIUKhp1npOMrjsnvWzdpgHYgzob",
            "Accept": "application/json"
        }
        pollen_data = requests.get(purl, headers=headers)
        p_json = pollen_data.json()
        
        if not p_json:
            raise Exception("Could not get data for '" + message.data + "', try a large city.")

        return message.reply(data=p_json, text="Total pollen count: {0[maxLevel]}".format(p_json['periods'][0]['combined']))
        

@plugin
class forecast_io:
    @command("whereis")
    def whereis(self, message):
        """Get the latitude and longitdue of a given place
        """
        if not message:
            raise Exception("You must provide a place name.")
        
        ll = self.latlong(message.data)
        if isinstance(ll, dict):
            return message.reply(data=ll, text="Latitude: {}, Longitude: {}".format(ll['latitude'], ll['longitude']))
        else:
            return message.reply(data=ll, text=ll)

    @command("condition")
    def condition(self, message):
        """Get the current weather using the https://developer.forecast.io/docs/v2 API.
        """
        if not message:
            raise Exception("You must provide a place name.")

        w = self.get_forecast_io_weather(message.data)
        if isinstance(w, dict):
            return message.reply(data=w, 
                text="Current condition for {1}: {0[summary]} P({0[precipProbability]}) probability of precipitation. \
{0[temperature]}°C, feels like {0[apparentTemperature]}°C. Dew Point: {0[dewPoint]}°C. \
Humidity: {0[humidity]}. Wind Speed: {0[windSpeed]}mph bearing {0[windBearing]:03d}. \
Cloud Cover: {0[cloudCover]}. Pressure: {0[pressure]}mb. Ozone: {0[ozone]}.".format(w['currently'], message.data))
        else:
            return message.reply(data=w, text=w)


    def latlong(self, place):
        # Use Yahoo's yql to build the query
        if not place:
            raise Exception("You must provide a place name.")

        url = 'https://query.yahooapis.com/v1/public/yql?q=select centroid from geo.places(1) where text = "' + place + '"&format=json'

        # Fetch the results
        r = requests.get(url)
        json = r.json()

        if not json['query']['results']:
            return "Could not find " + place + "."

        return json['query']['results']['place']['centroid']

    def get_forecast_io_weather(self, place):
        if not message:
            raise Exception("You must provide a place name.")

        ll = self.latlong(place)
        
        # TODO: yeild an error
        if not isinstance(ll, dict):
            return ll
        
        # Build a forecast IO request string. TODO: Remove API key and regenerate it
        url = 'https://api.forecast.io/forecast/da05193c059f48ff118de841ccb7cd92/' + ll['latitude'] + "," + ll['longitude'] + "?units=uk"

        # Fetch the results
        r = requests.get(url)
        json = r.json()
        return json
