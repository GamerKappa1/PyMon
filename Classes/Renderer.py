from Classes import Helpers
from Classes.Monitor import Monitor
import pygame

def run(monitors: list[Monitor], divider: int = 8):
    pygame.init()

    screen = pygame.display.set_mode((1200, 950), pygame.RESIZABLE)
    pygame.display.set_caption("Monitor Layout Editor")

    # Colors
    BG_COLOR = (30, 32, 36)
    FIELD_COLOR = (36, 39, 44)
    FIELD_BORDER = (85, 91, 100)

    BOX_COLOR = (65, 76, 88)
    BOX_BORDER = (115, 130, 145)
    BOX_SELECTED = (85, 91, 100)
    BOX_TEXT = (215, 220, 225)
    SELECTED_BORDER = (185, 165, 125)

    BUTTON_COLOR = (53, 58, 65)
    BUTTON_BORDER = (95, 103, 113)
    BUTTON_TEXT = (215, 220, 225)
    BUTTON_DISABLED = (43, 46, 51)
    APPLY_COLOR = (70, 130, 180)
    TOOLBAR_COLOR = (36, 39, 44)

    # Fonts
    font = pygame.font.SysFont("Arial", 17)
    small_font = pygame.font.SysFont("Arial", 13)

    # Layout settings
    MARGIN = 50
    MAX_FIELD_HEIGHT = 480
    FIELD_BUTTON_GAP = 20
    BUTTON_HEIGHT = 55
    BOTTOM_ROW_GAP = 15

    # Helper to safely parse "WxH" strings into integers
    def parse_dim(dim_str):
        parts = str(dim_str).lower().replace(" ", "").split("x")
        return int(parts[0]), int(parts[1])

    # Hyprland transform values 0-7. Odd values rotate the bounding box
    # by 90/270 degrees (including flipped variants), swapping its dimensions.
    TRANSFORM_LABELS = {
        "0": "0°",
        "1": "90°",
        "2": "180°",
        "3": "270°",
        "4": "0° (flipped)",
        "5": "90° (flipped)",
        "6": "180° (flipped)",
        "7": "270° (flipped)",
    }

    def transform_value(monitor):
        value = str(getattr(monitor, "transform", "0") or "0").strip()
        return value if value in TRANSFORM_LABELS else "0"

    def transform_label(value):
        return TRANSFORM_LABELS.get(str(value), "0°")

    # Monitor.disabled is parsed from Hyprland's monitor output as a string.
    def is_monitor_disabled(monitor):
        value = getattr(monitor, "disabled", "false")
        return value is True or str(value).strip().lower() in {"1", "true", "yes"}

    # Filter active vs disabled monitors. Keep the position/resolution checks as
    # fallbacks for monitor objects created by older versions of the parser.
    def get_valid_monitors():
        return [
            mon for mon in monitors
            if not is_monitor_disabled(mon)
            and getattr(mon, "position", "-1x-1") != "-1x-1"
            and getattr(mon, "resolution", "0x0") != "0x0"
        ]

    def get_disabled_monitors():
        return [
            mon for mon in monitors
            if is_monitor_disabled(mon)
            or getattr(mon, "position", "-1x-1") == "-1x-1"
            or getattr(mon, "resolution", "0x0") == "0x0"
        ]

    def mirror_target(monitor):
        """Return the configured mirror output name, or None."""
        value = getattr(monitor, "mirror", None)
        if value is None:
            return None
        value = str(value).strip()
        return value if value and value.lower() not in {"none", "off", "false", "0"} else None

    def mirror_root(monitor, by_name):
        """Resolve a mirrored output to the physical output it ultimately follows."""
        current = monitor
        seen = set()
        while mirror_target(current):
            target_name = mirror_target(current)
            if target_name in seen or target_name not in by_name:
                break
            seen.add(target_name)
            current = by_name[target_name]
        return current

    valid_monitors = get_valid_monitors()

    # Rebuild boxes based on active monitors
    def rebuild_boxes():
        nonlocal valid_monitors
        valid_monitors = get_valid_monitors()

        parsed_positions = []
        parsed_resolutions = []

        for x in valid_monitors:
            px, py = parse_dim(x.position)
            rw, rh = parse_dim(x.resolution)
            # The visible monitor rectangle follows its transform. 90° and
            # 270° transforms (including flipped variants) swap width/height.
            if int(transform_value(x)) % 2 == 1:
                rw, rh = rh, rw
            parsed_positions.append((px, py))
            parsed_resolutions.append((rw, rh))

        if parsed_positions:
            min_x = min(p[0] for p in parsed_positions)
            min_y = min(p[1] for p in parsed_positions)
        else:
            min_x, min_y = 0, 0

        raw_boxes = []
        for (px, py), (rw, rh) in zip(parsed_positions, parsed_resolutions):
            rx = int(round((px - min_x) / divider))
            ry = int(round((py - min_y) / divider))
            rw_scaled = int(round(rw / divider))
            rh_scaled = int(round(rh / divider))
            raw_boxes.append(pygame.Rect(rx, ry, rw_scaled, rh_scaled))

        new_boxes = []
        if raw_boxes:
            group_min_x = min(b.left for b in raw_boxes)
            group_min_y = min(b.top for b in raw_boxes)
            group_max_x = max(b.right for b in raw_boxes)
            group_max_y = max(b.bottom for b in raw_boxes)

            group_height = group_max_y - group_min_y

            initial_field_width = 1200 - MARGIN * 2
            initial_field_height = min(900 - MARGIN * 2 - FIELD_BUTTON_GAP - BUTTON_HEIGHT * 2 - BOTTOM_ROW_GAP,
                                       MAX_FIELD_HEIGHT)

            eighth_offset = (initial_field_width // 8) - group_min_x
            center_offset_y = (initial_field_height - group_height) // 2 - group_min_y

            for b in raw_boxes:
                new_boxes.append(pygame.Rect(
                    b.x + MARGIN + eighth_offset,
                    b.y + MARGIN + center_offset_y,
                    b.width,
                    b.height
                ))

        # A mirrored output is part of its target's visual group. Keep one
        # box per monitor (Helpers.write_config relies on that ordering), but
        # place mirrored outputs over their ultimate source box.
        by_name = {mon.name: i for i, mon in enumerate(valid_monitors)}
        for i, mon in enumerate(valid_monitors):
            if mirror_target(mon):
                root = mirror_root(mon, {m.name: m for m in valid_monitors})
                root_index = by_name.get(root.name)
                if root_index is not None and root_index != i:
                    new_boxes[i] = new_boxes[root_index].copy()

        return new_boxes

    boxes = rebuild_boxes()

    dragged_box = None
    selected_box = None
    is_panning = False
    open_dropdown = None

    offset_x = 0
    offset_y = 0

    clock = pygame.time.Clock()
    running = True

    # Helper: calculate responsive layout dynamically based on current window size
    def get_layout():
        width, height = screen.get_size()
        field_width = max(1, width - MARGIN * 2)
        field_height = max(
            1,
            min(height - MARGIN * 2 - FIELD_BUTTON_GAP - BUTTON_HEIGHT * 2 - BOTTOM_ROW_GAP, MAX_FIELD_HEIGHT)
        )

        field = pygame.Rect(MARGIN, MARGIN, field_width, field_height)
        toolbar = pygame.Rect(MARGIN, field.bottom + FIELD_BUTTON_GAP, field_width, BUTTON_HEIGHT)

        # Bottom row buttons
        apply_width = 160
        apply_rect = pygame.Rect(toolbar.right - apply_width, toolbar.bottom + BOTTOM_ROW_GAP, apply_width,
                                 BUTTON_HEIGHT)

        enable_dropdown_width = 220
        enable_dropdown_rect = pygame.Rect(toolbar.x, toolbar.bottom + BOTTOM_ROW_GAP, enable_dropdown_width,
                                           BUTTON_HEIGHT)

        return field, toolbar, apply_rect, enable_dropdown_rect

    # Helper: draw a button
    def draw_button(rect, label, value=None, disabled=False, is_apply=False, is_dropdown=False):
        color = APPLY_COLOR if is_apply and not disabled else (BUTTON_DISABLED if disabled else BUTTON_COLOR)
        border = (100, 155, 205) if is_apply and not disabled else ((65, 69, 75) if disabled else BUTTON_BORDER)
        text_color = (110, 115, 122) if disabled else BUTTON_TEXT

        pygame.draw.rect(screen, color, rect, border_radius=5)
        pygame.draw.rect(screen, border, rect, width=1, border_radius=5)

        if value is None:
            text = font.render(label, True, text_color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
        else:
            label_surface = small_font.render(label, True, text_color)
            value_surface = font.render(value, True, text_color)

            label_rect = label_surface.get_rect(midleft=(rect.x + 10, rect.centery - 11))
            value_rect = value_surface.get_rect(midleft=(rect.x + 10, rect.centery + 9))

            screen.blit(label_surface, label_rect)
            screen.blit(value_surface, value_rect)

            arrow = small_font.render("v", True, text_color)
            screen.blit(arrow, (rect.right - 20, rect.centery - 7))

    def get_control_rects(toolbar):
        toolbar_margin = 10
        gap = 8
        num_buttons = 5
        available_width = toolbar.width - (toolbar_margin * 2)
        button_width = (available_width - (gap * (num_buttons - 1))) // num_buttons
        rects = []
        x = toolbar.x + toolbar_margin
        for _ in range(num_buttons):
            rects.append(pygame.Rect(
                x, toolbar.y + 7, button_width, toolbar.height - 14
            ))
            x += button_width + gap
        return rects

    def get_dropdown_options(name, monitor, disabled):
        if name == "enable":
            return [(mon.name, mon) for mon in disabled]

        if monitor is None:
            return []

        modes = getattr(monitor, "available_modes", []) or []
        if name == "rotate":
            # Hyprland transform values: 0-3 rotations, 4-7 flipped variants.
            transforms = [
                ("0°", "0"),
                ("90°", "1"),
                ("180°", "2"),
                ("270°", "3"),
                ("0° (flipped)", "4"),
                ("90° (flipped)", "5"),
                ("180° (flipped)", "6"),
                ("270° (flipped)", "7"),
            ]
            return transforms

        if name == "resolution":
            resolutions = list(dict.fromkeys(
                str(mode.resolution) for mode in modes if getattr(mode, "resolution", None)
            ))
            if monitor.resolution and monitor.resolution not in resolutions:
                resolutions.insert(0, str(monitor.resolution))
            return [(resolution, resolution) for resolution in resolutions]

        if name == "refresh":
            rates = list(dict.fromkeys(
                str(mode.refresh_rate)
                for mode in modes
                if str(getattr(mode, "resolution", "")) == str(monitor.resolution)
                and getattr(mode, "refresh_rate", None) not in (None, "")
            ))
            if monitor.refresh_rate and str(monitor.refresh_rate) not in rates:
                rates.insert(0, str(monitor.refresh_rate))
            return [(f"{rate} Hz", rate) for rate in rates]

        if name == "disable":
            return [("Disable selected monitor", "disable")]

        if name == "mirror":
            # A monitor can mirror any other active output, but never itself.
            # None removes mirroring from the selected monitor.
            options = [("No mirroring", None)]
            options.extend(
                (f"Mirror {other.name}", other.name)
                for other in valid_monitors
                if other is not monitor
            )
            return options
        return []

    def get_menu_rect(anchor, option_count, item_height=36):
        menu = pygame.Rect(
            anchor.x, anchor.bottom + 5, anchor.width,
            option_count * item_height + 10
        )
        if menu.bottom > screen.get_height() - 8:
            menu.bottom = anchor.top - 5
        return menu

    def apply_dropdown_option(name, value, monitor):
        nonlocal boxes, selected_box

        if name == "enable":
            mon = value
            mon.disabled = "false"
            if getattr(mon, "position", "-1x-1") == "-1x-1":
                mon.position = "0x0"

            modes = getattr(mon, "available_modes", []) or []
            if modes:
                # Prefer the first advertised mode when the stored mode is invalid.
                matching_mode = next(
                    (mode for mode in modes
                     if str(mode.resolution) == str(mon.resolution)),
                    modes[0]
                )
                if not mon.resolution or mon.resolution == "0x0":
                    mon.resolution = str(matching_mode.resolution)
                if not mon.refresh_rate:
                    mon.refresh_rate = str(matching_mode.refresh_rate)
            elif not mon.resolution or mon.resolution == "0x0":
                mon.resolution = "1920x1080"

            boxes = rebuild_boxes()
            selected_box = None

        elif monitor is not None and name == "rotate":
            # Keep Hyprland's numeric transform (0-7), and update the actual
            # rectangle shown in the editor to match the transformed shape.
            monitor.transform = str(value)
            monitor_index = valid_monitors.index(monitor) if monitor in valid_monitors else None
            boxes = rebuild_boxes()
            selected_box = boxes[monitor_index] if monitor_index is not None and monitor_index < len(boxes) else None

        elif monitor is not None and name == "resolution":
            monitor.resolution = str(value)
            compatible_rates = [
                str(mode.refresh_rate)
                for mode in (getattr(monitor, "available_modes", []) or [])
                if str(getattr(mode, "resolution", "")) == str(value)
                and getattr(mode, "refresh_rate", None) not in (None, "")
            ]
            if compatible_rates:
                current_rate = str(getattr(monitor, "refresh_rate", ""))
                if current_rate not in compatible_rates:
                    monitor.refresh_rate = compatible_rates[0]
            boxes = rebuild_boxes()
            selected_box = None

        elif monitor is not None and name == "refresh":
            monitor.refresh_rate = str(value)

        elif monitor is not None and name == "mirror":
            # A root monitor can be selected even when its mirrored outputs
            # are visually grouped underneath it. "No mirroring" therefore
            # clears both its own rule and rules from outputs mirroring it.
            if value is None:
                monitor.mirror = None
                by_name = {m.name: m for m in valid_monitors}
                for other in valid_monitors:
                    if other is not monitor and mirror_root(other, by_name) is monitor:
                        other.mirror = None
            else:
                monitor.mirror = value
            boxes = rebuild_boxes()
            selected_index = valid_monitors.index(monitor) if monitor in valid_monitors else None
            selected_box = boxes[selected_index] if selected_index is not None else None

        elif monitor is not None and name == "disable":
            monitor.disabled = "true"
            # Hyprland's disabled monitor output may use either sentinel values
            # or an explicit disabled flag; the flag is authoritative here.
            boxes = rebuild_boxes()
            selected_box = None

    while running:
        field, toolbar, apply_rect, enable_dropdown_rect = get_layout()
        disabled_monitors = get_disabled_monitors()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Nudge selected box with arrow keys by 1px
                if selected_box is not None:
                    old_position = selected_box.topleft
                    dx, dy = 0, 0
                    if event.key == pygame.K_LEFT:
                        dx = -1
                    elif event.key == pygame.K_RIGHT:
                        dx = 1
                    elif event.key == pygame.K_UP:
                        dy = -1
                    elif event.key == pygame.K_DOWN:
                        dy = 1

                    if dx != 0 or dy != 0:
                        selected_box.x += dx
                        selected_box.y += dy
                        # Prevent overlap during keyboard nudging
                        if any(
                                selected_box.colliderect(box)
                                for box in boxes
                                if box is not selected_box
                        ):
                            selected_box.topleft = old_position

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Resolve the selected monitor before processing dropdown actions.
                    selected_monitor = None
                    if selected_box is not None and selected_box in boxes:
                        selected_index = boxes.index(selected_box)
                        if selected_index < len(valid_monitors):
                            selected_monitor = valid_monitors[selected_index]

                    control_rects = get_control_rects(toolbar)
                    control_names = ["rotate", "resolution", "refresh", "mirror", "disable"]
                    clicked_dropdown_item = False

                    if open_dropdown is not None:
                        if open_dropdown == "enable":
                            anchor = enable_dropdown_rect
                            options = get_dropdown_options("enable", selected_monitor, disabled_monitors)
                        else:
                            control_index = control_names.index(open_dropdown)
                            anchor = control_rects[control_index]
                            options = get_dropdown_options(open_dropdown, selected_monitor, disabled_monitors)

                        item_height = 36
                        menu_rect = get_menu_rect(anchor, len(options), item_height)
                        for i, (option_label, option_value) in enumerate(options):
                            item_rect = pygame.Rect(
                                menu_rect.x + 5,
                                menu_rect.y + 5 + i * item_height,
                                menu_rect.width - 10,
                                item_height - 4
                            )
                            if item_rect.collidepoint(event.pos):
                                apply_dropdown_option(open_dropdown, option_value, selected_monitor)
                                open_dropdown = None
                                clicked_dropdown_item = True
                                break

                    if clicked_dropdown_item:
                        continue

                    if enable_dropdown_rect.collidepoint(event.pos):
                        open_dropdown = (
                            None if open_dropdown == "enable"
                            else ("enable" if disabled_monitors else None)
                        )
                    else:
                        clicked_control = None
                        for name, rect in zip(control_names, control_rects):
                            if rect.collidepoint(event.pos):
                                clicked_control = name
                                break

                        if clicked_control is not None:
                            if selected_monitor is not None:
                                open_dropdown = (
                                    None if open_dropdown == clicked_control
                                    else clicked_control
                                )
                            else:
                                open_dropdown = None
                        elif apply_rect.collidepoint(event.pos):
                            Helpers.write_config(boxes.copy(), monitors.copy())
                            open_dropdown = None
                        elif field.collidepoint(event.pos):
                            open_dropdown = None
                            selected_box = None

                            for box in reversed(boxes):
                                if box.collidepoint(event.pos):
                                    dragged_box = box
                                    selected_box = box
                                    offset_x = box.x - event.pos[0]
                                    offset_y = box.y - event.pos[1]
                                    break
                        else:
                            open_dropdown = None
                            dragged_box = None

                elif event.button == 2:  # Middle-click pan
                    if field.collidepoint(event.pos):
                        is_panning = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragged_box is not None:
                        SNAP_THRESHOLD = 30
                        for box in boxes:
                            if box is dragged_box:
                                continue

                            if not (dragged_box.bottom <= box.top or dragged_box.top >= box.bottom):
                                if abs(dragged_box.right - box.left) < SNAP_THRESHOLD:
                                    dragged_box.right = box.left
                                    break
                                elif abs(dragged_box.left - box.right) < SNAP_THRESHOLD:
                                    dragged_box.left = box.right
                                    break

                            if not (dragged_box.right <= box.left or dragged_box.left >= box.right):
                                if abs(dragged_box.bottom - box.top) < SNAP_THRESHOLD:
                                    dragged_box.bottom = box.top
                                    break
                                elif abs(dragged_box.top - box.bottom) < SNAP_THRESHOLD:
                                    dragged_box.top = box.bottom
                                    break

                    dragged_box = None

                elif event.button == 2:
                    is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    dx, dy = event.rel
                    for box in boxes:
                        box.x += dx
                        box.y += dy
                elif dragged_box is not None:
                    old_position = dragged_box.topleft

                    dragged_box.x = event.pos[0] + offset_x
                    dragged_box.y = event.pos[1] + offset_y

                    if any(
                            dragged_box.colliderect(box)
                            for box in boxes
                            if box is not dragged_box
                    ):
                        dragged_box.topleft = old_position

        # Get selected monitor
        selected_monitor = None
        if selected_box is not None and selected_box in boxes:
            selected_index = boxes.index(selected_box)
            if selected_index < len(valid_monitors):
                selected_monitor = valid_monitors[selected_index]

        # Get available modes for selected monitor
        available_resolutions = []
        available_refresh_rates = []

        if selected_monitor is not None:
            modes = getattr(selected_monitor, "available_modes", [])
            available_resolutions = list(dict.fromkeys(
                getattr(mode, "resolution", mode) for mode in modes
            ))
            available_refresh_rates = list(dict.fromkeys(
                getattr(mode, "refresh_rate", mode)
                for mode in modes
                if getattr(mode, "resolution", None) == selected_monitor.resolution
            ))

        # -------------------------
        # Drawing
        # -------------------------
        screen.fill(BG_COLOR)

        # Playing field with clipping area for partial offscreen hiding
        screen.set_clip(field)

        # Playing field background
        pygame.draw.rect(screen, FIELD_COLOR, field)
        pygame.draw.rect(screen, FIELD_BORDER, field, width=2)

        # Monitor boxes. Mirrored outputs are drawn as part of their ultimate
        # source monitor instead of as separate rectangles.
        by_name = {mon.name: mon for mon in valid_monitors}
        grouped_names = {}
        for mon in valid_monitors:
            root = mirror_root(mon, by_name)
            grouped_names.setdefault(root.name, []).append(mon.name)

        for box, monitor in zip(boxes, valid_monitors):
            # Do not draw a second rectangle for a mirrored output.
            if mirror_target(monitor):
                continue

            is_selected = box is selected_box
            fill = BOX_SELECTED if is_selected else BOX_COLOR
            border = SELECTED_BORDER if is_selected else BOX_BORDER

            pygame.draw.rect(screen, fill, box, border_radius=4)
            pygame.draw.rect(screen, border, box, width=2, border_radius=4)

            names = grouped_names.get(monitor.name, [monitor.name])
            label_text = " | ".join(names)
            label = font.render(label_text, True, BOX_TEXT)
            # Keep long grouped labels inside the monitor rectangle.
            if label.get_width() > box.width - 12:
                label = small_font.render(label_text, True, BOX_TEXT)
            screen.blit(label, label.get_rect(center=box.center))

        # Reset screen clip so toolbar and border render cleanly outside the field
        screen.set_clip(None)
        pygame.draw.rect(screen, FIELD_BORDER, field, width=2)

        # Toolbar background
        pygame.draw.rect(screen, TOOLBAR_COLOR, toolbar)
        pygame.draw.rect(screen, FIELD_BORDER, toolbar, width=2)

        # Five toolbar dropdowns
        control_rects = get_control_rects(toolbar)
        if selected_monitor is not None:
            # Show the names of outputs grouped with this selected monitor.
            mirror_members = [
                mon.name for mon in valid_monitors
                if mon is not selected_monitor and mirror_root(mon, {m.name: m for m in valid_monitors}) is selected_monitor
            ]
            own_target = getattr(selected_monitor, "mirror", None)
            if mirror_members:
                mirror_label = " | ".join(mirror_members)
            elif own_target:
                mirror_label = str(own_target)
            else:
                mirror_label = "Off"
        else:
            mirror_label = "Select monitor"
        button_specs = [
            ("Transform", transform_label(transform_value(selected_monitor)) if selected_monitor else "Select monitor"),
            ("Resolution", selected_monitor.resolution if selected_monitor else "Select monitor"),
            (
                "Refresh rate",
                f"{selected_monitor.refresh_rate} Hz" if selected_monitor else "Select monitor"
            ),
            ("Mirror", mirror_label),
            ("Disable", None)
        ]

        for rect, (label, value) in zip(control_rects, button_specs):
            draw_button(rect, label, value, disabled=selected_monitor is None)

        # Draw Bottom Row Buttons
        draw_button(apply_rect, "Apply", disabled=False, is_apply=True)

        enable_label = f"Enable Monitor ({len(disabled_monitors)})" if disabled_monitors else "No Disabled Monitors"
        draw_button(enable_dropdown_rect, enable_label, disabled=not disabled_monitors, is_dropdown=True)

        # Draw the currently open dropdown menu.
        if open_dropdown is not None:
            if open_dropdown == "enable":
                anchor = enable_dropdown_rect
            else:
                anchor = control_rects[["rotate", "resolution", "refresh", "mirror", "disable"].index(open_dropdown)]

            options = get_dropdown_options(open_dropdown, selected_monitor, disabled_monitors)
            item_height = 36
            menu_rect = get_menu_rect(anchor, len(options), item_height)

            pygame.draw.rect(screen, BUTTON_COLOR, menu_rect, border_radius=5)
            pygame.draw.rect(screen, BUTTON_BORDER, menu_rect, width=1, border_radius=5)

            for i, (option_label, _) in enumerate(options):
                item_rect = pygame.Rect(
                    menu_rect.x + 5,
                    menu_rect.y + 5 + i * item_height,
                    menu_rect.width - 10,
                    item_height - 4
                )
                if item_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, (70, 78, 88), item_rect, border_radius=4)

                item_text = small_font.render(str(option_label), True, BUTTON_TEXT)
                screen.blit(
                    item_text,
                    item_text.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
                )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()