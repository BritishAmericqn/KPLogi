import numpy as np
from PIL import Image
import heapq
from math import sqrt, inf


class PathNode:
    def __init__(self, position, g_cost=float('inf'), h_cost=0):
        self.position = position
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.parent = None

    def f_cost(self):
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost() < other.f_cost()


class RouteCalculator:
    def __init__(self, image_path):
        self.load_map(image_path)
        self.directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        self.sea_rgb = (0, 0, 255)  # Pure blue for sea
        self.sea_threshold = 150  # Threshold for blue component
        self.blue_ratio = 1.5  # How much higher blue should be compared to red/green

    def load_map(self, image_path):
        """Load and process the map image"""
        self.original_image = Image.open(image_path)
        self.gray_image = np.array(self.original_image.convert('L'))
        self.height, self.width = self.gray_image.shape
        self.rgb_array = np.array(self.original_image.convert('RGB'))

    def is_sea(self, position):
        """Enhanced sea detection using RGB values"""
        x, y = position
        if 0 <= x < self.width and 0 <= y < self.height:
            r, g, b = self.rgb_array[y, x]
            is_bluish = (b > self.sea_threshold and
                         b > r * self.blue_ratio and
                         b > g * self.blue_ratio)
            return is_bluish
        return False

    def get_terrain_cost(self, position, avoid_sea=False):
        """Calculate terrain cost based on pixel intensity and mode"""
        x, y = position
        if 0 <= x < self.width and 0 <= y < self.height:
            # If in sea-restricted mode and position is sea, return infinite cost
            if avoid_sea and self.is_sea(position):
                return float('inf')

            # Otherwise, use grayscale intensity for cost
            return 1 + (self.gray_image[y, x] / 255.0) * 9
        return float('inf')

    def calculate_route(self, start, end, mode="unrestricted"):
        """Main routing function that handles all travel modes"""
        if mode == "air_travel":
            return self.calculate_air_route(start, end)
        elif mode == "sea_restricted":
            return self.calculate_astar_route(start, end, avoid_sea=True)
        else:  # unrestricted
            return self.calculate_astar_route(start, end, avoid_sea=False)

    def calculate_air_route(self, start, end):
        """Calculate direct air route using Pythagorean theorem"""
        distance = sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
        return [start, end], distance

    def get_valid_neighbors(self, position, avoid_sea=False):
        """Get valid neighboring positions"""
        neighbors = []
        x, y = position

        for dx, dy in self.directions:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                # Only check for sea if in sea-restricted mode
                if avoid_sea and self.is_sea((new_x, new_y)):
                    continue
                neighbors.append((new_x, new_y))

        return neighbors

    def heuristic(self, a, b):
        """Calculate heuristic distance between two points"""
        return sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

    def calculate_astar_route(self, start, end, avoid_sea=False):
        """A* pathfinding implementation"""
        start_node = PathNode(start, g_cost=0)
        start_node.h_cost = self.heuristic(start, end)

        open_set = []
        heapq.heappush(open_set, start_node)
        open_dict = {start: start_node}

        closed_set = set()

        while open_set:
            current = heapq.heappop(open_set)
            open_dict.pop(current.position)

            if current.position == end:
                path = []
                cost = current.g_cost
                while current:
                    path.append(current.position)
                    current = current.parent
                return path[::-1], cost

            closed_set.add(current.position)

            for neighbor_pos in self.get_valid_neighbors(current.position, avoid_sea):
                if neighbor_pos in closed_set:
                    continue

                # Calculate movement cost based on terrain and mode
                movement_cost = self.get_terrain_cost(neighbor_pos, avoid_sea)

                # Skip if the position is impassable
                if movement_cost == float('inf'):
                    continue

                new_g_cost = current.g_cost + movement_cost

                if neighbor_pos in open_dict:
                    neighbor = open_dict[neighbor_pos]
                    if new_g_cost < neighbor.g_cost:
                        neighbor.g_cost = new_g_cost
                        neighbor.parent = current
                        heapq.heapify(open_set)
                else:
                    neighbor = PathNode(neighbor_pos, g_cost=new_g_cost)
                    neighbor.h_cost = self.heuristic(neighbor_pos, end)
                    neighbor.parent = current
                    heapq.heappush(open_set, neighbor)
                    open_dict[neighbor_pos] = neighbor

        return None, float('inf')