import unittest

from domain import apply_step


class PaymentRulesTest(unittest.TestCase):
    def setUp(self):
        self.payment = {
            'amount': 10000, 'currency': 'RUB', 'decision': 'ALLOW',
            'debited': 10000, 'transferred': 0, 'refunded': 0,
            'transfer_fails': False,
        }

    def test_refund_is_rejected_after_transfer(self):
        self.payment['transferred'] = 10000
        with self.assertRaises(ValueError):
            apply_step('refund-funds', self.payment)

    def test_transfer_is_rejected_after_refund(self):
        self.payment['refunded'] = 10000
        with self.assertRaises(ValueError):
            apply_step('transfer-funds', self.payment)

    def test_refund_requires_debit(self):
        self.payment['debited'] = 0
        with self.assertRaises(ValueError):
            apply_step('refund-funds', self.payment)

    def test_repeated_simulated_refund_does_not_accumulate(self):
        self.payment.update(apply_step('refund-funds', self.payment))
        self.payment.update(apply_step('refund-funds', self.payment))
        self.assertEqual(self.payment['refunded'], 10000)

    def test_invalid_amounts_are_rejected(self):
        for amount in (0, -100, True, 10.5):
            with self.subTest(amount=amount):
                self.payment['amount'] = amount
                with self.assertRaises(ValueError):
                    apply_step('create-payment', self.payment)

    def test_final_decision_cannot_remain_manual(self):
        self.payment['decision'] = 'MANUAL'
        with self.assertRaises(ValueError):
            apply_step('record-decision', self.payment)


if __name__ == '__main__':
    unittest.main()
