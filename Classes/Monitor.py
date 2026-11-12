from dataclasses import dataclass
import re

@dataclass
class HardwareDetails:
    backend: str
    hdr: str
    chroma: str
    bt2020: str
    vrr_capable: str

@dataclass
class MonitorMode:
    resolution: str
    refresh_rate: str

@dataclass
class Monitor:
    name: str
    id: str
    resolution: str
    refresh_rate: str
    position: str
    description: str
    make: str
    model: str
    physical_size: str
    serial: str
    active_workspace: str
    special_workspace: str
    reserved: str
    scale: str
    transform: str
    focused: str
    dpms_status: str
    vrr: str
    solitary: str
    solitary_blocked_by: str
    actively_tearing: str
    tearing_blocked_by: str
    direct_scanout_to: str
    direct_scanout_blocked_by: str
    disabled: str
    current_format: str
    mirror_of: str
    available_modes: list[MonitorMode]
    color_management_preset: str
    sdr_brightness: str
    sdr_saturation: str
    sdr_min_luminance: str
    sdr_max_luminance: str
    hardware_cursors_in_use: str
    hardware_details: HardwareDetails

    def __init__(self, monitor_string: str):
        lines = monitor_string.strip().splitlines()

        header_match = re.match(r"Monitor\s+(.*?)\s+\(ID\s+([^)]+)\):", lines[0].strip())
        self.name = header_match.group(1) if header_match else ""
        self.id = header_match.group(2) if header_match else ""

        res_str = lines[1].strip() if len(lines) > 1 else ""
        match = re.match(r"([\d]+x[\d]+)@([\d.]+)\s+at\s+(.+)", res_str)
        if match:
            self.resolution = match.group(1)
            self.refresh_rate = match.group(2)
            self.position = match.group(3)
        else:
            self.resolution = res_str
            self.refresh_rate = ""
            self.position = ""

        data = {}
        hw_data = {}
        is_hardware_details = False

        for line in lines[2:]:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("hardwareDetails:"):
                is_hardware_details = True
                continue

            if is_hardware_details and line.startswith("\t\t"):
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    hw_data[k.strip()] = v.strip()
            elif ":" in stripped:
                k, v = stripped.split(":", 1)
                data[k.strip()] = v.strip()

        self.description = data.get("description", "")
        self.make = data.get("make", "")
        self.model = data.get("model", "")
        self.physical_size = data.get("physical size (mm)", "")
        self.serial = data.get("serial", "")
        self.active_workspace = data.get("active workspace", "")
        self.special_workspace = data.get("special workspace", "")
        self.reserved = data.get("reserved", "")
        self.scale = data.get("scale", "")
        self.transform = data.get("transform", "")
        self.focused = data.get("focused", "")
        self.dpms_status = data.get("dpmsStatus", "")
        self.vrr = data.get("vrr", "")
        self.solitary = data.get("solitary", "")
        self.solitary_blocked_by = data.get("solitaryBlockedBy", "")
        self.actively_tearing = data.get("activelyTearing", "")
        self.tearing_blocked_by = data.get("tearingBlockedBy", "")
        self.direct_scanout_to = data.get("directScanoutTo", "")
        self.direct_scanout_blocked_by = data.get("directScanoutBlockedBy", "")
        self.disabled = data.get("disabled", "")
        self.current_format = data.get("currentFormat", "")
        self.mirror_of = data.get("mirrorOf", "")

        self.available_modes = [
            MonitorMode(
                resolution=match.group(1),
                refresh_rate=match.group(2)
            )
            for mode in data.get("availableModes", "").split()
            if (match := re.match(r"(\d+x\d+)@([\d.]+)Hz", mode))
        ]

        self.color_management_preset = data.get("colorManagementPreset", "")
        self.sdr_brightness = data.get("sdrBrightness", "")
        self.sdr_saturation = data.get("sdrSaturation", "")
        self.sdr_min_luminance = data.get("sdrMinLuminance", "")
        self.sdr_max_luminance = data.get("sdrMaxLuminance", "")
        self.hardware_cursors_in_use = data.get("hardwareCursorsInUse", "")

        self.hardware_details = HardwareDetails(
            backend=hw_data.get("backend", ""),
            hdr=hw_data.get("hdr", ""),
            chroma=hw_data.get("chroma", ""),
            bt2020=hw_data.get("bt2020", ""),
            vrr_capable=hw_data.get("vrrCapable", "")
        )