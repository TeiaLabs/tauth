# Installation

To use `tauth`, you need to have Python 3.12 or higher installed.

If you are interesed in contributing to TAuth's develpoment, we recommend using the `uv` and Docker setup provided in the repository.

Follow these steps:

1. Clone the git repository
2. Navigate to the repository folder
3. Run the command `uv sync` to generate the requirements lock file
4. Copy the contents of `example.env` into `.env` and change the environment variables as needed
5. Run Docker commands to run the application. Example: `docker compose up --build --watch --remove-orphans tauth`
6. The package is automatically installed in editable mode in the development image. That is, all changes will be reflected in the container without needing to rebuild the image.
