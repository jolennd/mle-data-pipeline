"""python -m flows <YYYY-MM> | all | serve"""

import sys

from .green_trips import green_trips_all, green_trips_flow

MONTHLY_CRON = "0 6 1 * *"  # 06:00 on the first day of each month


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        raise SystemExit("usage: python -m flows <YYYY-MM> | all | serve")
    arg = argv[0]
    if arg == "serve":
        green_trips_all.serve(name="green-trips-monthly", cron=MONTHLY_CRON)
    elif arg == "all":
        green_trips_all()
    else:
        green_trips_flow(arg)


if __name__ == "__main__":
    main(sys.argv[1:])
