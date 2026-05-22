from dotenv import load_dotenv

from dashboard.ui import render_dashboard


def main() -> None:
    """Load local settings and start the Streamlit dashboard."""

    load_dotenv()
    render_dashboard()


if __name__ == "__main__":
    main()
