import asyncio
import json
import logging
import os
import signal

from pyzeebe import Job, ZeebeWorker, create_insecure_channel

from domain import apply_step


STEPS = (
    "create-payment", "debit-funds", "check-fraud", "prepare-review",
    "allow-cutoff", "record-decision", "transfer-funds", "prepare-refund",
    "refund-funds", "notify-security", "finish-refund", "notify-customer",
)
logger = logging.getLogger("payment")


async def handle_error(error, job, controller):
    logger.error("payment=%s step=%s retries=%s error=%s",
                 job.variables.get("payment_id"), job.type, job.retries, error)
    await controller.set_failure_status(str(error), retry_back_off_ms=1000)


async def handle_job(job: Job):
    if job.variables.get("fail_once") == job.type and job.retries == 3:
        raise ConnectionError("simulated temporary failure before the operation")
    result = apply_step(job.type, job.variables)
    logger.info("payment=%s process=%s job=%s step=%s result=%s",
                job.variables["payment_id"], job.process_instance_key, job.key,
                job.type, json.dumps(result, ensure_ascii=False))
    return result


async def main():
    address = os.getenv("ZEEBE_ADDRESS", "localhost:26500")
    async with create_insecure_channel(grpc_address=address) as channel:
        worker = ZeebeWorker(channel, name="payment-worker", exception_handler=handle_error)
        for step in STEPS:
            worker.task(task_type=step)(handle_job)
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))
        logger.info("worker ready address=%s steps=%s", address, ",".join(STEPS))
        await worker.work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("pyzeebe").setLevel(logging.WARNING)
    asyncio.run(main())
