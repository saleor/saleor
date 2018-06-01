import { products } from "../products/fixtures";

export const category = (placeholderImage: string) => ({
  description:
    "Across pressure PM food discover recognize. Send letter reach listen. Quickly work plan rule.\nTell lose part purpose do when. Whatever drug contain particularly defense.",
  id: "c1",
  name: "Apparel",
  products: products(placeholderImage)
});

export const errors = [
  {
    field: "name",
    message: "To pole jest wymagane."
  }
];
