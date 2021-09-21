def main(workers: int = 1, threads: int = 5):
    import sys

    from gunicorn.app.wsgiapp import run

    sys.argv.extend((f"--workers={workers}", f"--threads={threads}", "wallet.api.app:create_app()"))
    run()


if __name__ == "__main__":
    main()
