/* tslint:disable */
//  This file was automatically generated and should not be edited.

export interface CategoryDeleteMutationVariables {
  id: string,
};

export interface CategoryDeleteMutation {
  categoryDelete:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
  } | null,
};

export interface CategoryCreateMutationVariables {
  name: string,
  description?: string | null,
  parentId?: string | null,
};

export interface CategoryCreateMutation {
  categoryCreate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    category:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      parent:  {
        // The ID of the object.
        id: string,
      } | null,
    } | null,
  } | null,
};

export interface CategoryUpdateMutationVariables {
  id: string,
  name: string,
  description: string,
};

export interface CategoryUpdateMutation {
  categoryUpdate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    category:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      parent:  {
        // The ID of the object.
        id: string,
      } | null,
    } | null,
  } | null,
};

export interface CategoryDetailsQueryVariables {
  id: string,
};

export interface CategoryDetailsQuery {
  // Lookup a category by ID.
  category:  {
    // The ID of the object.
    id: string,
    name: string,
    description: string,
    parent:  {
      // The ID of the object.
      id: string,
    } | null,
  } | null,
};

export interface RootCategoryChildrenQuery {
  // List of the shop's categories.
  categories:  {
    edges:  Array< {
      // A cursor for use in pagination
      cursor: string,
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      } | null,
    } | null >,
  } | null,
};

export interface CategoryPropertiesQueryVariables {
  id: string,
  first?: number | null,
  after?: string | null,
  last?: number | null,
  before?: string | null,
};

export interface CategoryPropertiesQuery {
  // Lookup a category by ID.
  category:  {
    // The ID of the object.
    id: string,
    name: string,
    description: string,
    parent:  {
      // The ID of the object.
      id: string,
    } | null,
    // List of children of the category.
    children:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
        } | null,
      } | null >,
    } | null,
    // List of products in the category.
    products:  {
      // A total count of items in the collection
      totalCount: number | null,
      pageInfo:  {
        // When paginating forwards, the cursor to continue.
        endCursor: string | null,
        // When paginating forwards, are there more items?
        hasNextPage: boolean,
        // When paginating backwards, are there more items?
        hasPreviousPage: boolean,
        // When paginating backwards, the cursor to continue.
        startCursor: string | null,
      },
      edges:  Array< {
        // A cursor for use in pagination
        cursor: string,
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
          // The URL of a main thumbnail for a product.
          thumbnailUrl: string | null,
          productType:  {
            // The ID of the object.
            id: string,
            name: string,
          },
        } | null,
      } | null >,
    } | null,
  } | null,
};

export interface PageDeleteMutationVariables {
  id: string,
};

export interface PageDeleteMutation {
  pageDelete:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
  } | null,
};

export interface PageUpdateMutationVariables {
  id: string,
  title: string,
  content: string,
  slug: string,
  isVisible: boolean,
  availableOn?: string | null,
};

export interface PageUpdateMutation {
  pageUpdate:  {
    page:  {
      // The ID of the object.
      id: string,
      slug: string,
      title: string,
      content: string,
      isVisible: boolean,
      availableOn: string | null,
    } | null,
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
  } | null,
};

export interface PageCreateMutationVariables {
  title: string,
  content: string,
  slug: string,
  isVisible: boolean,
  availableOn?: string | null,
};

export interface PageCreateMutation {
  pageCreate:  {
    page:  {
      // The ID of the object.
      id: string,
      slug: string,
      title: string,
      content: string,
      isVisible: boolean,
      availableOn: string | null,
      created: string,
    } | null,
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
  } | null,
};

export interface PageListQueryVariables {
  first?: number | null,
  after?: string | null,
  last?: number | null,
  before?: string | null,
};

