import unittest
import json
from app import app, create_app
from app.state import seed_sample_data

class MicrofinanceApiTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        seed_sample_data()  # Reset sample data before each test

    def get_token(self, username, password):
        res = self.client.post('/login', json={'username': username, 'password': password})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        return data['token']

    def test_login_success_and_failure(self):
        # Valid login
        res = self.client.post('/login', json={'username': 'agent1', 'password': 'pass123'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['role'], 'Agent')

        # Invalid login
        res_fail = self.client.post('/login', json={'username': 'agent1', 'password': 'wrongpassword'})
        self.assertEqual(res_fail.status_code, 401)

    def test_add_client_rbac(self):
        agent_token = self.get_token('agent1', 'pass123')
        hq_token = self.get_token('hq_admin', 'hq123')

        # Agent can add client
        res = self.client.post('/add_client', json={
            'client_name': 'Kondwani Phiri',
            'phone': '+260975556677',
            'nrc': '556677/88/1'
        }, headers={'Authorization': f'Bearer {agent_token}'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('added to ShopA', res.get_json()['message'])

        # HQ can also add client
        res_hq = self.client.post('/add_client', json={
            'client_name': 'HQ Farmer',
            'shop': 'ShopA'
        }, headers={'Authorization': f'Bearer {hq_token}'})
        self.assertEqual(res_hq.status_code, 200)

    def test_fertilizer_loan_flow(self):
        agent_token = self.get_token('agent1', 'pass123')
        headers = {'Authorization': f'Bearer {agent_token}'}

        # First add client
        self.client.post('/add_client', json={'client_name': 'Moses Zimba'}, headers=headers)

        # Add fertilizer loan: 3 bags @ 1:4 ratio -> 12 expected maize bags, ZMW 1350 downpayment
        loan_res = self.client.post('/fertilizer_loans/add', json={
            'client_name': 'Moses Zimba',
            'fertilizer_type': 'NPK Compound',
            'fertilizer_bags': 3,
            'repayment_ratio': '1:4'
        }, headers=headers)
        self.assertEqual(loan_res.status_code, 200)
        loan_data = loan_res.get_json()['loan']

        self.assertEqual(loan_data['expected_maize_bags'], 12)
        self.assertEqual(loan_data['downpayment_cash'], 1350)
        self.assertEqual(loan_data['balance_remaining'], 12)

        # Make repayment of 5 bags
        repay_res = self.client.post('/loans/repay', json={
            'loan_id': loan_data['id'],
            'amount': 5,
            'notes': 'Partial harvest repayment'
        }, headers=headers)
        self.assertEqual(repay_res.status_code, 200)
        self.assertEqual(repay_res.get_json()['new_balance'], 7)

        # Repay remaining 7 bags -> status becomes completed
        repay_final = self.client.post('/loans/repay', json={
            'loan_id': loan_data['id'],
            'amount': 7,
            'notes': 'Final harvest repayment'
        }, headers=headers)
        self.assertEqual(repay_final.get_json()['status'], 'completed')
        self.assertEqual(repay_final.get_json()['new_balance'], 0)

    def test_asset_finance_loan_flow(self):
        agent_token = self.get_token('agent1', 'pass123')
        headers = {'Authorization': f'Bearer {agent_token}'}

        self.client.post('/add_client', json={'client_name': 'Peter Zulu'}, headers=headers)

        # Asset value 10,000, 20% downpayment (2,000), Net loan 8,000, 15% interest -> Total 9,200
        loan_res = self.client.post('/asset_finance_loans/add', json={
            'client_name': 'Peter Zulu',
            'asset_type': 'Treadle Irrigation Pump',
            'asset_value': 10000,
            'downpayment_percent': 20,
            'interest_rate': 15
        }, headers=headers)
        self.assertEqual(loan_res.status_code, 200)
        loan_data = loan_res.get_json()['loan']

        self.assertEqual(loan_data['downpayment_cash'], 2000)
        self.assertEqual(loan_data['total_repayable'], 9200)
        self.assertEqual(loan_data['balance_remaining'], 9200)

    def test_cash_loan_flow(self):
        hq_token = self.get_token('hq_admin', 'hq123')
        headers = {'Authorization': f'Bearer {hq_token}'}

        self.client.post('/add_client', json={'client_name': 'Grace Musonda'}, headers=headers)

        # Cash loan 3,000 @ 10% interest -> 3,300 total repayable
        loan_res = self.client.post('/cash_loans/add', json={
            'client_name': 'Grace Musonda',
            'shop': 'ShopA',
            'loan_amount': 3000,
            'interest_rate': 10,
            'purpose': 'Seedlings Purchase'
        }, headers=headers)
        self.assertEqual(loan_res.status_code, 200)
        loan_data = loan_res.get_json()['loan']

        self.assertEqual(loan_data['total_repayable'], 3300)
        self.assertEqual(loan_data['balance_remaining'], 3300)

    def test_dashboard_and_hierarchy_role_filtering(self):
        agent_token = self.get_token('agent1', 'pass123')
        hq_token = self.get_token('hq_admin', 'hq123')

        # Agent hierarchy scope (ShopA only)
        res_agent = self.client.get('/hierarchy', headers={'Authorization': f'Bearer {agent_token}'})
        tree_agent = res_agent.get_json()['hierarchy']
        self.assertIn('Eastern Province', tree_agent)
        self.assertIn('ShopA', tree_agent['Eastern Province']['DistrictA']['VillageX'])
        self.assertNotIn('ShopB', tree_agent['Eastern Province']['DistrictA'].get('VillageY', {}))

        # HQ hierarchy scope (all shops)
        res_hq = self.client.get('/hierarchy', headers={'Authorization': f'Bearer {hq_token}'})
        tree_hq = res_hq.get_json()['hierarchy']
        self.assertIn('ShopA', tree_hq['Eastern Province']['DistrictA']['VillageX'])
        self.assertIn('ShopB', tree_hq['Eastern Province']['DistrictA']['VillageY'])

if __name__ == '__main__':
    unittest.main()
