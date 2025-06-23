# DIY Under-Door Fan Duct

This repo holds the CadQuery code for the fan duct I designed to stop waking up groggy. It attaches to a standard 120mm PC fan, sits on the floor, and pushes air out under the door.

![CAD model of the v4 fan duct](https://raw.githubusercontent.com/andrey-lepekhin/diy-door-fan/main/2025-06-23-v4-cad.jpg)

### The Backstory

The project started when I found out my sealed bedroom's CO₂ levels were hitting 1,700 ppm overnight. After a few experiments with pizza boxes and over-engineered prototypes, I landed on this simple, effective design.

I wrote the full story here: **[DIY Door Fan to Fix My Groggy Mornings](https://www.lepekhin.com/2025/06/22/DIY-Door-Fan-to-Fix-My-Groggy-Mornings)**.

## Neat Stuff

- Fully parametric. Tweak all the numbers in `constants.py` to fit your door and fan.

- Quiet & efficient. The smooth lofted transition minimizes air noise and friction.

- Simple print, no supports needed.

## Make Your Own

### You'll need:
- Python 3.11+
- [uv](https://github.com/astral-sh/uv), or any tool that can install dependencies from a `pyproject.toml` file.

### Steps:

1.  **Clone the repo:**
    ```sh
    git clone https://github.com/andrey-lepekhin/diy-door-fan.git
    cd diy-door-fan
    ```

2.  **Install the dependencies:**
    This sets up a virtual environment and grabs everything you need.
    ```sh
    uv sync
    ```

3.  **Tweak the model (optional):**
    Open `constants.py` and change the numbers to fit your setup.

4.  **Generate the STL:**
    ```sh
    uv run main.py
    ```
    You'll find your file ready to slice in the `stl/` directory.

5.  **See a live 3D preview (optional):**
    ```sh
    uv run CQ-editor
    ```
    Then, open `main.py` from inside the editor.

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.