"""Offline demonstration of separate login handlers; never requests real codes.

    python examples/stepwise_login.py --demo

For application integration see docs/stepwise_login.md. The demonstration alone
uses the smoke suite's synthetic transport; LoginFlow/SRP/session code are real.
"""
import argparse
import asyncio
from pathlib import Path
import socket
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tgdata import LoginFlow


async def demo():
    from tgdata.smoke_tests.test_41_stepwise_login import fixture, PHONE, CODE, PASSWORD

    # Demonstration stores only. Real handlers need private durable storage and
    # exclusive use of each latest flow checkpoint.
    private_flows, sessions = {}, {}
    with fixture(two_factor=True) as (config, service):
        flow = LoginFlow(config)
        print('After phone:', (await flow.start(PHONE)).step)
        private_flows['demo-flow'] = flow.export_state()

        flow = LoginFlow(config, state=private_flows['demo-flow'])
        print('After code:', (await flow.submit_code(CODE)).step)
        private_flows['demo-flow'] = flow.export_state()

        flow = LoginFlow(config, state=private_flows['demo-flow'])
        print('After password:', (await flow.submit_password(PASSWORD)).step)
        sessions['demo-account'] = flow.session_data
        del private_flows['demo-flow']
        assert service.srp_accepted == 1 and sessions['demo-account']
        print('Finished session retained privately; no live Telegram connection.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Run with synthetic replies only')
    args = parser.parse_args()
    if not args.demo:
        parser.error('Use --demo; integrate real inputs through the documented API.')
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network forbidden')):
        asyncio.run(demo())
