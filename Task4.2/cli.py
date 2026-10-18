import argparse
import asyncio
import json
import os
import uuid
from dataclasses import asdict

from pyzeebe import ZeebeClient, create_insecure_channel


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["ALLOW", "DENY", "MANUAL", "TIMEOUT"], default="ALLOW")
    parser.add_argument("--payment-id", default=f"pay-{uuid.uuid4().hex[:10]}")
    parser.add_argument("--amount", type=positive_int, default=10000)
    parser.add_argument("--review-seconds", type=positive_int, default=1200)
    parser.add_argument("--check-seconds", type=positive_int, default=30)
    parser.add_argument("--transfer-fails", action="store_true")
    parser.add_argument("--fail-once", choices=["transfer-funds", "refund-funds", "notify-customer"], default="")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--wait-seconds", type=positive_int, default=90)
    return parser.parse_args()


async def start(args):
    variables = {
        "payment_id": args.payment_id,
        "amount": args.amount,
        "currency": "RUB",
        "fraud_mode": args.mode,
        "review_seconds": args.review_seconds,
        "check_timeout": f"PT{args.check_seconds}S",
        "transfer_fails": args.transfer_fails,
        "fail_once": args.fail_once,
        "security_notified": False,
        "customer_notified": False,
    }
    async with create_insecure_channel(grpc_address=os.getenv("ZEEBE_ADDRESS", "localhost:26500")) as channel:
        client = ZeebeClient(channel)
        if args.wait:
            result = await client.run_process_with_result(
                "orchestrpay-payment", variables, timeout=args.wait_seconds * 1000,
            )
        else:
            result = await client.run_process("orchestrpay-payment", variables)
        print(json.dumps({"payment_id": args.payment_id, **asdict(result)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(start(arguments()))
