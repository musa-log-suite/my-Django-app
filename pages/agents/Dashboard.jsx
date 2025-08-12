import React, { useEffect, useState } from 'react';
import axiosInstance from '../../services/axiosInstance';

const Dashboard = () => {
  const [balance, setBalance] = useState(0);
  const [commissions, setCommissions] = useState(0);

  useEffect(() => {
    axiosInstance.get('/wallets/me/')
      .then(res => {
        setBalance(res.data.balance);
        setCommissions(res.data.commissions);
      });
  }, []);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold">Agent Dashboard</h2>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-white shadow p-4 rounded">
          <h3 className="text-lg font-medium">Wallet Balance</h3>
          <p className="text-xl font-bold text-green-600">₦{balance}</p>
        </div>
        <div className="bg-white shadow p-4 rounded">
          <h3 className="text-lg font-medium">Commissions</h3>
          <p className="text-xl font-bold text-blue-600">₦{commissions}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;