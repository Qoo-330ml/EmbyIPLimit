import re
import socket


def extract_ip_address(remote_endpoint):
    """智能提取IP地址，支持IPv4和IPv6"""
    if not remote_endpoint:
        return ""

    ipv6_pattern = r'^\[(.*?)\](?::(\d+))?$|^([^%]:*)(?:%[^:]*)?:(?:(\d+))?$'
    match = re.match(ipv6_pattern, remote_endpoint)

    if match:
        if match.group(1):
            return match.group(1)
        ip_part = match.group(3)
        if ip_part and is_ipv6(ip_part):
            return ip_part
        if ip_part:
            return ip_part

    parts = remote_endpoint.split(':')
    if len(parts) >= 8:
        potential_ipv6 = ':'.join(parts[:8])
        if is_ipv6(potential_ipv6):
            return potential_ipv6

    ipv4_pattern = r'^(\d+\.\d+\.\d+\.\d+):(\d+)$'
    match = re.match(ipv4_pattern, remote_endpoint)
    if match:
        return match.group(1)

    return remote_endpoint.split('%')[0]


def is_ipv6(ip_str):
    try:
        socket.inet_pton(socket.AF_INET6, ip_str)
        return True
    except (socket.error, ValueError):
        return False


def is_ipv4(ip_str):
    try:
        socket.inet_pton(socket.AF_INET, ip_str)
        return True
    except (socket.error, ValueError):
        return False


def get_ipv6_prefix(ipv6_address, prefix_length):
    if not ipv6_address or not is_ipv6(ipv6_address):
        return ipv6_address

    try:
        binary_data = socket.inet_pton(socket.AF_INET6, ipv6_address)
        prefix_bytes = prefix_length // 8
        if prefix_length % 8 != 0:
            prefix_bytes += 1

        prefix_binary = binary_data[:prefix_bytes]
        prefix_segments = prefix_length // 16
        if prefix_length % 16 != 0:
            prefix_segments += 1

        prefix_address = socket.inet_ntop(socket.AF_INET6, prefix_binary.ljust(16, b'\x00'))
        segments = prefix_address.split(':')
        prefix_segments = segments[:prefix_segments]
        if len(prefix_segments) < 8:
            prefix_segments.append('')
        return ':'.join(prefix_segments)
    except Exception:
        return ipv6_address


def is_same_network(ip1, ip2, ipv6_prefix_length):
    if ip1 == ip2:
        return True

    if is_ipv6(ip1) and is_ipv6(ip2):
        prefix1 = get_ipv6_prefix(ip1, ipv6_prefix_length)
        prefix2 = get_ipv6_prefix(ip2, ipv6_prefix_length)
        return prefix1 == prefix2

    if is_ipv4(ip1) and is_ipv4(ip2):
        return ip1 == ip2

    return False
