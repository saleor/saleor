export const shop = (placeholderImage: string) => ({
  activities: [
    {
      action: "published",
      admin: false,
      date: "2018-09-10T13:22:24.376193+00:00",
      elementName: "Tępa Podkowa",
      id: "1",
      newElement: "collection",
      user: "Maćko z Bogdańca"
    },
    {
      action: "published",
      admin: false,
      date: "2018-10-18T13:22:24.376193+00:00",
      elementName: "Porwania",
      id: "2",
      newElement: "category",
      user: "Danusia Jurandówna"
    },
    {
      action: "created",
      admin: false,
      date: "2018-09-19T13:22:24.376193+00:00",
      elementName: "Legiony polskie",
      id: "3",
      newElement: "collection",
      user: "Ksiądz Robak"
    },
    {
      action: "added",
      admin: true,
      date: "2018-09-20T13:22:24.376193+00:00",
      id: "4",
      newElement: "user",
      user: "Tadeusz Soplica"
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
  userName: "Zbyszko z Bogdańca"
});
