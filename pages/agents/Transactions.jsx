import React, { useEffect, useState } from 'react';
import axiosInstance from '../../services/axiosInstance';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    axiosInstance.get('/wallets/transactions/')
      .then(res => setTransactions(res.data));
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold">Recent Transactions</h2>
      <table className="w-full mt-4 border">
        <thead>
          <tr className="border-b bg-gray-100">
            <th className="p-2 text-left">Date</th>
            <th className="p-2 text-left">Type</th>
            <th className="p-2 text-left">Amount</th>
            <th className="p-2 text-left">Status</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(tx => (
            <tr key={tx.id} className="border-b">
              <td className="p-2">{tx.timestamp}</td>
              <td className="p-2">{tx.type}</td>
              <td className="p-2">₦{tx.amount}</td>
              <td className="p-2">{tx.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Transactions;