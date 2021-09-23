import sys

from gunicorn.app.wsgiapp import run as run_server


def main(workers: int = 1, threads: int = 5):
    sys.argv.extend((f"--workers={workers}", f"--threads={threads}", "tilapia.api.app:create_app()"))
    run_server()


if __name__ == "__main__":
    main()
