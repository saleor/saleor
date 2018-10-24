import { HomePageProps } from "./components/HomePage";

export const shop: (placeholderImage: string) => HomePageProps = (
  placeholderImage: string
) => ({
  activities: [
    {
      action: "published",
      admin: false,
      date: "2018-09-10T13:22:24.376193+00:00",
      id: "1"
    },
    {
      action: "published",
      admin: false,
      date: "2018-10-18T13:22:24.376193+00:00",
      id: "2"
    },
    {
      action: "created",
      admin: false,
      date: "2018-09-19T13:22:24.376193+00:00",
      id: "3"
    },
    {
      action: "added",
      admin: true,
      date: "2018-09-20T13:22:24.376193+00:00",
      id: "4"
    }
  ],
  daily: {
    orders: {
      amount: 1223
    },
    sales: {
      amount: 12325,
      currency: "PLN"
    }
  },
  notifications: {
    orders: 12,
    payments: 10,
    problems: 69,
    productsOut: 2
  },
  onProductClick: () => undefined,
  topProducts: [
    {
      id: "1",
      name: "Lake Success",
      orders: 123,
      price: {
        amount: 54,
        currency: "PLN"
      },
      thumbnailUrl: placeholderImage,
      variant: "Hardcover"
    },
    {
      id: "2",
      name: "The Sadness of Beautiful Things",
      orders: 111,
      price: {
        amount: 23,
        currency: "PLN"
      },
      thumbnailUrl: placeholderImage,
      variant: "Softcover"
    },
    {
      id: "3",
      name: "The Messy Middle",
      orders: 93,
      price: {
        amount: 112,
        currency: "PLN"
      },
      thumbnailUrl: placeholderImage,
      variant: "Softcover"
    },
    {
      id: "4",
      name: "Everything's Trash",
      orders: 32,
      price: {
        amount: 15,
        currency: "PLN"
      },
      thumbnailUrl: placeholderImage,
      variant: "Hardcover"
    }
  ],
  userName: "John Smith"
});
