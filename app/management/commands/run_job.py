"""Run a single scheduled job once, by name.

The job list is derived from the APScheduler registrations in
[app/scheduled_job/updater.py](app/scheduled_job/updater.py), so a job added
there is runnable here immediately — there is no separate registry to update.

    python manage.py run_job --list
    python manage.py run_job check_orders
    python manage.py run_job check_orders sync_prices
"""

import time
import warnings

from django.core.management.base import BaseCommand, CommandError
from telegram.warnings import PTBUserWarning

from app.scheduled_job.updater import jobs

warnings.filterwarnings(
    "ignore",
    message=r"If 'per_message=False'.*",
    category=PTBUserWarning,
)


def get_jobs():
    """Map every scheduled job's name to its callable, in registration order."""
    return {job.name: job.func for job in jobs.scheduler.get_jobs()}


class Command(BaseCommand):
    help = "Run one or more scheduled jobs once, immediately, by name"

    def add_arguments(self, parser):
        parser.add_argument(
            "names",
            nargs="*",
            help="Names of the jobs to run (see --list)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            dest="list_jobs",
            help="List the runnable job names and exit",
        )

    def handle(self, *args, **options):
        available = get_jobs()

        if options["list_jobs"]:
            self.print_jobs()
            return

        names = options["names"]
        if not names:
            raise CommandError(
                "Specify at least one job name, or use --list to see what is available."
            )

        unknown = [name for name in names if name not in available]
        if unknown:
            raise CommandError(
                "Unknown job(s): {}. Use --list to see what is available.".format(
                    ", ".join(unknown)
                )
            )

        for name in names:
            self.run_job(name, available[name])

    def print_jobs(self):
        self.stdout.write("Available jobs:")
        for job in jobs.scheduler.get_jobs():
            self.stdout.write(f"  {job.name:<40} {job.trigger}")

    def run_job(self, name, func):
        self.stdout.write(f"Running {name} ...")
        started = time.monotonic()
        try:
            func()
        except Exception as exc:
            # The jobs wrap themselves in @notify_on_exception(reraise=False), so
            # reaching here means something escaped that net; surface it properly
            # rather than letting the remaining jobs run as if nothing happened.
            raise CommandError(f"{name} failed: {exc}") from exc

        elapsed = time.monotonic() - started
        self.stdout.write(self.style.SUCCESS(f"{name} finished in {elapsed:.1f}s"))
