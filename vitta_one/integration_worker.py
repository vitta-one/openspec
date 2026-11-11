"""Run every five minutes: python -m vitta_one.integration_worker (no in-memory queue)."""
import argparse
import logging
from threading import Event
import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from vitta_one.financial.asaas import ConfigurationError
from vitta_one.financial.service import process_events
from vitta_one.notifications.service import enqueue_reminders, process_outbox, apply_delivery_events


def run_batch(limit: int):
    with rx.session() as db:
        try:
            process_events(db, limit=limit)
        except ConfigurationError:
            db.rollback()
        enqueue_reminders(db)
        process_outbox(db, limit=limit)
        apply_delivery_events(db)


def main():
    parser = argparse.ArgumentParser(description="Processar integrações Vitta-One em lote limitado.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--watch", action="store_true", help="Executar um lote a cada cinco minutos até interrupção.")
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit deve estar entre 1 e 100")
    stop = Event()
    try:
        while True:
            try:
                run_batch(args.limit)
            except SQLAlchemyError:
                # Never print exception text: SQL parameters may contain personal data.
                logging.getLogger(__name__).error("integration_worker database_unavailable")
                if not args.watch:
                    raise SystemExit(1) from None
            if not args.watch:
                break
            stop.wait(300)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
