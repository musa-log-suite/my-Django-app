import React, { useState } from 'react';
import axiosInstance from '../../services/axiosInstance';

const SellBundle = () => {
  const [formData, setFormData] = useState({
    phone: '', network: '', amount: '', type: 'data'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axiosInstance.post('/marketplace/sell/', formData);
    alert('Bundle sold successfully!');
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold">Sell Airtime or Data</h2>
      <form onSubmit={handleSubmit} className="space-y-4 mt-4">
        <input name="phone" placeholder="Phone number" className="input" onChange={e => setFormData({...formData, phone: e.target.value})} />
        <select name="network" className="select" onChange={e => setFormData({...formData, network: e.target.value})}>
          <option value="">Select Network</option>
          <option value="MTN">MTN</option>
          <option value="Airtel">Airtel</option>
          <option value="Glo">Glo</option>
          <option value="9mobile">9mobile</option>
        </select>
        <input type="number" name="amount" placeholder="Amount" className="input" onChange={e => setFormData({...formData, amount: e.target.value})} />
        <select name="type" className="select" onChange={e => setFormData({...formData, type: e.target.value})}>
          <option value="data">Data</option>
          <option value="airtime">Airtime</option>
        </select>
        <button type="submit" className="btn">Sell</button>
      </form>
    </div>
  );
};

export default SellBundle;