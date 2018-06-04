import { products } from "../products/fixtures";

export const categories = [
  {
    id: "123123",
    name: "Lorem ipsum dolor"
  },
  {
    id: "876752",
    name: "Mauris vehicula tortor vulputate"
  }
];
export const category = (placeholderImage: string) => ({
  SeoDescription:
    "Across pressure PM food discover recognize. Send letter reach listen. Quickly work plan rule.\nTell lose part purpose do when. Whatever drug contain particularly defense.",
  SeoTitle: "Apparel",
  children: categories,
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
