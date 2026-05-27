import math


def clamp(v, a, b):
    return max(a, min(b, v))


def normalize(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l) if l else (0, 0)


def rects_overlap(a, b, padding=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (ax - padding < bx + bw and ax + aw + padding > bx and
            ay - padding < by + bh and ay + ah + padding > by)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def keep_inside_map(pos, margin, map_w, map_h):
    pos[0] = clamp(pos[0], margin, map_w - margin)
    pos[1] = clamp(pos[1], margin, map_h - margin)


def resolve_aabb(pos, size, rect):
    px, py = pos
    x, y, w, h = rect
    closest_x = clamp(px, x, x + w)
    closest_y = clamp(py, y, y + h)
    dx = px - closest_x
    dy = py - closest_y
    d = math.hypot(dx, dy)
    if d == 0:
        sides = [(abs(px - x), x - size, None),
                 (abs((x + w) - px), x + w + size, None),
                 (abs(py - y), None, y - size),
                 (abs((y + h) - py), None, y + h + size)]
        _, nx, ny = min(sides, key=lambda item: item[0])
        if nx is not None:
            pos[0] = nx
        if ny is not None:
            pos[1] = ny
        return
    if d < size:
        overlap = size - d
        pos[0] += dx / d * overlap
        pos[1] += dy / d * overlap


def on_screen_rect(rect, cam, screen_w, screen_h, pad=140):
    x, y, w, h = rect
    return (x + w > cam[0] - pad and x < cam[0] + screen_w + pad and
            y + h > cam[1] - pad and y < cam[1] + screen_h + pad)
