from pathlib import Path
def get_start_end_line_monitors():
    path = Path("~/.config/hypr/hyprland.lua").expanduser()
    content = path.read_text()

    split_content = content.split("\n")
    startline = 0
    endline = 0

    for i in range(content.count("\n")):
        if split_content[i].startswith("hl.monitor"):
            startline = i
        elif startline != 0:
            break

    hl_monitor_is_open = False
    for i in range(startline, content.count("\n")):
        if split_content[i].startswith("hl.monitor"):
            hl_monitor_is_open = True
        elif hl_monitor_is_open and split_content[i].startswith("})"):
            hl_monitor_is_open = False
            endline = i + 1

    return startline,endline

def get_monitors():
    import subprocess
    from Classes.Monitor import Monitor
    import re

    # If return value is needed
    # subprocess.check_output(["<command>", "<arguments>"])
    # subprocess.check_output("<command>")

    # If no return value is needed
    # subprocess.run(["<command>", "<arguments>"])
    # subprocess.run("<command>")

    monitor_config = subprocess.check_output("hyprctl monitors all", shell=True).decode("utf-8").strip().encode("utf-8")

    return [Monitor(x) for x in re.split(r"\n\n", monitor_config.decode("utf-8")) if x]

def get_offset(boxes):
    if boxes is None or boxes.__sizeof__() == 0:
        return None

    offset_x, offset_y = boxes[0].left, boxes[0].top

    for box in boxes:
        offset_x = min(box.left, offset_x)
        offset_y = min(box.top, offset_y)

    return offset_x, offset_y

from Classes.Monitor import Monitor
def write_config(boxes, monitors: list[Monitor]):

    print("Writing Config...")

    if not boxes:
        return

    offset_x, offset_y = get_offset(boxes)

    config = "\n"

    for box, monitor in zip(boxes, monitors):
        config += (
                "hl.monitor({\n" +
                f'    output = "{monitor.name}",\n' +
                f'    mode = "{monitor.resolution}@{monitor.refresh_rate}",\n' +
                f'    position = "{(box.x - offset_x) * 8}x{(box.y - offset_y) * 8}",\n' +
                "    scale = 1,\n" +
                f'    disabled = {"true" if str(monitor.disabled).lower().strip() == "true" else "false"},\n' +
                f"    transform = {monitor.transform},\n"
        )

        # Hyprland mirror option: the value is the output name to mirror.
        mirror_target = getattr(monitor, "mirror", None)
        if mirror_target:
            config += f'    mirror = "{mirror_target}",\n'

        config += "})\n"

    startline, endline = get_start_end_line_monitors()
    path = Path("~/.config/hypr/hyprland.lua").expanduser()
    content = path.read_text()
    content = content.split("\n")
    content = "\n".join(content[:startline]) + config + "\n".join(content[endline:])
    path = Path("~/.config/hypr/hyprland.lua").expanduser()
    # path = Path("~/Applications/layout/hyprland.lua").expanduser()
    path.write_text(content)
