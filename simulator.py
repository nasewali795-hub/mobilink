#!/usr/bin/env python3
"""
Dummy Gateway Simulator
Simulates an Android gateway phone for testing without physical hardware.
"""
import asyncio
import json
import random
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

GATEWAY_ID = "gateway-1"
SERVER_URL = "ws://localhost:8000/gateway/ws/connect/gateway-1"

class DummyGateway:
    def __init__(self):
        self.websocket = None
        self.running = False
        self.transaction_count = 0

    async def connect(self):
        print(f"[SIMULATOR] Connecting to {SERVER_URL}")
        try:
            self.websocket = await websockets.connect(SERVER_URL)
            print("[SIMULATOR] Connected to backend")
            self.running = True
            return True
        except Exception as e:
            print(f"[SIMULATOR] Connection failed: {e}")
            return False

    async def listen(self):
        if not self.websocket:
            print("[SIMULATOR] Not connected")
            return

        try:
            async for message in self.websocket:
                data = json.loads(message)
                print(f"[SIMULATOR] Received: {data.get('type', 'unknown')}")
                
                if data.get("type") == "execute_ussd":
                    await self.handle_execute_ussd(data)
                elif data.get("type") == "ping":
                    await self.send({"type": "pong", "timestamp": time.time()})
                elif data.get("type") == "cancel_transaction":
                    print("[SIMULATOR] Transaction cancelled")
                    
        except websockets.exceptions.ConnectionClosed:
            print("[SIMULATOR] Connection closed")
            self.running = False
        except Exception as e:
            print(f"[SIMULATOR] Error: {e}")
            self.running = False

    async def handle_execute_ussd(self, command):
        transaction_id = command.get("transaction_id")
        network = command.get("network", "MTN")
        operation = command.get("operation", "cash_out")
        amount = command.get("amount", 0)
        customer_phone = command.get("customer_phone", "")

        print(f"[SIMULATOR] Processing {operation} of {amount} to {customer_phone} on {network}")

        await self.send_transaction_update(transaction_id, "executing_ussd", "Dialing USSD code...")
        await asyncio.sleep(1.5)

        await self.send_transaction_update(transaction_id, "processing", "Entering phone number...")
        await asyncio.sleep(0.8)

        await self.send_transaction_update(transaction_id, "processing", "Entering amount...")
        await asyncio.sleep(0.8)

        if operation == "cash_out":
            await self.send_transaction_update(transaction_id, "processing", "Entering PIN...")
            await asyncio.sleep(1.0)

        await self.send_transaction_update(transaction_id, "processing", "Waiting for confirmation...")
        await asyncio.sleep(1.5)

        success = random.random() > 0.1

        if success:
            mno_ref = f"TXN{random.randint(100000, 999999)}"
            new_balance = random.randint(10000, 50000)
            
            await self.send_transaction_update(transaction_id, "success", mno_ref)
            
            await asyncio.sleep(0.5)
            await self.send_sms_webhook(
                transaction_id=transaction_id,
                network=network,
                amount=amount,
                mno_ref=mno_ref,
                new_balance=new_balance
            )
            print(f"[SIMULATOR] Transaction {transaction_id} completed successfully")
        else:
            await self.send_transaction_update(transaction_id, "failed", "Insufficient customer balance")
            print(f"[SIMULATOR] Transaction {transaction_id} failed")

        self.transaction_count += 1

    async def send_transaction_update(self, transaction_id, status, detail=None):
        payload = {
            "type": "transaction_update",
            "transaction_id": transaction_id,
            "status": status,
            "network": "MTN",
            "timestamp": time.time()
        }
        if detail:
            payload["detail"] = detail
        
        await self.send(payload)

    async def send_sms_webhook(self, transaction_id, network, amount, mno_ref, new_balance):
        sms_messages = {
            "MTN": f"MTN Mobile Money\nTransaction ID: {mno_ref}\nAmount: {amount}\nNew Balance: {new_balance}\nYou have received {amount} from customer.",
            "Airtel": f"Airtel Money\nTransaction: {mno_ref}\nAmount: {amount}\nBalance: {new_balance}\nPayment received successfully.",
            "Zamtel": f"Zamtel M-money\nRef: {mno_ref}\nAmount: {amount}\nNew Bal: {new_balance}\nTransaction successful."
        }
        
        message = sms_messages.get(network, sms_messages["MTN"])
        
        payload = {
            "type": "sms_webhook",
            "sender": f"+26097{random.randint(1000000, 9999999)}",
            "message": message,
            "received_at": datetime.utcnow().isoformat(),
            "transaction_id": transaction_id,
            "parsed_status": "success",
            "parsed_transaction_id": mno_ref,
            "parsed_amount": amount,
            "parsed_reference": mno_ref
        }
        
        await self.send(payload)

    async def send(self, data):
        if self.websocket and self.running:
            try:
                await self.websocket.send(json.dumps(data))
            except Exception as e:
                print(f"[SIMULATOR] Send error: {e}")

    async def close(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
            print("[SIMULATOR] Disconnected")

    async def run(self):
        print("=" * 60)
        print("  DUMMY GATEWAY SIMULATOR")
        print("  Simulates Android gateway phone for testing")
        print("=" * 60)
        print()
        
        while True:
            connected = await self.connect()
            if connected:
                await self.listen()
            
            if self.running:
                await asyncio.sleep(3)
            else:
                print("[SIMULATOR] Retrying in 5 seconds...")
                await asyncio.sleep(5)

def main():
    simulator = DummyGateway()
    try:
        asyncio.run(simulator.run())
    except KeyboardInterrupt:
        print("\n[SIMULATOR] Shutting down...")
        asyncio.run(simulator.close())

if __name__ == "__main__":
    main()
