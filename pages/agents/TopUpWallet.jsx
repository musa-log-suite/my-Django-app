import React, { useState } from 'react';
import axiosInstance from '../../services/axiosInstance';

const TopUpWallet = () => {
  const [amount, setAmount] = useState('');

  const handleTopUp = async () => {
    const res = await axiosInstance.post('/wallets/topup/', { amount });
    alert('Top-up initiated!');
    // Later: handle redirect to Flutterwave/Paystack
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold">Top Up Wallet</h2>
      <div className="mt-4 space-y-4">
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder="Amount (₦)"
          className="input"
        />
        <button onClick={handleTopUp} className="btn">Top Up</button>
      </div>
    </div>
  );
};

export default TopUpWallet;