import json
import math
import random
import threading
import tkinter as tk
import webbrowser

from tkinter import ttk, messagebox
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ZIP_SERVICE = "https://api.zippopotam.us/us/"
MAP_SERVICE = "https://overpass-api.de/api/interpreter"

COLORS = [
    "#B9D991", "#E7B582", "#89BDB1", "#D7BDDE",
    "#F0D583", "#A4BDE0", "#DE9C91", "#AAC9A0"
]


def get_json(url, data=None):
    request = Request(
        url,
        data=data,
        headers={
            "User-Agent": "RestaurantFinder/1.0 (personal desktop app)",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=60) as response:
        return json.load(response)


def distance_miles(lat1, lon1, lat2, lon2):
    lat1, lat2 = math.radians(lat1), math.radians(lat2)

    change_lat = lat2 - lat1
    change_lon = math.radians(lon2 - lon1)

    value = (
        math.sin(change_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(change_lon / 2) ** 2
    )

    return 3958.7613 * 2 * math.asin(
        math.sqrt(max(0, min(1, value)))
    )


def search_restaurants(zip_code, radius):
    if (
        len(zip_code) != 5
        or not zip_code.isascii()
        or not zip_code.isdigit()
    ):
        raise ValueError("Enter a five-digit US ZIP code.")

    try:
        location = get_json(ZIP_SERVICE + zip_code)
        place = location["places"][0]

        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
    except Exception:
        raise ValueError(
            "Could not locate that ZIP code. "
            "Check the ZIP code and your internet connection."
        ) from None

    meters = round(radius * 1609.344)

    query = f"""
    [out:json][timeout:45];
    nwr["amenity"="restaurant"]["name"]
      (around:{meters},{latitude},{longitude});
    out center tags;
    """

    try:
        result = get_json(
            MAP_SERVICE,
            urlencode({"data": query}).encode(),
        )
    except Exception:
        raise ValueError(
            "The free map service is busy or unavailable. "
            "Wait a minute and try again, or use a smaller distance."
        ) from None

    if result.get("remark"):
        raise ValueError(
            "The map service could not finish this search. "
            "Try a smaller distance or search again later."
        )

    restaurants = []

    for element in result.get("elements", []):
        tags = element.get("tags", {})
        point = element.get("center", element)

        if "lat" not in point or "lon" not in point:
            continue

        distance = distance_miles(
            latitude,
            longitude,
            point["lat"],
            point["lon"],
        )

        if distance > radius:
            continue

        street = " ".join(
            part for part in [
                tags.get("addr:housenumber", ""),
                tags.get("addr:street", ""),
            ]
            if part
        )

        locality = ", ".join(
            part for part in [
                tags.get("addr:city", ""),
                tags.get("addr:state", ""),
                tags.get("addr:postcode", ""),
            ]
            if part
        )

        address = tags.get("addr:full") or ", ".join(
            part for part in [street, locality] if part
        )

        restaurants.append({
            "name": tags["name"],
            "address": address or "Address not listed in OpenStreetMap",
            "distance": distance,
            "cuisine": tags.get(
                "cuisine", "Not listed"
            ).replace(";", ", ").replace("_", " "),
            "website": (
                tags.get("website")
                or tags.get("contact:website", "")
            ),
            "hours": tags.get("opening_hours", "Not listed"),
            "phone": (
                tags.get("phone")
                or tags.get("contact:phone", "Not listed")
            ),
            "map_url": (
                f"https://www.openstreetmap.org/"
                f"{element['type']}/{element['id']}"
            ),
        })

    restaurants.sort(
        key=lambda restaurant: restaurant["distance"]
    )

    return restaurants


class RestaurantFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Finder")
        self.root.geometry("1050x820")

        self.restaurants = []
        self.selected = None
        self.angle = 0
        self.busy = False

        self.zip_code = tk.StringVar()
        self.radius = tk.DoubleVar(value=5)
        self.status = tk.StringVar(
            value="Enter your ZIP code to begin."
        )

        self.build_window()

        self.zip_code.trace_add("write", self.settings_changed)
        self.radius.trace_add("write", self.settings_changed)

        self.draw_wheel()

    def build_window(self):
        ttk.Label(
            self.root,
            text="Restaurant Finder",
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=(15, 5))

        ttk.Label(
            self.root,
            text="Find nearby food. Spin the wheel. Pick dinner.",
        ).pack()

        controls = ttk.Frame(self.root, padding=15)
        controls.pack(fill="x")

        ttk.Label(
            controls,
            text="US ZIP code:",
        ).grid(row=0, column=0, sticky="w")

        self.zip_entry = ttk.Entry(
            controls,
            textvariable=self.zip_code,
            width=12,
        )
        self.zip_entry.grid(
            row=0, column=1, padx=12, sticky="w"
        )

        self.distance_label = ttk.Label(
            controls,
            text="Distance: 5 miles",
        )
        self.distance_label.grid(
            row=1, column=0, pady=15, sticky="w"
        )

        self.slider = ttk.Scale(
            controls,
            from_=1,
            to=30,
            variable=self.radius,
        )
        self.slider.grid(
            row=1,
            column=1,
            columnspan=2,
            padx=12,
            sticky="ew",
        )

        controls.columnconfigure(2, weight=1)

        self.search_button = ttk.Button(
            controls,
            text="Find restaurants",
            command=self.start_search,
        )
        self.search_button.grid(
            row=0, column=2, sticky="e"
        )

        ttk.Label(
            self.root,
            textvariable=self.status,
            wraplength=980,
        ).pack(pady=5)

        content = ttk.Frame(self.root)
        content.pack(
            fill="both",
            expand=True,
            padx=15,
        )

        left = ttk.Frame(content)
        left.pack(
            side="left",
            fill="both",
            expand=True,
        )

        self.canvas = tk.Canvas(
            left,
            width=470,
            height=470,
            background="#F5F4EF",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.spin_button = ttk.Button(
            left,
            text="SPIN THE WHEEL",
            command=self.spin,
            state="disabled",
        )
        self.spin_button.pack(pady=12)

        right = ttk.Frame(content, padding=15)
        right.pack(
            side="left",
            fill="both",
            expand=True,
        )

        ttk.Label(
            right,
            text="Your restaurant",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        self.details = tk.Text(
            right,
            width=40,
            height=24,
            wrap="word",
            font=("Segoe UI", 11),
            state="disabled",
        )
        self.details.pack(
            fill="both",
            expand=True,
            pady=10,
        )

        self.map_button = ttk.Button(
            right,
            text="Open restaurant on OpenStreetMap",
            command=self.open_map,
            state="disabled",
        )
        self.map_button.pack(fill="x", pady=5)

        self.website_button = ttk.Button(
            right,
            text="Open restaurant website / menu",
            command=self.open_website,
            state="disabled",
        )
        self.website_button.pack(fill="x", pady=5)

        footer = ttk.Frame(self.root, padding=10)
        footer.pack(fill="x")

        attribution = ttk.Label(
            footer,
            text="Map data © OpenStreetMap contributors",
            foreground="blue",
            cursor="hand2",
        )
        attribution.pack()

        attribution.bind(
            "<Button-1>",
            lambda event: webbrowser.open(
                "https://www.openstreetmap.org/copyright"
            ),
        )

        ttk.Label(
            footer,
            text=(
                "ZIP lookup: Zippopotam.us • No API key required\n"
                "Distances are from the ZIP center, not driving distances.\n"
                "Free community data may be incomplete or outdated."
            ),
            justify="center",
        ).pack(pady=4)

    def write_details(self, text):
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", text)
        self.details.configure(state="disabled")

    def settings_changed(self, *_):
        self.distance_label.configure(
            text=f"Distance: {round(self.radius.get())} miles"
        )

        self.restaurants = []
        self.selected = None

        self.spin_button.configure(state="disabled")
        self.map_button.configure(state="disabled")
        self.website_button.configure(state="disabled")

        self.write_details("")
        self.draw_wheel()

        self.status.set(
            "Settings changed. Click Find restaurants."
        )

    def set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"

        for widget in (
            self.zip_entry,
            self.slider,
            self.search_button,
        ):
            widget.configure(state=state)

        self.spin_button.configure(
            state=(
                "normal"
                if self.restaurants and not busy
                else "disabled"
            )
        )

    def start_search(self):
        if self.busy:
            return

        zip_code = self.zip_code.get().strip()
        radius = round(self.radius.get())

        self.restaurants = []
        self.selected = None

        self.map_button.configure(state="disabled")
        self.website_button.configure(state="disabled")

        self.write_details("")
        self.draw_wheel()
        self.set_busy(True)

        self.status.set(
            "Searching free map data… This may take a minute."
        )

        result = {}
        finished = threading.Event()

        def worker():
            try:
                result["restaurants"] = search_restaurants(
                    zip_code, radius
                )
            except Exception as error:
                result["error"] = (
                    str(error)
                    if isinstance(error, ValueError)
                    else "Could not read restaurant data."
                )
            finally:
                finished.set()

        def check_result():
            if not finished.is_set():
                self.root.after(100, check_result)
                return

            if "error" in result:
                self.set_busy(False)
                self.status.set("Search failed.")

                messagebox.showerror(
                    "Search error",
                    result["error"],
                )
                return

            # Use the nearest 20 to keep the wheel readable.
            found = result["restaurants"]
            self.restaurants = found[:20]
            self.angle = 0

            self.draw_wheel()
            self.set_busy(False)

            if not self.restaurants:
                self.status.set(
                    "No mapped restaurants found. "
                    "Try a larger distance."
                )
                return

            self.status.set(
                f"Found {len(found)} mapped restaurants. "
                f"The nearest {len(self.restaurants)} "
                f"are on the wheel."
            )

            self.write_details(
                "RESTAURANT LINEUP\n\n"
                + "\n\n".join(
                    f"{restaurant['name']}\n"
                    f"{restaurant['distance']:.1f} miles"
                    for restaurant in self.restaurants
                )
            )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

        self.root.after(100, check_result)

    def draw_wheel(self):
        self.canvas.delete("all")

        count = len(self.restaurants) or 8
        segment = 360 / count
        center = 235
        radius = 208

        for index in range(count):
            start = self.angle + index * segment

            self.canvas.create_arc(
                center - radius,
                center - radius,
                center + radius,
                center + radius,
                start=start,
                extent=segment,
                fill=COLORS[index % len(COLORS)],
                outline="white",
                width=2,
            )

            middle = math.radians(
                start + segment / 2
            )

            x = center + math.cos(middle) * radius * 0.67
            y = center - math.sin(middle) * radius * 0.67

            name = (
                self.restaurants[index]["name"]
                if self.restaurants
                else "Find food"
            )

            if len(name) > 20:
                name = name[:18] + "…"

            self.canvas.create_text(
                x,
                y,
                text=name,
                width=95,
                font=(
                    "Segoe UI",
                    8 if count > 12 else 10,
                    "bold",
                ),
                fill="#17251D",
            )

        self.canvas.create_oval(
            200,
            200,
            270,
            270,
            fill="#243B2D",
            outline="white",
        )

        self.canvas.create_text(
            center,
            center,
            text="EAT",
            fill="white",
            font=("Segoe UI", 15, "bold"),
        )

        self.canvas.create_polygon(
            222,
            8,
            248,
            8,
            235,
            43,
            fill="#C84F3E",
            outline="white",
        )

    def spin(self):
        if self.busy or not self.restaurants:
            return

        self.set_busy(True)
        self.map_button.configure(state="disabled")
        self.website_button.configure(state="disabled")

        self.write_details("Choosing your restaurant…")

        chosen = random.randrange(
            len(self.restaurants)
        )

        segment = 360 / len(self.restaurants)

        # Align the selected slice with the top pointer.
        target = (
            90 - (chosen + 0.5) * segment
        ) % 360

        start = self.angle
        travel = 360 * 6 + (target - start) % 360
        frames = 150

        def animate(frame=0):
            progress = frame / frames
            eased = 1 - (1 - progress) ** 4

            self.angle = start + travel * eased
            self.draw_wheel()

            if frame < frames:
                self.root.after(
                    20,
                    animate,
                    frame + 1,
                )
            else:
                self.angle %= 360
                self.set_busy(False)

                self.show_restaurant(
                    self.restaurants[chosen]
                )

        animate()

    def show_restaurant(self, restaurant):
        self.selected = restaurant

        self.write_details(
            f"{restaurant['name']}\n\n"
            f"ADDRESS\n"
            f"{restaurant['address']}\n\n"
            f"DISTANCE\n"
            f"{restaurant['distance']:.1f} miles from ZIP center\n\n"
            f"CUISINE\n"
            f"{restaurant['cuisine']}\n\n"
            f"PHONE\n"
            f"{restaurant['phone']}\n\n"
            f"OPENING HOURS\n"
            f"{restaurant['hours']}"
        )

        self.status.set(
            f"Tonight's pick: {restaurant['name']}"
        )

        self.map_button.configure(state="normal")

        self.website_button.configure(
            state=(
                "normal"
                if restaurant["website"]
                else "disabled"
            )
        )

    def open_map(self):
        if self.selected:
            webbrowser.open(
                self.selected["map_url"]
            )

    def open_website(self):
        if not self.selected:
            return

        url = self.selected["website"]

        if url and "://" not in url:
            url = "https://" + url

        if url.startswith(("https://", "http://")):
            webbrowser.open(url)


if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantFinder(root)
    root.mainloop()
