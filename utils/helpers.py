def pixel_to_grid(px: int, py: int, cell_size: int):
    return px // cell_size, py // cell_size


def distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)
