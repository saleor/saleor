import "./scss/index.scss";

import * as React from "react";

import { CachedThumbnail } from "..";
import { BasicProductFields } from "../../views/Product/types/BasicProductFields";

import noPhotoImg from "../../images/no-photo.svg";

export interface Product extends BasicProductFields {
  category?: {
    id: string;
    name: string;
  };
  price: {
    localized: string;
  };
}

interface ProductListItemProps {
  product: Product;
}

const ProductListItem: React.FC<ProductListItemProps> = ({ product }) => {
  const { price, category } = product;
  return (
    <div className="product-list-item">
      <div className="product-list-item__image">
        <CachedThumbnail source={product}>
          <img src={noPhotoImg} alt={product.thumbnail.alt} />
        </CachedThumbnail>
      </div>
      <h4 className="product-list-item__title">{product.name}</h4>
      <p className="product-list-item__category">{category.name}</p>
      <p className="product-list-item__price">{price.localized}</p>
    </div>
  );
};

export default ProductListItem;
