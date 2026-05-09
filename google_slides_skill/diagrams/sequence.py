"""
Sequence diagram generator -- Phase 4, Step 4.

Renders participant boxes, lifelines, and message arrows onto a slide.

Usage:
    participants = ["Client", "Server", "Database"]
    messages = [
        {"from": "Client", "to": "Server", "label": "GET /api"},
        {"from": "Server", "to": "Database", "label": "SELECT *"},
        {"from": "Database", "to": "Server", "label": "rows", "reply": True},
        {"from": "Server", "to": "Client", "label": "200 OK", "reply": True},
        {"from": "Server", "to": "Server", "label": "log()", "self_call": True},
    ]
    requests = render_sequence(page_id, participants, messages)
"""

from __future__ import annotations

from ..shapes import (
    rectangle, text_label, line, arrow, _next_id,
    FILL_LIGHT_BLUE, BORDER_BLUE, BORDER_DEFAULT,
    DASH_SOLID, DASH_DASH, ARROW_FILLED, ARROW_OPEN,
    DEFAULT_BORDER_WEIGHT_PT, to_emu,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

AREA_X = 1.0
AREA_Y = 1.0
AREA_W = 8.0
AREA_H = 4.3

# Participant box
PARTICIPANT_W = 1.2
PARTICIPANT_H = 0.45
PARTICIPANT_GAP = 0.3  # minimum gap between boxes

# Lifeline
LIFELINE_START_OFFSET = 0.1  # below participant box

# Messages
MSG_Y_START = 0.2  # first message offset below participant boxes
MSG_Y_STEP = 0.45  # vertical space per message
SELF_CALL_W = 0.6  # width of self-call loop
SELF_CALL_H = 0.3


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_sequence(page_id: str, participants: list[str],
                    messages: list[dict], *,
                    area_x: float = AREA_X, area_y: float = AREA_Y,
                    area_w: float = AREA_W, area_h: float = AREA_H,
                    ) -> list[dict]:
    """Render a sequence diagram onto a slide page.

    Args:
        page_id: Slide object ID.
        participants: List of participant names (left to right).
        messages: List of dicts with keys:
            - from, to: participant names
            - label: message text
            - reply (bool): if True, use dashed line + open arrow
            - self_call (bool): if True, draw a loop arrow to self

    Returns:
        List of batchUpdate request dicts.
    """
    n = len(participants)
    if n == 0:
        return []

    requests = []

    # Calculate participant positions (centered across area)
    total_box_w = n * PARTICIPANT_W + (n - 1) * PARTICIPANT_GAP
    spacing = PARTICIPANT_W + PARTICIPANT_GAP
    if total_box_w > area_w and n > 1:
        # Compress spacing to fit
        spacing = (area_w - PARTICIPANT_W) / (n - 1)

    start_x = area_x + (area_w - (PARTICIPANT_W + spacing * (n - 1))) / 2
    box_y = area_y

    # Map participant name -> center X
    p_centers: dict[str, float] = {}
    p_index: dict[str, int] = {}

    for i, name in enumerate(participants):
        px = start_x + i * spacing
        cx = px + PARTICIPANT_W / 2
        p_centers[name] = cx
        p_index[name] = i

        # Draw participant box
        _, reqs = rectangle(
            page_id, px, box_y, PARTICIPANT_W, PARTICIPANT_H,
            text=name, fill=FILL_LIGHT_BLUE, border_color=BORDER_BLUE,
            font_size=10, bold=True,
        )
        requests.extend(reqs)

    # Draw lifelines
    lifeline_top = box_y + PARTICIPANT_H + LIFELINE_START_OFFSET
    lifeline_bottom = area_y + area_h

    for name in participants:
        cx = p_centers[name]
        _, reqs = line(
            page_id, cx, lifeline_top, cx, lifeline_bottom,
            color={"red": 0.6, "green": 0.6, "blue": 0.6},
            weight_pt=1.0, dash=DASH_DASH,
        )
        requests.extend(reqs)

    # Draw messages
    msg_base_y = lifeline_top + MSG_Y_START

    for i, msg in enumerate(messages):
        msg_y = msg_base_y + i * MSG_Y_STEP
        from_name = msg["from"]
        to_name = msg["to"]
        label_text = msg.get("label", "")
        is_reply = msg.get("reply", False)
        is_self = msg.get("self_call", False) or (from_name == to_name)

        from_x = p_centers.get(from_name, area_x)
        to_x = p_centers.get(to_name, area_x + area_w)

        dash = DASH_DASH if is_reply else DASH_SOLID
        arrow_head = ARROW_OPEN if is_reply else ARROW_FILLED
        line_color = BORDER_DEFAULT

        if is_self:
            # Self-call: draw a small loop to the right
            loop_x = from_x
            _, reqs = line(page_id, loop_x, msg_y, loop_x + SELF_CALL_W, msg_y,
                           color=line_color, weight_pt=1.0, dash=dash)
            requests.extend(reqs)

            _, reqs = line(page_id, loop_x + SELF_CALL_W, msg_y,
                           loop_x + SELF_CALL_W, msg_y + SELF_CALL_H,
                           color=line_color, weight_pt=1.0, dash=dash)
            requests.extend(reqs)

            _, reqs = arrow(page_id, loop_x + SELF_CALL_W, msg_y + SELF_CALL_H,
                            loop_x, msg_y + SELF_CALL_H,
                            color=line_color, weight_pt=1.0, dash=dash,
                            head=arrow_head)
            requests.extend(reqs)

            # Label above the loop
            if label_text:
                _, reqs = text_label(
                    page_id, loop_x + 0.05, msg_y - 0.22,
                    SELF_CALL_W + 0.2, 0.2,
                    label_text, font_size=8, color=line_color,
                    alignment="START",
                )
                requests.extend(reqs)
        else:
            # Regular arrow between participants
            _, reqs = arrow(page_id, from_x, msg_y, to_x, msg_y,
                            color=line_color, weight_pt=1.0, dash=dash,
                            head=arrow_head)
            requests.extend(reqs)

            # Label above the arrow
            if label_text:
                label_x = min(from_x, to_x) + 0.05
                label_w = abs(to_x - from_x) - 0.1
                _, reqs = text_label(
                    page_id, label_x, msg_y - 0.22,
                    max(label_w, 0.5), 0.2,
                    label_text, font_size=8, color=line_color,
                    alignment="CENTER",
                )
                requests.extend(reqs)

    return requests
