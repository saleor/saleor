import { products } from "../products/fixtures";

export const categories = [
  {
    children: {
      totalCount: 2
    },
    id: "123123",
    name: "Lorem ipsum dolor",
    products: {
      totalCount: 4
    }
  },
  {
    children: {
      totalCount: 54
    },
    id: "876752",
    name: "Mauris vehicula tortor vulputate",
    products: {
      totalCount: 3
    }
  },
  {
    children: {
      totalCount: 2
    },
    id: "876542",
    name: "Excepteur sint occaecat cupidatat non proident",
    products: {
      totalCount: 6
    }
  },
  {
    children: {
      totalCount: 6
    },
    id: "875352",
    name: "Ut enim ad minim veniam",
    products: {
      totalCount: 12
    }
  },
  {
    children: {
      totalCount: 76
    },
    id: "865752",
    name: "Duis aute irure dolor in reprehenderit",
    products: {
      totalCount: 43
    }
  },
  {
    children: {
      totalCount: 11
    },
    id: "878752",
    name: "Neque porro quisquam est",
    products: {
      totalCount: 21
    }
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
  backgroundImage: {
    id: "UPJvZHVjfEs4YWdlOjV",
    url: placeholderImage
  },
  products: products(placeholderImage)
});
export const errors = [
  {
    field: "name",
    message: "To pole jest wymagane."
  }
];
