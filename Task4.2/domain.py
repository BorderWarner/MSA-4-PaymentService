from datetime import datetime, timedelta, timezone


def apply_step(step, data):
    amount = data["amount"]
    if step == "create-payment":
        if type(amount) is not int or amount <= 0:
            raise ValueError("amount must be a positive integer in minor units")
        if data["currency"] != "RUB":
            raise ValueError("the prototype supports RUB only")
        return {"status": "CREATED", "debited": 0, "transferred": 0, "refunded": 0}
    if step == "debit-funds":
        return {"debited": amount, "status": "DEBITED"}
    if step == "check-fraud":
        decision = data["fraud_mode"]
        if decision not in {"ALLOW", "DENY", "MANUAL", "TIMEOUT"}:
            raise ValueError("unknown fraud mode")
        return {
            "decision": "PENDING" if decision == "TIMEOUT" else decision,
            "status": "CHECK_PENDING",
            "decision_source": "fraud",
        }
    if step == "prepare-review":
        deadline = datetime.now(timezone.utc) + timedelta(seconds=data["review_seconds"])
        return {"status": "MANUAL_REVIEW", "review_deadline": deadline.isoformat()}
    if step == "allow-cutoff":
        return {"decision": "ALLOW", "decision_source": "cutoff"}
    if step == "record-decision":
        if data["decision"] not in {"ALLOW", "DENY"}:
            raise ValueError("a final decision must be ALLOW or DENY")
        return {"status": "APPROVED" if data["decision"] == "ALLOW" else "BLOCKED"}
    if step == "transfer-funds":
        if data["decision"] != "ALLOW" or data["refunded"]:
            raise ValueError("transfer is not allowed")
        if data["transfer_fails"]:
            return {"transfer_ok": False, "status": "REFUND_PENDING", "refund_reason": "transfer_failed"}
        return {"transfer_ok": True, "transferred": amount, "status": "SUCCEEDED"}
    if step == "prepare-refund":
        return {
            "status": "REFUND_PENDING",
            "refund_reason": "fraud_denied" if data["decision"] == "DENY" else "transfer_failed",
        }
    if step == "refund-funds":
        if data["debited"] != amount or data["transferred"]:
            raise ValueError("refund requires a debit and no completed transfer")
        return {"refunded": amount}
    if step == "notify-security":
        return {"security_notified": data["decision"] == "DENY"}
    if step == "finish-refund":
        if data["refunded"] != amount:
            raise ValueError("refund has not completed")
        return {"status": "REFUNDED"}
    if step == "notify-customer":
        return {"customer_notified": True}
    raise ValueError(f"unknown step: {step}")
