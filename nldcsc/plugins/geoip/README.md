# GEOIP PLUGIN

IP GEOLOCATION API provides country, city, state, province, local currency, latitude and longitude, company detail, ISP lookup, language, zip code, country calling code, time zone, current time, sunset and sunrise time, moonset and moonrise time from any IPv4 and IPv6 address in REST, JSON and XML format over HTTPS.

[Documentation](https://ipgeolocation.io/documentation.html)

Expected environment variables and defaults

```python
# IP GEOLOCATION ACTIVATION AND API KEY 
IPGEOLOCATION_ENABLE = os.getenv("IPGEOLOCATION_ENABLE", False)
IPGEOLOCATION_API_KEY = os.getenv("IPGEOLOCATION_API_KEY", None)
```
