import React from 'react';
import './BundleCard.css'; // Optional styling file if you create one

const BundleCard = ({ provider, description, price, onPurchase }) => {
  return (
    <div className="bundle-card">
      <img
        src={`/assets/providers/${provider}.png`}
        alt={`${provider} logo`}
        className="provider-logo"
      />
      <h3 className="bundle-title">{provider.toUpper()}</h3>
      <p className="bundle-description">{description}</p>
      <strong className="bundle-price">₦{price}</strong>
      <button className="purchase-button" onClick={onPurchase}>
        Buy
      </button>
    </div>
  );
};

export default BundleCard;