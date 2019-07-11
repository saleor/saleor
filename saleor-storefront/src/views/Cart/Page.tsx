import "./scss/index.scss";

import * as React from "react";
import { useAlert } from "react-alert";
import { Link } from "react-router-dom";

import { CheckoutContextInterface } from "../../checkout/context";
import { baseUrl as checkoutUrl } from "../../checkout/routes";
import { Button, CartTable, EmptyCart, Loader } from "../../components";
import { CartInterface } from "../../components/CartProvider/context";
import {
  extractCartLines,
  extractCheckoutLines,
  getTotal
} from "../../components/CartProvider/uitls";
import { OverlayContextInterface } from "../../components/Overlay/context";
import { getShop_shop } from "../../components/ShopProvider/types/getShop";
import { UserContext } from "../../components/User/context";
import { maybe } from "../../core/utils";
import { checkoutLoginUrl } from "../../routes";
import { TypedProductVariantsQuery } from "../Product/queries";

interface PageProps {
  checkout: CheckoutContextInterface;
  overlay: OverlayContextInterface;
  cart: CartInterface;
  shop: getShop_shop;
}

const Page: React.FC<PageProps> = ({
  shop: { geolocalization, defaultCountry },
  checkout: {
    checkout,
    loading: checkoutLoading,
    syncWithCart,
    syncUserCheckout,
  },
  cart: {
    lines,
    remove,
    add,
    errors,
    clearErrors,
    subtract,
    loading: cartLoading,
    changeQuantity,
  },
}) => {
  const alert = useAlert();
  const user = React.useContext(UserContext);
  const hasErrors: boolean | null = maybe(() => !!errors.length);
  const isLoading =
    (!checkout && checkoutLoading) || syncWithCart || syncUserCheckout;

  React.useEffect(() => {
    if (hasErrors) {
      alert.show(
        {
          content: errors.map(err => err.message).join(", "),
          title: "Error",
        },
        { type: "error" }
      );
      clearErrors();
    }
  }, [hasErrors]);

  if (isLoading) {
    return <Loader full />;
  }
  if (!lines.length) {
    return <EmptyCart />;
  }
  const productTableProps = {
    add,
    changeQuantity,
    invalid: maybe(() => !!errors.length, false),
    processing: cartLoading,
    remove,
    subtract,
  };
  const locale = maybe(() => geolocalization.country.code, defaultCountry.code);

  return (
    <>
      {checkout ? (
        <CartTable
          {...productTableProps}
          lines={extractCheckoutLines(checkout.lines)}
          subtotal={checkout.subtotalPrice.gross.localized}
        />
      ) : (
        <TypedProductVariantsQuery
          variables={{
            ids: lines.map(line => line.variantId),
          }}
        >
          {({ data }) => (
            <CartTable
              {...productTableProps}
              lines={extractCartLines(data, lines, locale)}
              subtotal={getTotal(data, lines, locale)}
            />
          )}
        </TypedProductVariantsQuery>
      )}
      <div className="cart-page__checkout-action">
        <Link to={user ? checkoutUrl : checkoutLoginUrl}>
          <Button disabled={cartLoading}>Proceed to Checkout</Button>
        </Link>
      </div>
    </>
  );
};

export default Page;
