// Marketplace.jsx

import React, { useState } from 'react';
import './BundleCard.css';

const providerList = ['All', 'MTN', 'GLO', 'AIRTEL', '9Mobile'];
const categoryList = ['All', 'Data', 'Airtime', 'SMS'];

const BundleCard = ({ provider, description, price, category, onPurchase }) => {
  const providerName = provider?.toUpperCase() || 'UNKNOWN';

  return (
    <div className="bundle-card">
      <img
        src={`/assets/providers/${provider}.png`}
        alt={`${providerName} logo`}
        className="provider-logo"
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = '/assets/providers/default.png';
        }}
      />
      <h3 className="bundle-title">{providerName}</h3>
      <p className="bundle-category">{category}</p>
      <p className="bundle-description">
        {description || 'No description available.'}
      </p>
      <strong className="bundle-price">₦{price}</strong>
      <button className="purchase-button" onClick={onPurchase}>
        Buy
      </button>
    </div>
  );
};

const Marketplace = ({ bundles }) => {
  const [wallet, setWallet] = useState(5000);
  const [providerFilter, setProviderFilter] = useState('All');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedBundle, setSelectedBundle] = useState(null);

  const filteredBundles = bundles.filter((bundle) => {
    const matchesProvider =
      providerFilter === 'All' ||
      bundle.provider.toUpperCase() === providerFilter;
    const matchesCategory =
      categoryFilter === 'All' ||
      bundle.category.toLowerCase() === categoryFilter.toLowerCase();
    const matchesSearch = bundle.description
      .toLowerCase()
      .includes(searchQuery.toLowerCase());

    return matchesProvider && matchesCategory && matchesSearch;
  });

  const openPurchaseModal = (bundle) => {
    setSelectedBundle(bundle);
    setShowModal(true);
  };

  const confirmPurchase = () => {
    if (selectedBundle.price > wallet) {
      alert('Insufficient wallet balance.');
    } else {
      setWallet((prev) => prev - selectedBundle.price);
      alert(`Purchased ${selectedBundle.provider} bundle successfully!`);
    }
    setShowModal(false);
    setSelectedBundle(null);
  };

  const cancelPurchase = () => {
    setShowModal(false);
    setSelectedBundle(null);
  };

  const handleTopUp = () => {
    setWallet((prev) => prev + 1000);
  };

  return (
    <div className="marketplace-container">
      <div className="controls">
        <select
          value={providerFilter}
          onChange={(e) => setProviderFilter(e.target.value)}
        >
          {providerList.map((prov) => (
            <option key={prov} value={prov}>
              {prov}
            </option>
          ))}
        </select>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          {categoryList.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search bundles..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        <div className="wallet-display">
          Wallet: ₦{wallet}{' '}
          <button className="topup-button" onClick={handleTopUp}>
            Top-Up ₦1000
          </button>
        </div>
      </div>

      <p className="bundle-count">
        Showing {filteredBundles.length} bundle
        {filteredBundles.length !== 1 && 's'}
      </p>

      <div className="marketplace-grid">
        {filteredBundles.length > 0 ? (
          filteredBundles.map((bundle) => (
            <BundleCard
              key={bundle.id}
              provider={bundle.provider}
              description={bundle.description}
              price={bundle.price}
              category={bundle.category}
              onPurchase={() => openPurchaseModal(bundle)}
            />
          ))
        ) : (
          <p className="no-bundles">No bundles available.</p>
        )}
      </div>

      {showModal && selectedBundle && (
        <div className="modal-overlay">
          <div className="modal">
            <h2>Confirm Purchase</h2>
            <p>
              Buy {selectedBundle.category} bundle from{' '}
              {selectedBundle.provider.toUpperCase()} for ₦
              {selectedBundle.price}?
            </p>
            <div className="modal-actions">
              <button onClick={confirmPurchase}>Confirm</button>
              <button onClick={cancelPurchase}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Marketplace;