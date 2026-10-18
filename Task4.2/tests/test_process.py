import os
import unittest
import uuid

from pyzeebe import ZeebeClient, create_insecure_channel


@unittest.skipUnless(os.getenv('RUN_E2E') == '1', 'set RUN_E2E=1 with the stack running')
class PaymentProcessTest(unittest.IsolatedAsyncioTestCase):
    async def run_payment(self, mode, **options):
        variables = {
            'payment_id': f'test-{uuid.uuid4().hex[:10]}',
            'amount': 10000, 'currency': 'RUB', 'fraud_mode': mode,
            'review_seconds': 3, 'check_timeout': 'PT3S',
            'transfer_fails': False, 'fail_once': '',
            'security_notified': False, 'customer_notified': False,
            **options,
        }
        async with create_insecure_channel(grpc_address=os.getenv('ZEEBE_ADDRESS', 'localhost:26500')) as channel:
            result = await ZeebeClient(channel).run_process_with_result(
                'orchestrpay-payment', variables, timeout=45000,
            )
        return result.variables

    def check_success(self, result):
        self.assertEqual(result['status'], 'SUCCEEDED')
        self.assertEqual(result['debited'], 10000)
        self.assertEqual(result['transferred'], 10000)
        self.assertEqual(result['refunded'], 0)
        self.assertTrue(result['customer_notified'])

    async def test_allow(self):
        self.check_success(await self.run_payment('ALLOW'))

    async def test_deny(self):
        result = await self.run_payment('DENY')
        self.assertEqual(result['status'], 'REFUNDED')
        self.assertEqual(result['refunded'], 10000)
        self.assertEqual(result['transferred'], 0)
        self.assertTrue(result['security_notified'])
        self.assertTrue(result['customer_notified'])

    async def test_check_cutoff(self):
        result = await self.run_payment('TIMEOUT')
        self.check_success(result)
        self.assertEqual(result['decision_source'], 'cutoff')

    async def test_manual_cutoff(self):
        result = await self.run_payment('MANUAL')
        self.check_success(result)
        self.assertEqual(result['decision_source'], 'cutoff')

    async def test_transfer_rejection(self):
        result = await self.run_payment('ALLOW', transfer_fails=True)
        self.assertEqual(result['status'], 'REFUNDED')
        self.assertEqual(result['refunded'], 10000)
        self.assertEqual(result['transferred'], 0)
        self.assertFalse(result['security_notified'])

    async def test_refund_retry(self):
        result = await self.run_payment('DENY', fail_once='refund-funds')
        self.assertEqual(result['status'], 'REFUNDED')
        self.assertEqual(result['refunded'], 10000)
        self.assertTrue(result['customer_notified'])

    async def test_notification_retry(self):
        self.check_success(await self.run_payment('ALLOW', fail_once='notify-customer'))


if __name__ == '__main__':
    unittest.main()
