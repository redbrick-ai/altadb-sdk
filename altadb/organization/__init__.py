"""Organization class."""

from typing import Optional
import platform

from altadb.common.context import AltaDBContext


class AltaDBOrganization:
    """
    Representation of RedBrick organization.

    The :attr:`altadb.organization.AltaDBOrganization` object allows you to programmatically interact with
    your RedBrick organization. This class provides methods for querying your
    organization and doing other high level actions. Retrieve the organization object in the following way:

    .. code:: python

        >>> org = redbrick.get_org(api_key="", org_id="")
    """

    def __init__(self, context: AltaDBContext, org_id: str) -> None:
        """Construct AltaDBOrganization."""
        self.context = context

        self._org_id = org_id
        self._name: str

        self._get_org()

    def _get_org(self) -> None:
        org = self.context.project.get_org(self._org_id)
        self._name = org["name"]

    @property
    def org_id(self) -> str:
        """Retrieve the unique org_id of this organization."""
        return self._org_id

    @property
    def name(self) -> str:
        """Retrieve unique name of this organization."""
        return self._name

    def __str__(self) -> str:
        """Get string representation of AltaDBOrganization object."""
        return f"RedBrick AI Organization - {self._name} - ( {self._org_id} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)

    def self_health_check(self, self_url: str) -> Optional[str]:
        """Send a health check update from the model server."""
        # pylint: disable=too-many-locals, import-outside-toplevel

        import psutil  # type: ignore
        import GPUtil  # type: ignore

        uname = platform.uname()
        cpu_freq = psutil.cpu_freq()
        svmem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        partitions = psutil.disk_partitions()
        total_storage, used_storage, free_storage = 0, 0, 0
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            total_storage += partition_usage.total
            used_storage += partition_usage.used
            free_storage += partition_usage.free

        disk_io = psutil.disk_io_counters()
        if_addrs = psutil.net_if_addrs()
        net_io = psutil.net_io_counters()
        gpus = GPUtil.getGPUs()

        self_data = {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "boot_time": psutil.boot_time(),
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": cpu_freq.max,
            "min_frequency": cpu_freq.min,
            "current_frequency": cpu_freq.current,
            "cores": [
                {"usage": percentage}
                for percentage in psutil.cpu_percent(percpu=True, interval=1)
            ],
            "total_mem": svmem.total,
            "used_mem": svmem.used,
            "free_mem": svmem.free,
            "total_swap": swap.total,
            "used_swap": swap.used,
            "free_swap": swap.free,
            "total_storage": total_storage,
            "used_storage": used_storage,
            "free_storage": free_storage,
            "disk_read": disk_io.read_bytes if disk_io else None,
            "disk_write": disk_io.write_bytes if disk_io else None,
            "network": [
                {
                    "interface": interface_name,
                    "family": str(address.family),
                    "address": address.address,
                    "mask": address.netmask,
                    "broadcast": address.broadcast,
                }
                for interface_name, interface_addresses in if_addrs.items()
                for address in interface_addresses
                if str(address.family)
                in ("AddressFamily.AF_INET", "AddressFamily.AF_PACKET")
            ],
            "network_sent": net_io.bytes_sent,
            "network_recv": net_io.bytes_recv,
            "gpus": [
                {
                    "id": gpu.id,
                    "name": gpu.name,
                    "load": gpu.load,
                    "total_mem": gpu.memoryTotal,
                    "used_mem": gpu.memoryUsed,
                    "free_mem": gpu.memoryFree,
                    "temp": gpu.temperature,
                    "uuid": gpu.uuid,
                }
                for gpu in gpus
            ],
        }
        return self.context.project.self_health_check(self.org_id, self_url, self_data)
