import { isEqual, pullAllBy } from "lodash";
import * as React from "react";

import { ApolloClient } from "apollo-client";
import { CheckoutContextInterface } from "../../checkout/context";
import { updateCheckoutLineQuery } from "../../checkout/queries";
import {
  updateCheckoutLine,
  updateCheckoutLineVariables
} from "../../checkout/types/updateCheckoutLine";
import { maybe } from "../../core/utils";
import {
  CartContext,
  CartInterface,
  CartLine,
  CartLineInterface
} from "./context";

enum LocalStorageKeys {
  Cart = "cart",
}

interface CartProviderProps {
  checkout: CheckoutContextInterface;
  apolloClient: ApolloClient<any>;
}

type CartProviderState = CartInterface;

export default class CartProvider extends React.Component<
  CartProviderProps,
  CartProviderState
> {
  constructor(props: CartProviderProps) {
    super(props);

    let lines;
    try {
      lines = JSON.parse(localStorage.getItem(LocalStorageKeys.Cart)) || [];
    } catch {
      lines = [];
    }
    this.state = {
      add: this.add,
      changeQuantity: this.changeQuantity,
      clear: this.clear,
      clearErrors: this.clearErrors,
      errors: null,
      getQuantity: this.getQuantity,
      lines,
      loading: false,
      remove: this.remove,
      subtract: this.subtract,
    };
  }

  componentDidUpdate() {
    const {
      checkout: { syncWithCart, update },
    } = this.props;

    if (syncWithCart) {
      this.syncCheckoutFromCart();
      update({ syncWithCart: false });
    }
  }

  syncCheckoutFromCart = async () => {
    const { checkout } = this.props.checkout;
    const { lines } = this.state;
    const checkoutLines = checkout.lines.map(
      ({ quantity, variant: { id } }) => ({ quantity, variantId: id })
    );

    if (lines.length) {
      if (!isEqual(lines, checkoutLines)) {
        const linestoRemove = pullAllBy(checkoutLines, lines, "variantId").map(
          ({ variantId }) => ({
            quantity: 0,
            variantId,
          })
        );
        this.changeQuantity([...linestoRemove, ...lines]);
      }
    } else if (checkoutLines.length) {
      this.changeQuantity(checkoutLines);
    }
  };

  getLine = (variantId: string): CartLineInterface =>
    this.state.lines.find(line => line.variantId === variantId);

  changeQuantity = async (lines: CartLine[]) => {
    this.setState({ loading: true });

    const { checkout } = this.props;
    const checkoutID = maybe(() => checkout.checkout.id);
    let apiError = false;

    if (checkoutID) {
      const { apolloClient } = this.props;
      const {
        data: {
          checkoutLinesUpdate: { errors, checkout: updatedCheckout },
        },
      } = await apolloClient.mutate<
        updateCheckoutLine,
        updateCheckoutLineVariables
      >({
        mutation: updateCheckoutLineQuery,
        variables: {
          checkoutId: checkoutID,
          lines,
        },
      });
      apiError = !!errors.length;
      if (apiError) {
        this.setState({
          errors: [...errors],
          loading: false,
        });
      } else {
        checkout.update({
          checkout: {
            ...checkout.checkout,
            lines: updatedCheckout.lines,
            subtotalPrice: updatedCheckout.subtotalPrice,
          },
        });
      }
    }

    if (!apiError) {
      this.setState(prevState => {
        const updatedLines = [
          ...pullAllBy(prevState.lines, lines, "variantId"),
          ...lines,
        ].filter(({ quantity }) => !!quantity);
        localStorage.setItem("cart", JSON.stringify(updatedLines));
        return { lines: updatedLines, loading: false };
      });
    }
  };

  add = (variantId, quantity = 1) => {
    const line = this.getLine(variantId);
    const newQuantity = line ? line.quantity + quantity : quantity;
    this.changeQuantity([{ variantId, quantity: newQuantity }]);
  };

  subtract = (variantId, quantity = 1) => {
    const line = this.getLine(variantId);
    const newQuantity = line ? line.quantity - quantity : quantity;
    this.changeQuantity([{ variantId, quantity: newQuantity }]);
  };

  clear = () => {
    this.setState({ lines: [], errors: [] });
    localStorage.removeItem(LocalStorageKeys.Cart);
  };

  clearErrors = () => this.setState({ errors: [] });

  getQuantity = () =>
    this.state.lines.reduce((sum, line) => sum + line.quantity, 0);

  remove = variantId => this.changeQuantity([{ variantId, quantity: 0 }]);

  render() {
    return (
      <CartContext.Provider value={this.state}>
        {this.props.children}
      </CartContext.Provider>
    );
  }
}
