import pytest
from api.validators import validate_ip_address, validate_state, validate_hostname


class TestIPAddressValidation:

    def test_valid_ipv4(self):
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "0.0.0.0",
            "255.255.255.255",
            "127.0.0.1",
        ]
        for ip in valid_ips:
            assert validate_ip_address(ip) is True, f"Should be valid: {ip}"

    def test_valid_ipv6(self):
        valid_ips = [
            "::1",
            "fe80::1",
            "2001:db8::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "::ffff:192.168.1.1",
        ]
        for ip in valid_ips:
            assert validate_ip_address(ip) is True, f"Should be valid: {ip}"

    def test_invalid_ip_addresses(self):
        invalid_ips = [
            "invalid",
            "192.168.1",
            "192.168.1.1.1",
            "256.0.0.1",
            "192.168.1.999",
            "",
            "localhost",
            "192.168.1.1:8080",
        ]
        for ip in invalid_ips:
            assert validate_ip_address(ip) is False, f"Should be invalid: {ip}"


class TestStateValidation:

    def test_valid_states(self):
        valid_states = ["active", "offline", "retired"]
        for state in valid_states:
            assert validate_state(state) is True, f"Should be valid: {state}"

    def test_invalid_states(self):
        invalid_states = [
            "running",
            "stopped",
            "Active",
            "OFFLINE",
            "",
            "inactive",
        ]
        for state in invalid_states:
            assert validate_state(state) is False, f"Should be invalid: {state}"


class TestHostnameValidation:

    def test_valid_simple_hostnames(self):
        valid_hostnames = [
            "a",
            "server1",
            "web-server",
            "my-host-name",
            "server123",
            "123server",
            "a1",
            "1a",
        ]
        for hostname in valid_hostnames:
            assert validate_hostname(hostname) is True, f"Should be valid: {hostname}"

    def test_valid_fqdn_hostnames(self):
        valid_hostnames = [
            "server.example.com",
            "web-01.us-east-1.example.com",
            "db.prod.internal",
            "a.b.c",
            "server1.server2.server3",
        ]
        for hostname in valid_hostnames:
            assert validate_hostname(hostname) is True, f"Should be valid: {hostname}"

    def test_invalid_hostnames_leading_trailing_chars(self):
        invalid_hostnames = [
            "-server",
            "server-",
            ".server",
            "server.",
            "-",
            ".",
        ]
        for hostname in invalid_hostnames:
            assert validate_hostname(hostname) is False, f"Should be invalid: {hostname}"

    def test_invalid_hostnames_consecutive_dots(self):
        invalid_hostnames = [
            "server..name",
            "a..b",
            "server...name",
        ]
        for hostname in invalid_hostnames:
            assert validate_hostname(hostname) is False, f"Should be invalid: {hostname}"

    def test_invalid_hostnames_special_chars(self):
        invalid_hostnames = [
            "server name",
            "server_name",
            "server@name",
            "server#name",
            "server!",
        ]
        for hostname in invalid_hostnames:
            assert validate_hostname(hostname) is False, f"Should be invalid: {hostname}"

    def test_hostname_length_limits(self):
        # Max total length is 255 (must use valid labels of max 63 chars each)
        # Create a 255 char hostname: 63 + 1 + 63 + 1 + 63 + 1 + 63 = 255
        long_valid = "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 63
        assert len(long_valid) == 255
        assert validate_hostname(long_valid) is True

        # 256 chars should fail
        too_long = long_valid + "e"
        assert validate_hostname(too_long) is False

        # Empty hostname
        assert validate_hostname("") is False

        # Each label max 63 chars
        assert validate_hostname("a" * 63) is True
        assert validate_hostname("a" * 63 + ".b") is True
        assert validate_hostname("a" * 64) is False  # Single label > 63 chars

    def test_hostname_label_rules(self):
        # Labels must start and end with alphanumeric
        assert validate_hostname("a-b") is True
        assert validate_hostname("a--b") is True  # Consecutive hyphens in middle is OK
        assert validate_hostname("-ab") is False
        assert validate_hostname("ab-") is False

        # Each label in FQDN follows same rules
        assert validate_hostname("ok.ok") is True
        assert validate_hostname("-bad.ok") is False
        assert validate_hostname("ok.-bad") is False
        assert validate_hostname("ok.bad-") is False

    def test_single_character_labels(self):
        assert validate_hostname("a") is True
        assert validate_hostname("a.b") is True
        assert validate_hostname("a.b.c") is True
        assert validate_hostname("1") is True
        assert validate_hostname("1.2.3") is True
