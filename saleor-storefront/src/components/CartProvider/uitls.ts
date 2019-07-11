import { Checkout_lines } from "../../checkout/types/Checkout";
import { priceToString } from "../../core/utils";
import { VariantList } from "../../views/Product/types/VariantList";
import { LineI } from "../CartTable/ProductRow";
import { CartLineInterface } from "./context";

export const getTotal = (
  variantList: VariantList,
  lines: CartLineInterface[],
  locale?: string
): string => {
  const amount = lines.reduce((sum, { variantId, quantity }) => {
    const { node } = variantList.productVariants.edges.find(
      ({ node: { id } }) => id === variantId
    );
    return sum + node.price.amount * quantity;
  }, 0);
  const { currency } = variantList.productVariants.edges[0].node.price;

  return priceToString({ amount, currency }, locale);
};

export const extractCartLines = (
  data: VariantList,
  lines: CartLineInterface[],
  locale?: string
): LineI[] =>
  data.productVariants.edges
    .map(({ node }) => {
      const line = lines.find(({ variantId }) => variantId === node.id);
      if (!line) {
        return;
      }
      const quantity = line.quantity;
      return {
        ...node,
        quantity,
        totalPrice: priceToString(
          {
            amount: quantity * node.price.amount,
            currency: node.price.currency,
          },
          locale
        ),
      };
    })
    .filter(line => line)
    .sort((a, b) => b.id.toLowerCase().localeCompare(a.id.toLowerCase()));

export const extractCheckoutLines = (lines: Checkout_lines[]): LineI[] => {
  return lines
    .map(line => ({
      quantity: line.quantity,
      totalPrice: line.totalPrice.gross.localized,
      ...line.variant,
    }))
    .sort((a, b) => b.id.toLowerCase().localeCompare(a.id.toLowerCase()));
};