export interface PageListQuery {
  // List of the shop's pages.
  pages:  {
    edges:  Array< {
      // A cursor for use in pagination
      cursor: string,
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        slug: string,
        title: string,
        isVisible: boolean,
      } | null,
    } | null >,
    pageInfo:  {
      // When paginating backwards, are there more items?
      hasPreviousPage: boolean,
      // When paginating forwards, are there more items?
      hasNextPage: boolean,
      // When paginating backwards, the cursor to continue.
      startCursor: string | null,
      // When paginating forwards, the cursor to continue.
      endCursor: string | null,
    },
  } | null,
};

export interface PageDetailsQueryVariables {
  id: string,
};

export interface PageDetailsQuery {
  // Lookup a page by ID or by slug.
  page:  {
    // The ID of the object.
    id: string,
    slug: string,
    title: string,
    content: string,
    created: string,
    isVisible: boolean,
    availableOn: string | null,
  } | null,
};

export interface ProductImageCreateMutationVariables {
  id: string,
  file: string,
};

export interface ProductImageCreateMutation {
  productImageCreate:  {
    // A newly created product image.
    productImage:  {
      // The ID of the object.
      id: string,
      image: string,
      url: string,
      order: number,
    } | null,
  } | null,
};

export interface ProductListQueryVariables {
  first?: number | null,
  after?: string | null,
  last?: number | null,
  before?: string | null,
};

export interface ProductListQuery {
  // List of the shop's products.
  products:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
        // The URL of a main thumbnail for a product.
        thumbnailUrl: string | null,
        productType:  {
          // The ID of the object.
          id: string,
          name: string,
        },
      } | null,
    } | null >,
    pageInfo:  {
      // When paginating backwards, are there more items?
      hasPreviousPage: boolean,
      // When paginating forwards, are there more items?
      hasNextPage: boolean,
      // When paginating backwards, the cursor to continue.
      startCursor: string | null,
      // When paginating forwards, the cursor to continue.
      endCursor: string | null,
    },
  } | null,
};

export interface ProductDetailsQueryVariables {
  id: string,
};

export interface ProductDetailsQuery {
  // Lookup a product by ID.
  product:  {
    // The ID of the object.
    id: string,
    name: string,
    description: string,
    collections:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
        } | null,
      } | null >,
    } | null,
    // The product's base price (without any discounts
    // applied).
    price:  {
      // Money formatted according to the current locale.
      localized: string | null,
    } | null,
    grossMargin:  Array< {
      start: number | null,
      stop: number | null,
    } | null > | null,
    purchaseCost:  {
      // Lower bound of a price range.
      start:  {
        // Amount of money including taxes.
        gross:  {
          // Money formatted according to the current locale.
          localized: string | null,
        } | null,
      } | null,
      // Upper bound of a price range.
      stop:  {
        // Amount of money including taxes.
        gross:  {
          // Money formatted according to the current locale.
          localized: string | null,
        } | null,
      } | null,
    } | null,
    isPublished: boolean,
    // Informs about product's availability in the storefront,
    // current price and discounts.
    availability:  {
      available: boolean | null,
      priceRange:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money without taxes.
          net:  {
            // Money formatted according to the current locale.
            localized: string | null,
          } | null,
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money without taxes.
          net:  {
            // Money formatted according to the current locale.
            localized: string | null,
          } | null,
        } | null,
      } | null,
    } | null,
    images:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          alt: string,
          order: number,
          url: string,
        } | null,
      } | null >,
    } | null,
    variants:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          sku: string,
          name: string,
          // Override the base price of a product if necessary.
          // A value of `null` indicates that the default product price is used.
          priceOverride:  {
            // Money formatted according to the current locale.
            localized: string | null,
          } | null,
          // Quantity of a product available for sale.
          stockQuantity: number,
          // Gross margin percentage value.
          margin: number | null,
        } | null,
      } | null >,
    } | null,
    productType:  {
      // The ID of the object.
      id: string,
      name: string,
    },
    // The storefront URL for the product.
    url: string,
  } | null,
};
