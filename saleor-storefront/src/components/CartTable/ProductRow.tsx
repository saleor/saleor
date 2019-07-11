import classNames from "classnames";
import * as React from "react";
import { Link } from "react-router-dom";
import ReactSVG from "react-svg";

import { CachedThumbnail, DebouncedTextField } from "..";
import { generateProductUrl } from "../../core/utils";
import { CartLine } from "../CartProvider/context";

import { ProductVariant } from "../../checkout/types/ProductVariant";
import cartAddDisabledImg from "../../images/cart-add-disabled.svg";
import cartAddImg from "../../images/cart-add.svg";
import cartRemoveImg from "../../images/cart-remove.svg";
import cartSubtractImg from "../../images/cart-subtract.svg";

export type LineI = ProductVariant & {
  quantity: number;
  totalPrice: string;
  stockQuantity?: number;
};

interface ReadProductRowProps {
  mediumScreen: boolean;
  line: LineI;
}

export interface EditableProductRowProps {
  processing?: boolean;
  invalid?: boolean;
  add?(variantId: string): void;
  changeQuantity?(lines: CartLine[]): void;
  remove?(variantId: string): void;
  subtract?(variantId: string): void;
}

const ProductRow: React.FC<ReadProductRowProps & EditableProductRowProps> = ({
  invalid,
  add,
  changeQuantity,
  mediumScreen,
  processing,
  remove,
  subtract,
  line,
}) => {
  const productUrl = generateProductUrl(line.product.id, line.product.name);
  const editable = !!(add && subtract && remove && changeQuantity);
  const inStock =
    line.stockQuantity === undefined
      ? false
      : line.quantity < line.stockQuantity;
  const quantityChangeControls = mediumScreen ? (
    <div>
      <ReactSVG path={cartSubtractImg} onClick={() => subtract(line.id)} />
      <p>{line.quantity}</p>
      <ReactSVG
        className={classNames({ disabled: !inStock })}
        path={inStock ? cartAddImg : cartAddDisabledImg}
        onClick={inStock ? () => add(line.id) : undefined}
      />
    </div>
  ) : (
    <DebouncedTextField
      value={line.quantity}
      onChange={evt =>
        changeQuantity([
          { variantId: line.id, quantity: parseInt(evt.target.value, 10) },
        ])
      }
      resetValue={invalid}
      disabled={processing}
    />
  );

  return (
    <tr
      className={classNames({
        "cart-table-row--processing": processing,
      })}
    >
      <td className="cart-table__thumbnail">
        <div>
          {mediumScreen && (
            <Link to={productUrl}>
              <CachedThumbnail source={line.product} />
            </Link>
          )}
          <Link to={productUrl}>{line.product.name}</Link>
        </div>
      </td>

      {mediumScreen && <td>{line.price.localized}</td>}

      <td>{line.name}</td>

      <td className="cart-table__quantity-cell">
        {editable ? quantityChangeControls : <p>{line.quantity}</p>}
      </td>

      <td colSpan={editable ? 1 : 2}>{line.totalPrice}</td>

      {editable && (
        <td>
          <ReactSVG path={cartRemoveImg} onClick={() => remove(line.id)} />
        </td>
      )}
    </tr>
  );
};

export default ProductRow;
