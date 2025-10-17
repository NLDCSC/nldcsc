import os

from nldcsc.plugins.geoip.api import GeoIp


class GeoIpTest:
    def test_is_valid_ip(self):
        os.environ["IPGEOLOCATION_ENABLE"] = "True"
        os.environ["IPGEOLOCATION_API_KEY"] = "tests"
        gi = GeoIp()

        assert all(gi.is_valid_ip(ip) for ip in valid_ips) == True
        assert all(not gi.is_valid_ip(ip) for ip in invalid_ips) == True


# TEST DATA

valid_ips = [
    # Valid IPv4 Addresses
    "192.168.1.1",  # Typical private IP address
    "10.0.0.255",  # Another private IP address
    "172.16.0.1",  # Yet another private IP address
    "192.168.0.1",  # Common private IP address in a home network
    "10.1.1.1",  # Another private IP address
    "172.31.255.255",  # Private IP address (highest in the range)
    "169.254.100.1",  # Link-local address (APIPA)
    "192.168.100.100",  # Common private IP address
    "255.255.255.255",  # Broadcast address
    "127.0.0.1",  # Loopback address
    "8.8.8.8",  # Google's public DNS server
    "1.1.1.1",  # Cloudflare's public DNS server
    "8.8.4.4",  # Google's public DNS server (alternative)
    "150.100.50.25",  # Public IP address
    "192.0.2.146",  # Example IP address (Test Net)
    "203.0.113.1",  # Another example IP address (Test Net)
    "203.0.113.5",  # Example IP address (Test Net)
    "192.0.2.1",  # Another example IP address (Test Net)
    "255.255.0.0",  # Class B subnet mask address
    # Valid IPv6 Addresses
    "::1",  # Loopback address in IPv6
    "::",  # Unspecified address in IPv6
    "::ffff:192.168.1.1",  # IPv4-mapped IPv6 address
    "2001:0db8::",  # Compressed format with only one hextet
    "abcd:ef01:2345:6789:abcd:ef01:2345:6789",  # Full representation
    "2001:0db8:85a3:0000:0000:8a2e:0370:7334",  # Full representation
    "2001:db8:abcd:0012:0000:0000:0000:0001",  # Example IPv6 address
    "2001:db8:1234:5678:abcd:ef01:2345:6789",  # Full representation
    "2607:f8b0:4005:805::200e",  # Google's IPv6 address
    "fe80::1ff:fe23:4567:890a",  # Link-local address
    "ff00::",  # Multicast address
]

invalid_ips = [
    # Invalid IPv4 Addresses
    "256.256.256.256",  # Invalid: Out of range
    "192.168.1.999",  # Invalid: Last octet out of range
    "172.16.0.300",  # Invalid: Last octet out of range
    "192.168.0.1.1",  # Invalid: Too many octets
    "192.168.1",  # Invalid: Not enough octets
    "10.0.0.-1",  # Invalid: Negative octet
    "10.0.0.256",  # Invalid: Out of range
    "123.045.067.089",  # Invalid: Leading zeros
    "192.168.1.01",  # Invalid: Leading zeros
    "192.168.1.abc",  # Invalid: Non-numeric characters
    # Invalid IPv6 Addresses
    "2001:db8:1234:5678:abcd:ef01:2345:6789:abcd",  # Invalid: Too many hextets
    "2001:db8:::1",  # Invalid: Multiple double colons
    "2001:db8:1234:5678:abcd:ef01:ghij",  # Invalid: Non-hexadecimal character
    "2001:db8:1234:5678:abcd:ef01:2345:6789:abcd",  # Invalid: Too many hextets
    "2001:db8:1234:5678:abcd:ef01:2345:678g",  # Invalid: Non-hex character
    "abcd:ef01:2345:6789:abcd:ef01:2345:6789:",  # Invalid: Trailing colon
    "::g",  # Invalid: Non-hexadecimal character
    "2001:0db8:85a3:0000:0000:8a2e:0370:7334g",  # Invalid: Non-hexadecimal character
]
