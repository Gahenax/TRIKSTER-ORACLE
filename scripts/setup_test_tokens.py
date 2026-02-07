# -*- coding: utf-8 -*-
"""Setup tokens for smoke test"""
import sys
sys.path.insert(0, '../backend')

from app.core.tokens import get_ledger

ledger = get_ledger()
ledger.set_balance('smoke_test_user', 20)
print(f'[OK] Balance set: {ledger.get_balance("smoke_test_user")} tokens')
