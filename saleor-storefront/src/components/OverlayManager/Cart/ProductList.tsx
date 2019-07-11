import * as React from "react";
import { Link } from "react-router-dom";
import ReactSVG from "react-svg";

import { CachedThumbnail } from "../..";
import { generateProductUrl } from "../../../core/utils";

import removeImg from "../../../images/garbage.svg";
import { LineI } from "../../CartTable/ProductRow";

const ProductList: React.SFC<{
  lines: LineI[];
  remove(variantId: string): void;
}> = ({ lines, remove }) => (
  <ul className="cart__list">
    {lines.map(line => {
      const productUrl = generateProductUrl(line.product.id, line.product.name);
      return (
        <li key={line.id} className="cart__list__item">
          <Link to={productUrl}>
            <CachedThumbnail source={line.product} />
          </Link>
          <div className="cart__list__item__details">
            <p>{line.price.localized}</p>
            <Link to={productUrl}>
              <p>{line.product.name}</p>
            </Link>
            <span className="cart__list__item__details__variant">
              <span>{line.name}</span>
              <span>{`Qty: ${line.quantity}`}</span>
            </span>
            <ReactSVG
              path={removeImg}
              className="cart__list__item__details__delete-icon"
              onClick={() => remove(line.id)}
            />
          </div>
        </li>
      );
    })}
  </ul>
);
export default ProductList;
