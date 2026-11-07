# Restaurant Finder

A Python desktop app that finds nearby restaurants using your US ZIP code and spins a wheel to choose where to eat.

No API keys or additional Python packages are required.

## Features

- Search restaurants by US ZIP code.
- Adjust the search distance from 1 to 30 miles.
- Spin a wheel containing the nearest 20 mapped restaurants.
- View the selected restaurant's address, cuisine, phone number, and opening hours when available.
- Open the restaurant on OpenStreetMap.
- Visit the restaurant's website or menu when a website is available.

## Requirements

- Python 3.10 or newer.
- Tkinter, included with the standard Windows Python installation.
- An internet connection.

## Download

1. Click **Code** on this GitHub repository.
2. Select **Download ZIP**.
3. Extract the downloaded ZIP.

## Run on Windows

Open PowerShell in the extracted folder and run:

```powershell
py "restaurant finder.py"
```

If the Python file is directly in your Downloads folder, run:

```powershell
py "$HOME\Downloads\restaurant finder.py"
```

## Run in Visual Studio

1. Install the **Python development** workload through Visual Studio Installer.
2. Create a **Python Application** project.
3. Add `restaurant finder.py` to the project.
4. In Solution Explorer, right-click the file and select **Set as Startup File**.
5. Select **Debug → Start Without Debugging**.

## How to Use

1. Enter your five-digit US ZIP code.
2. Move the distance slider to choose a radius between 1 and 30 miles.
3. Click **Find restaurants**.
4. Wait for the search to finish.
5. Click **SPIN THE WHEEL**.
6. View your selected restaurant and use the map or website buttons.

Changing the ZIP code or distance requires another search.

## Data Sources

- ZIP code locations: [Zippopotam.us](https://www.zippopotam.us/)
- Restaurant searches: [Overpass API](https://overpass-api.de/)
- Map data: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the Open Database License.

The MIT license covers this application's code. Third-party data retains its own licensing terms.

## Limitations

- Distances are straight-line miles from the ZIP code's center, not driving distances.
- The wheel includes up to 20 nearest mapped restaurants.
- Each restaurant on the wheel has an equal chance of selection.
- Only named locations tagged as restaurants are searched. Some cafes and fast-food locations may be excluded.
- Community map data may be missing or outdated.
- Opening hours are displayed as recorded; the app does not check whether a restaurant is currently open.
- Duplicate restaurant entries may appear.
- Public search services may be slow or temporarily unavailable. Wait before retrying failed searches.
- Popular menu items and average prices are not included.

## Privacy

The entered ZIP code is sent to Zippopotam.us. Its coordinates and your search radius are sent to the Overpass API.

The app does not intentionally save your searches.

## Troubleshooting

### Python cannot find the file

Open PowerShell in the folder containing `restaurant finder.py`, or use the full file path in quotation marks.

### The search fails

Check your internet connection and ZIP code. If the map service is busy, wait a minute and try a smaller distance.

### No restaurants appear

Increase the distance. Some restaurants may not be recorded in OpenStreetMap.

## License

This project's code is available under the MIT License. See `LICENSE`.

## Hosting

This is a desktop application. GitHub shares the source code; GitHub Pages cannot run the Python desktop app.
