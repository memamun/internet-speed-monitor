import psutil
from typing import Dict, Any


class AdapterProvider:
    """Provides information about available network adapters on the system."""

    @staticmethod
    def get_interfaces() -> Dict[str, Dict[str, Any]]:
        """
        Retrieves a dictionary of network interfaces with their statuses.
        Returns mapped data including isup (is the interface up) and speed.
        """
        interfaces = {}
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()

            for name, stat in stats.items():
                if name == "Loopback Pseudo-Interface 1" or name == "lo":
                    continue

                mac_address = ""
                # Try to find a MAC address for the interface
                if name in addrs:
                    for addr in addrs[name]:
                        # AddressFamily.AF_LINK (or psutil.AF_LINK) represents MAC layer
                        if addr.family == psutil.AF_LINK:
                            mac_address = addr.address

                interfaces[name] = {
                    "isup": stat.isup,
                    "mtu": stat.mtu,
                    "speed": stat.speed,  # Speed in MBps, 0 means unknown
                    "mac": mac_address
                }
        except Exception:
            pass

        return interfaces
