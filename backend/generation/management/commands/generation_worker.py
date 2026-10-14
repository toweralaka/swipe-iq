import time
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from generation.configuration import require_configuration
from generation.services import recover_interrupted, process_one
from generation.worker_lock import worker_lock


class Command(BaseCommand):
    help = "Process AI text draft requests. Requires paid-provider configuration; never run two workers against one database."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process at most one saved result/request and exit.")
        parser.add_argument("--poll-seconds", type=int, default=2)

    def handle(self, *args, **options):
        try:
            require_configuration()
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from None
        if not 1 <= options["poll_seconds"] <= 60:
            raise CommandError("poll-seconds must be between 1 and 60.")
        with worker_lock():
            recovered = recover_interrupted()
            self.stdout.write(f"Worker started. {recovered} interrupted requests marked for checking.")
            try:
                while True:
                    close_old_connections()
                    worked = process_one()
                    if options["once"]:
                        break
                    if not worked:
                        time.sleep(options["poll_seconds"])
            except KeyboardInterrupt:
                self.stdout.write("Worker stopped. Restarting will check interrupted requests without resending them.")
