import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import re
from pathfinding import RouteCalculator


class RoutePlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Route Planner")

        # Variables
        self.map_path = tk.StringVar()
        self.total_cost = tk.StringVar(value="0.00")
        self.travel_mode = tk.StringVar(value="unrestricted")
        self.zoom_level = 1.0
        self.start_coords = None
        self.end_coords = None
        self.start_entry = tk.StringVar()
        self.end_entry = tk.StringVar()
        self.base_point_radius = 5
        self.current_path = None  # Store the current path
        self.current_cost = None  # Store the current cost

        # Scrolling variables
        self.scroll_x = 0
        self.scroll_y = 0
        self.dragging = False
        self.last_x = 0
        self.last_y = 0

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Map viewer section with scrollbars
        map_viewer_frame = ttk.LabelFrame(main_frame, text="Map Viewer", padding="5")
        map_viewer_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Create scrollable canvas container
        self.canvas_container = ttk.Frame(map_viewer_frame)
        self.canvas_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add scrollbars
        x_scrollbar = ttk.Scrollbar(map_viewer_frame, orient=tk.HORIZONTAL)
        x_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        y_scrollbar = ttk.Scrollbar(map_viewer_frame, orient=tk.VERTICAL)
        y_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Canvas for map display
        self.map_canvas = tk.Canvas(self.canvas_container, width=600, height=400, bg='white',
                                    xscrollcommand=x_scrollbar.set,
                                    yscrollcommand=y_scrollbar.set)
        self.map_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure scrollbars
        x_scrollbar.configure(command=self.map_canvas.xview)
        y_scrollbar.configure(command=self.map_canvas.yview)

        # Bind events
        self.map_canvas.bind("<Button-1>", self.on_map_click)
        self.map_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.map_canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.map_canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down

        # Bind drag events
        self.map_canvas.bind("<Button-2>", self.start_drag)  # Middle mouse button
        self.map_canvas.bind("<B2-Motion>", self.drag)
        self.map_canvas.bind("<ButtonRelease-2>", self.stop_drag)

        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Route Parameters", padding="5")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Map file selection
        ttk.Label(input_frame, text="Map File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(input_frame, textvariable=self.map_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_map).grid(row=0, column=2, padx=5)

        # Cost display
        ttk.Label(input_frame, text="Total Cost:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Label(input_frame, textvariable=self.total_cost).grid(row=1, column=1, sticky=tk.W, padx=5)

        # Travel mode dropdown
        ttk.Label(input_frame, text="Travel Mode:").grid(row=2, column=0, sticky=tk.W, padx=5)
        travel_modes = ["Air Travel", "Sea Restricted", "Unrestricted"]
        travel_mode_dropdown = ttk.Combobox(input_frame, textvariable=self.travel_mode, values=travel_modes, state="readonly")
        travel_mode_dropdown.grid(row=2, column=1, sticky=tk.W, padx=5)

        # Coordinates entry frame
        coords_frame = ttk.Frame(input_frame)
        coords_frame.grid(row=3, column=0, columnspan=3, pady=5)

        # Start coordinates entry
        ttk.Label(coords_frame, text="Start Coordinates:").grid(row=0, column=0, sticky=tk.W, padx=5)
        start_entry = ttk.Entry(coords_frame, textvariable=self.start_entry, width=15)
        start_entry.grid(row=0, column=1, padx=5)
        self.start_entry.trace_add("write", self.on_start_entry_change)

        # End coordinates entry
        ttk.Label(coords_frame, text="End Coordinates:").grid(row=0, column=2, sticky=tk.W, padx=5)
        end_entry = ttk.Entry(coords_frame, textvariable=self.end_entry, width=15)
        end_entry.grid(row=0, column=3, padx=5)
        self.end_entry.trace_add("write", self.on_end_entry_change)

        # Compute button
        ttk.Button(input_frame, text="Compute Route", command=self.compute_route).grid(row=4, column=0, columnspan=3, pady=10)

        # Load initial map
        self.load_initial_map()

    def start_drag(self, event):
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y

    def drag(self, event):
        if self.dragging:
            # Calculate the difference in position
            dx = self.last_x - event.x
            dy = self.last_y - event.y

            # Scroll the canvas
            self.map_canvas.xview_scroll(int(dx), "units")
            self.map_canvas.yview_scroll(int(dy), "units")

            # Update the last position
            self.last_x = event.x
            self.last_y = event.y

    def stop_drag(self, event):
        self.dragging = False

    def load_initial_map(self):
        self.original_image = Image.open("kerbinbiomesTrue.png")
        self.display_image()

    def get_visible_coords(self, x, y):
        # Get the canvas scroll position
        scroll_x = self.map_canvas.xview()[0]
        scroll_y = self.map_canvas.yview()[0]

        # Calculate the actual coordinates taking into account scrolling
        actual_x = x + (scroll_x * self.map_canvas.winfo_width())
        actual_y = y + (scroll_y * self.map_canvas.winfo_height())

        return actual_x, actual_y

    def get_scaled_coordinates(self, coords):
        if coords:
            # Get scroll offset
            scroll_x = self.map_canvas.xview()[0] * self.map_canvas.winfo_width()
            scroll_y = self.map_canvas.yview()[0] * self.map_canvas.winfo_height()

            # Apply zoom and adjust for scrolling
            return (
                coords[0] * self.zoom_level - scroll_x,
                coords[1] * self.zoom_level - scroll_y
            )
        return None

    def get_unscaled_coordinates(self, coords):
        # Get scroll offset
        scroll_x = self.map_canvas.xview()[0] * self.map_canvas.winfo_width()
        scroll_y = self.map_canvas.yview()[0] * self.map_canvas.winfo_height()

        # Remove scroll offset and zoom scaling
        return (
            int((coords[0] + scroll_x) / self.zoom_level),
            int((coords[1] + scroll_y) / self.zoom_level)
        )

    def parse_coordinates(self, coord_str):
        try:
            match = re.match(r'\(?\s*(\d+)\s*,\s*(\d+)\s*\)?', coord_str)
            if match:
                return (int(match.group(1)), int(match.group(2)))
        except:
            return None
        return None

    def on_start_entry_change(self, *args):
        coords = self.parse_coordinates(self.start_entry.get())
        if coords:
            self.start_coords = coords
            self.redraw_points()

    def on_end_entry_change(self, *args):
        coords = self.parse_coordinates(self.end_entry.get())
        if coords:
            self.end_coords = coords
            self.redraw_points()

    def draw_point(self, coords, color, tag):
        """Draw a point with proper scaling and scroll position consideration"""
        if coords:
            scaled_coords = self.get_scaled_coordinates(coords)
            scaled_radius = self.base_point_radius * self.zoom_level
            x, y = scaled_coords
            self.map_canvas.create_oval(
                x - scaled_radius, y - scaled_radius,
                x + scaled_radius, y + scaled_radius,
                fill=color, tags=tag
            )

    def redraw_points(self):
        self.map_canvas.delete("all")
        self.display_image()

        # Redraw the current path if it exists
        if self.current_path:
            self.draw_path(self.current_path)

        # Draw points last to ensure they're on top
        if self.start_coords:
            self.draw_point(self.start_coords, 'green', 'start')
        if self.end_coords:
            self.draw_point(self.end_coords, 'red', 'end')

    def on_mouse_wheel(self, event):
        old_zoom = self.zoom_level

        # Handle different event types for Windows/Linux
        if event.num == 5 or event.delta < 0:  # Scroll down
            self.zoom_level = max(0.1, self.zoom_level * 0.9)
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.zoom_level = min(5.0, self.zoom_level * 1.1)

        # If zoom changed, update display
        if old_zoom != self.zoom_level:
            self.redraw_points()  # This will now redraw everything including the path

    def browse_map(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filename:
            self.map_path.set(filename)
            self.load_map(filename)

    def load_map(self, filename):
        try:
            self.original_image = Image.open(filename)
            self.display_image()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def display_image(self):
        if hasattr(self, 'original_image'):
            # Calculate new size based on zoom level
            new_width = int(self.original_image.width * self.zoom_level)
            new_height = int(self.original_image.height * self.zoom_level)

            # Resize image
            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)

            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(resized_image)

            # Update canvas
            self.map_canvas.delete("all")
            self.map_canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

            # Configure the scrollable area
            self.map_canvas.configure(scrollregion=(0, 0, new_width, new_height))

    def on_map_click(self, event):
        # Get the actual coordinates considering scroll position
        actual_coords = self.get_unscaled_coordinates((event.x, event.y))

        if not self.start_coords:
            self.start_coords = actual_coords
            self.start_entry.set(f"({actual_coords[0]}, {actual_coords[1]})")
            self.draw_point(self.start_coords, 'green', 'start')
        elif not self.end_coords:
            self.end_coords = actual_coords
            self.end_entry.set(f"({actual_coords[0]}, {actual_coords[1]})")
            self.draw_point(self.end_coords, 'red', 'end')
        else:
            self.start_coords = actual_coords
            self.end_coords = None
            self.start_entry.set(f"({actual_coords[0]}, {actual_coords[1]})")
            self.end_entry.set("")
            self.redraw_points()

    def draw_path(self, path):
        """Draw the path with proper scaling and scroll position consideration"""
        if not path:
            return

        scaled_path = []
        for x, y in path:
            scaled_x, scaled_y = self.get_scaled_coordinates((x, y))
            scaled_path.append((scaled_x, scaled_y))

        # Draw lines connecting the points
        for i in range(len(scaled_path) - 1):
            x1, y1 = scaled_path[i]
            x2, y2 = scaled_path[i + 1]
            self.map_canvas.create_line(x1, y1, x2, y2, fill='yellow', width=2, tags='path')

    def compute_route(self):
        if not self.start_coords or not self.end_coords:
            tk.messagebox.showwarning("Warning", "Please select both start and end points on the map")
            return

        try:
            # Initialize route calculator
            calculator = RouteCalculator(self.map_path.get() or "kerbinbiomesTrue.png")

            # Convert travel mode to pathfinding mode
            mode_mapping = {
                "Air Travel": "air_travel",
                "Sea Restricted": "sea_restricted",
                "Unrestricted": "unrestricted"
            }
            mode = mode_mapping[self.travel_mode.get()]

            # Calculate route
            path, cost = calculator.calculate_route(
                self.start_coords,
                self.end_coords,
                mode
            )

            # Store the current path and cost
            self.current_path = path
            self.current_cost = cost

            # Redraw everything
            self.redraw_points()

            # Update total cost display
            if cost != float('inf'):
                self.total_cost.set(f"{cost:.2f}")
            else:
                self.total_cost.set("No valid path")

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to compute route: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RoutePlannerGUI(root)
    root.mainloop()