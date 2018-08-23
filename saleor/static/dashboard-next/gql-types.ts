/* tslint:disable */
//  This file was automatically generated and should not be edited.

export interface ProductTypeInput {
  // Name of the product type.
  name?: string | null,
  // Determines if product of this type has multiple
  // variants. This option mainly simplifies product management
  // in the dashboard. There is always at least one variant created under
  // the hood.
  hasVariants?: boolean | null,
  // List of attributes shared among all product variants.
  productAttributes?: Array< string | null > | null,
  // List of attributes used to distinguish between
  // different variants of a product.
  variantAttributes?: Array< string | null > | null,
  // Determines if shipping is required for products
  // of this variant.
  isShippingRequired?: boolean | null,
};

export interface AttributeValueInput {
  // Slug of an attribute.
  slug: string,
  // Value of an attribute.
  value: string,
};

export interface TokenAuthMutationVariables {
  email: string,
  password: string,
};

export interface TokenAuthMutation {
  tokenCreate:  {
    token: string | null,
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    user:  {
      // The ID of the object.
      id: string,
      email: string,
      isStaff: boolean,
      note: string | null,
      permissions:  Array< {
        // Internal code for permission.
        code: string,
        // Describe action(s) allowed to do by permission.
        name: string,
      } | null > | null,
    } | null,
  } | null,
};

export interface VerifyTokenMutationVariables {
  token: string,
};

export interface VerifyTokenMutation {
  tokenVerify:  {
    payload: string | null,
    user:  {
      // The ID of the object.
      id: string,
      email: string,
      isStaff: boolean,
      note: string | null,
      permissions:  Array< {
        // Internal code for permission.
        code: string,
        // Describe action(s) allowed to do by permission.
        name: string,
      } | null > | null,
    } | null,
  } | null,
};

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
  name?: string | null,
  description?: string | null,
  parent?: string | null,
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
  name?: string | null,
  description?: string | null,
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
        // List of children of the category.
        children:  {
          // A total count of items in the collection
          totalCount: number | null,
        } | null,
        // List of products in the category.
        products:  {
          // A total count of items in the collection
          totalCount: number | null,
        } | null,
      },
    } >,
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
          // List of children of the category.
          children:  {
            // A total count of items in the collection
            totalCount: number | null,
          } | null,
          // List of products in the category.
          products:  {
            // A total count of items in the collection
            totalCount: number | null,
          } | null,
        },
      } >,
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
        },
      } >,
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
      },
    } >,
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

export interface ProductTypeDeleteMutationVariables {
  id: string,
};

export interface ProductTypeDeleteMutation {
  productTypeDelete:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productType:  {
      // The ID of the object.
      id: string,
    } | null,
  } | null,
};

export interface ProductTypeUpdateMutationVariables {
  id: string,
  input: ProductTypeInput,
};

export interface ProductTypeUpdateMutation {
  productTypeUpdate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productType:  {
      // The ID of the object.
      id: string,
      name: string,
      hasVariants: boolean,
      productAttributes:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            // Internal representation of an attribute name.
            slug: string | null,
            // Visible name for display purposes.
            name: string | null,
          },
        } >,
      } | null,
      variantAttributes:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            // Internal representation of an attribute name.
            slug: string | null,
            // Visible name for display purposes.
            name: string | null,
          },
        } >,
      } | null,
      isShippingRequired: boolean,
    } | null,
  } | null,
};

export interface ProductTypeListQueryVariables {
  after?: string | null,
  before?: string | null,
  first?: number | null,
  last?: number | null,
};

export interface ProductTypeListQuery {
  // List of the shop's product types.
  productTypes:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
        productAttributes:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              // Visible name for display purposes.
              name: string | null,
            },
          } >,
        } | null,
        variantAttributes:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              // Visible name for display purposes.
              name: string | null,
            },
          } >,
        } | null,
      },
    } >,
    pageInfo:  {
      // When paginating forwards, are there more items?
      hasNextPage: boolean,
      // When paginating backwards, are there more items?
      hasPreviousPage: boolean,
      // When paginating backwards, the cursor to continue.
      startCursor: string | null,
      // When paginating forwards, the cursor to continue.
      endCursor: string | null,
    },
  } | null,
};

export interface ProductTypeDetailsQueryVariables {
  id: string,
};

export interface ProductTypeDetailsQuery {
  // Lookup a product type by ID.
  productType:  {
    // The ID of the object.
    id: string,
    name: string,
    hasVariants: boolean,
    productAttributes:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
        },
      } >,
    } | null,
    variantAttributes:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
        },
      } >,
    } | null,
    isShippingRequired: boolean,
    taxRate: string,
  } | null,
};

export interface SearchAttributeQueryVariables {
  search: string,
};

export interface SearchAttributeQuery {
  // List of the shop's product attributes.
  attributes:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        // Internal representation of an attribute name.
        slug: string | null,
        // Visible name for display purposes.
        name: string | null,
      },
    } >,
  } | null,
};

export interface ProductImageCreateMutationVariables {
  product: string,
  image: string,
  alt?: string | null,
};

export interface ProductImageCreateMutation {
  productImageCreate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      seoTitle: string | null,
      seoDescription: string | null,
      category:  {
        // The ID of the object.
        id: string,
        name: string,
      },
      collections:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            name: string,
          },
        } >,
      } | null,
      // The product's base price (without any discounts
      // applied).
      price:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      margin:  {
        start: number | null,
        stop: number | null,
      } | null,
      purchaseCost:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
      } | null,
      isPublished: boolean,
      chargeTaxes: boolean,
      availableOn: string | null,
      // List of product attributes assigned to this product.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
          // List of attribute's values.
          values:  Array< {
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Informs about product's availability in the storefront,
      // current price and discounts.
      availability:  {
        available: boolean | null,
        priceRange:  {
          // Lower bound of a price range.
          start:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
          } | null,
          // Upper bound of a price range.
          stop:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
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
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
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
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            } | null,
            // Quantity of a product available for sale.
            stockQuantity: number,
            // Gross margin percentage value.
            margin: number | null,
          },
        } >,
      } | null,
      productType:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
      },
      // The storefront URL for the product.
      url: string,
    } | null,
  } | null,
};

export interface ProductDeleteMutationVariables {
  id: string,
};

export interface ProductDeleteMutation {
  productDelete:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
    } | null,
  } | null,
};

export interface ProductImageReorderMutationVariables {
  productId: string,
  imagesIds: Array< string | null >,
};

export interface ProductImageReorderMutation {
  productImageReorder:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            alt: string,
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
      } | null,
    } | null,
  } | null,
};

export interface ProductUpdateMutationVariables {
  id: string,
  attributes?: Array< AttributeValueInput | null > | null,
  availableOn?: string | null,
  category?: string | null,
  chargeTaxes: boolean,
  collections?: Array< string | null > | null,
  description?: string | null,
  isPublished: boolean,
  name?: string | null,
  price?: string | null,
};

export interface ProductUpdateMutation {
  productUpdate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      seoTitle: string | null,
      seoDescription: string | null,
      category:  {
        // The ID of the object.
        id: string,
        name: string,
      },
      collections:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            name: string,
          },
        } >,
      } | null,
      // The product's base price (without any discounts
      // applied).
      price:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      margin:  {
        start: number | null,
        stop: number | null,
      } | null,
      purchaseCost:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
      } | null,
      isPublished: boolean,
      chargeTaxes: boolean,
      availableOn: string | null,
      // List of product attributes assigned to this product.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
          // List of attribute's values.
          values:  Array< {
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Informs about product's availability in the storefront,
      // current price and discounts.
      availability:  {
        available: boolean | null,
        priceRange:  {
          // Lower bound of a price range.
          start:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
          } | null,
          // Upper bound of a price range.
          stop:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
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
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
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
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            } | null,
            // Quantity of a product available for sale.
            stockQuantity: number,
            // Gross margin percentage value.
            margin: number | null,
          },
        } >,
      } | null,
      productType:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
      },
      // The storefront URL for the product.
      url: string,
    } | null,
  } | null,
};

export interface ProductCreateMutationVariables {
  attributes?: Array< AttributeValueInput | null > | null,
  availableOn?: string | null,
  category: string,
  chargeTaxes: boolean,
  collections?: Array< string | null > | null,
  description?: string | null,
  isPublished: boolean,
  name: string,
  price?: string | null,
  productType: string,
};

export interface ProductCreateMutation {
  productCreate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      seoTitle: string | null,
      seoDescription: string | null,
      category:  {
        // The ID of the object.
        id: string,
        name: string,
      },
      collections:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            name: string,
          },
        } >,
      } | null,
      // The product's base price (without any discounts
      // applied).
      price:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      margin:  {
        start: number | null,
        stop: number | null,
      } | null,
      purchaseCost:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
      } | null,
      isPublished: boolean,
      chargeTaxes: boolean,
      availableOn: string | null,
      // List of product attributes assigned to this product.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
          // List of attribute's values.
          values:  Array< {
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Informs about product's availability in the storefront,
      // current price and discounts.
      availability:  {
        available: boolean | null,
        priceRange:  {
          // Lower bound of a price range.
          start:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
          } | null,
          // Upper bound of a price range.
          stop:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
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
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
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
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            } | null,
            // Quantity of a product available for sale.
            stockQuantity: number,
            // Gross margin percentage value.
            margin: number | null,
          },
        } >,
      } | null,
      productType:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
      },
      // The storefront URL for the product.
      url: string,
    } | null,
  } | null,
};

export interface VariantDeleteMutationVariables {
  id: string,
};

export interface VariantDeleteMutation {
  productVariantDelete:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productVariant:  {
      // The ID of the object.
      id: string,
    } | null,
  } | null,
};

export interface VariantUpdateMutationVariables {
  id: string,
  attributes?: Array< AttributeValueInput | null > | null,
  costPrice?: string | null,
  priceOverride?: string | null,
  product?: string | null,
  sku?: string | null,
  quantity?: number | null,
  trackInventory: boolean,
};

export interface VariantUpdateMutation {
  productVariantUpdate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productVariant:  {
      // The ID of the object.
      id: string,
      // List of attributes assigned to this variant.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
          // List of attribute's values.
          values:  Array< {
            // The ID of the object.
            id: string,
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Cost price of the variant.
      costPrice:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
          },
        } >,
      } | null,
      name: string,
      // Override the base price of a product if necessary.
      // A value of `null` indicates that the default product price is used.
      priceOverride:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      product:  {
        // The ID of the object.
        id: string,
        images:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              alt: string,
              sortOrder: number,
              // The URL of the image.
              url: string,
            },
          } >,
        } | null,
        name: string,
        // The URL of a main thumbnail for a product.
        thumbnailUrl: string | null,
        variants:  {
          // A total count of items in the collection
          totalCount: number | null,
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              name: string,
              sku: string,
              image:  {
                edges:  Array< {
                  // The item at the end of the edge
                  node:  {
                    // The ID of the object.
                    id: string,
                    // The URL of the image.
                    url: string,
                  },
                } >,
              } | null,
            },
          } >,
        } | null,
      },
      sku: string,
      quantity: number,
      quantityAllocated: number,
    } | null,
  } | null,
};

export interface VariantCreateMutationVariables {
  attributes?: Array< AttributeValueInput | null > | null,
  costPrice?: string | null,
  priceOverride?: string | null,
  product?: string | null,
  sku?: string | null,
  quantity?: number | null,
  trackInventory: boolean,
};

export interface VariantCreateMutation {
  productVariantCreate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productVariant:  {
      // The ID of the object.
      id: string,
      // List of attributes assigned to this variant.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
          // List of attribute's values.
          values:  Array< {
            // The ID of the object.
            id: string,
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Cost price of the variant.
      costPrice:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
          },
        } >,
      } | null,
      name: string,
      // Override the base price of a product if necessary.
      // A value of `null` indicates that the default product price is used.
      priceOverride:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      product:  {
        // The ID of the object.
        id: string,
        images:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              alt: string,
              sortOrder: number,
              // The URL of the image.
              url: string,
            },
          } >,
        } | null,
        name: string,
        // The URL of a main thumbnail for a product.
        thumbnailUrl: string | null,
        variants:  {
          // A total count of items in the collection
          totalCount: number | null,
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              name: string,
              sku: string,
              image:  {
                edges:  Array< {
                  // The item at the end of the edge
                  node:  {
                    // The ID of the object.
                    id: string,
                    // The URL of the image.
                    url: string,
                  },
                } >,
              } | null,
            },
          } >,
        } | null,
      },
      sku: string,
      quantity: number,
      quantityAllocated: number,
    } | null,
  } | null,
};

export interface ProductImageDeleteMutationVariables {
  id: string,
};

export interface ProductImageDeleteMutation {
  productImageDelete:  {
    product:  {
      // The ID of the object.
      id: string,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
          },
        } >,
      } | null,
    } | null,
  } | null,
};

export interface ProductImageUpdateMutationVariables {
  id: string,
  alt: string,
};

export interface ProductImageUpdateMutation {
  productImageUpdate:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    product:  {
      // The ID of the object.
      id: string,
      name: string,
      description: string,
      seoTitle: string | null,
      seoDescription: string | null,
      category:  {
        // The ID of the object.
        id: string,
        name: string,
      },
      collections:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            name: string,
          },
        } >,
      } | null,
      // The product's base price (without any discounts
      // applied).
      price:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      margin:  {
        start: number | null,
        stop: number | null,
      } | null,
      purchaseCost:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
      } | null,
      isPublished: boolean,
      chargeTaxes: boolean,
      availableOn: string | null,
      // List of product attributes assigned to this product.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Internal representation of an attribute name.
          slug: string | null,
          // Visible name for display purposes.
          name: string | null,
          // List of attribute's values.
          values:  Array< {
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Informs about product's availability in the storefront,
      // current price and discounts.
      availability:  {
        available: boolean | null,
        priceRange:  {
          // Lower bound of a price range.
          start:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
          } | null,
          // Upper bound of a price range.
          stop:  {
            // Amount of money without taxes.
            net:  {
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            },
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
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
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
              // Amount of money.
              amount: number,
              // Currency code.
              currency: string,
            } | null,
            // Quantity of a product available for sale.
            stockQuantity: number,
            // Gross margin percentage value.
            margin: number | null,
          },
        } >,
      } | null,
      productType:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
      },
      // The storefront URL for the product.
      url: string,
    } | null,
  } | null,
};

export interface VariantImageAssignMutationVariables {
  variantId: string,
  imageId: string,
};

export interface VariantImageAssignMutation {
  variantImageAssign:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productVariant:  {
      // The ID of the object.
      id: string,
      // List of attributes assigned to this variant.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
          // List of attribute's values.
          values:  Array< {
            // The ID of the object.
            id: string,
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Cost price of the variant.
      costPrice:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
          },
        } >,
      } | null,
      name: string,
      // Override the base price of a product if necessary.
      // A value of `null` indicates that the default product price is used.
      priceOverride:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      product:  {
        // The ID of the object.
        id: string,
        images:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              alt: string,
              sortOrder: number,
              // The URL of the image.
              url: string,
            },
          } >,
        } | null,
        name: string,
        // The URL of a main thumbnail for a product.
        thumbnailUrl: string | null,
        variants:  {
          // A total count of items in the collection
          totalCount: number | null,
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              name: string,
              sku: string,
              image:  {
                edges:  Array< {
                  // The item at the end of the edge
                  node:  {
                    // The ID of the object.
                    id: string,
                    // The URL of the image.
                    url: string,
                  },
                } >,
              } | null,
            },
          } >,
        } | null,
      },
      sku: string,
      quantity: number,
      quantityAllocated: number,
    } | null,
  } | null,
};

export interface VariantImageUnassignMutationVariables {
  variantId: string,
  imageId: string,
};

export interface VariantImageUnassignMutation {
  variantImageUnassign:  {
    // List of errors that occurred executing the mutation.
    errors:  Array< {
      // Name of a field that caused the error. A value of
      // `null` indicates that the error isn't associated with a particular
      // field.
      field: string | null,
      // The error message.
      message: string | null,
    } | null > | null,
    productVariant:  {
      // The ID of the object.
      id: string,
      // List of attributes assigned to this variant.
      attributes:  Array< {
        // Name of an attribute
        attribute:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
          // List of attribute's values.
          values:  Array< {
            // The ID of the object.
            id: string,
            // Visible name for display purposes.
            name: string | null,
            // Internal representation of an attribute name.
            slug: string | null,
          } | null > | null,
        } | null,
        // Value of an attribute.
        value:  {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null,
      } | null > | null,
      // Cost price of the variant.
      costPrice:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
          },
        } >,
      } | null,
      name: string,
      // Override the base price of a product if necessary.
      // A value of `null` indicates that the default product price is used.
      priceOverride:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      product:  {
        // The ID of the object.
        id: string,
        images:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              alt: string,
              sortOrder: number,
              // The URL of the image.
              url: string,
            },
          } >,
        } | null,
        name: string,
        // The URL of a main thumbnail for a product.
        thumbnailUrl: string | null,
        variants:  {
          // A total count of items in the collection
          totalCount: number | null,
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              name: string,
              sku: string,
              image:  {
                edges:  Array< {
                  // The item at the end of the edge
                  node:  {
                    // The ID of the object.
                    id: string,
                    // The URL of the image.
                    url: string,
                  },
                } >,
              } | null,
            },
          } >,
        } | null,
      },
      sku: string,
      quantity: number,
      quantityAllocated: number,
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
        // Informs about product's availability in the storefront,
        // current price and discounts.
        availability:  {
          available: boolean | null,
        } | null,
        // The product's base price (without any discounts
        // applied).
        price:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        productType:  {
          // The ID of the object.
          id: string,
          name: string,
        },
      },
    } >,
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
    seoTitle: string | null,
    seoDescription: string | null,
    category:  {
      // The ID of the object.
      id: string,
      name: string,
    },
    collections:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
        },
      } >,
    } | null,
    // The product's base price (without any discounts
    // applied).
    price:  {
      // Amount of money.
      amount: number,
      // Currency code.
      currency: string,
    } | null,
    margin:  {
      start: number | null,
      stop: number | null,
    } | null,
    purchaseCost:  {
      // Lower bound of a price range.
      start:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
      // Upper bound of a price range.
      stop:  {
        // Amount of money.
        amount: number,
        // Currency code.
        currency: string,
      } | null,
    } | null,
    isPublished: boolean,
    chargeTaxes: boolean,
    availableOn: string | null,
    // List of product attributes assigned to this product.
    attributes:  Array< {
      // Name of an attribute
      attribute:  {
        // The ID of the object.
        id: string,
        // Internal representation of an attribute name.
        slug: string | null,
        // Visible name for display purposes.
        name: string | null,
        // List of attribute's values.
        values:  Array< {
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null > | null,
      } | null,
      // Value of an attribute.
      value:  {
        // The ID of the object.
        id: string,
        // Visible name for display purposes.
        name: string | null,
        // Internal representation of an attribute name.
        slug: string | null,
      } | null,
    } | null > | null,
    // Informs about product's availability in the storefront,
    // current price and discounts.
    availability:  {
      available: boolean | null,
      priceRange:  {
        // Lower bound of a price range.
        start:  {
          // Amount of money without taxes.
          net:  {
            // Amount of money.
            amount: number,
            // Currency code.
            currency: string,
          },
        } | null,
        // Upper bound of a price range.
        stop:  {
          // Amount of money without taxes.
          net:  {
            // Amount of money.
            amount: number,
            // Currency code.
            currency: string,
          },
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
          sortOrder: number,
          // The URL of the image.
          url: string,
        },
      } >,
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
            // Amount of money.
            amount: number,
            // Currency code.
            currency: string,
          } | null,
          // Quantity of a product available for sale.
          stockQuantity: number,
          // Gross margin percentage value.
          margin: number | null,
        },
      } >,
    } | null,
    productType:  {
      // The ID of the object.
      id: string,
      name: string,
      hasVariants: boolean,
    },
    // The storefront URL for the product.
    url: string,
  } | null,
  // List of the shop's collections.
  collections:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      },
    } >,
  } | null,
  // List of the shop's categories.
  categories:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      },
    } >,
  } | null,
};

export interface ProductVariantDetailsQueryVariables {
  id: string,
};

export interface ProductVariantDetailsQuery {
  // Lookup a variant by ID.
  productVariant:  {
    // The ID of the object.
    id: string,
    // List of attributes assigned to this variant.
    attributes:  Array< {
      // Name of an attribute
      attribute:  {
        // The ID of the object.
        id: string,
        // Visible name for display purposes.
        name: string | null,
        // Internal representation of an attribute name.
        slug: string | null,
        // List of attribute's values.
        values:  Array< {
          // The ID of the object.
          id: string,
          // Visible name for display purposes.
          name: string | null,
          // Internal representation of an attribute name.
          slug: string | null,
        } | null > | null,
      } | null,
      // Value of an attribute.
      value:  {
        // The ID of the object.
        id: string,
        // Visible name for display purposes.
        name: string | null,
        // Internal representation of an attribute name.
        slug: string | null,
      } | null,
    } | null > | null,
    // Cost price of the variant.
    costPrice:  {
      // Amount of money.
      amount: number,
      // Currency code.
      currency: string,
    } | null,
    images:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
        },
      } >,
    } | null,
    name: string,
    // Override the base price of a product if necessary.
    // A value of `null` indicates that the default product price is used.
    priceOverride:  {
      // Amount of money.
      amount: number,
      // Currency code.
      currency: string,
    } | null,
    product:  {
      // The ID of the object.
      id: string,
      images:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            alt: string,
            sortOrder: number,
            // The URL of the image.
            url: string,
          },
        } >,
      } | null,
      name: string,
      // The URL of a main thumbnail for a product.
      thumbnailUrl: string | null,
      variants:  {
        // A total count of items in the collection
        totalCount: number | null,
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            name: string,
            sku: string,
            image:  {
              edges:  Array< {
                // The item at the end of the edge
                node:  {
                  // The ID of the object.
                  id: string,
                  // The URL of the image.
                  url: string,
                },
              } >,
            } | null,
          },
        } >,
      } | null,
    },
    sku: string,
    quantity: number,
    quantityAllocated: number,
  } | null,
};

export interface ProductCreateDataQuery {
  // List of the shop's product types.
  productTypes:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
        hasVariants: boolean,
        productAttributes:  {
          edges:  Array< {
            // The item at the end of the edge
            node:  {
              // The ID of the object.
              id: string,
              // Internal representation of an attribute name.
              slug: string | null,
              // Visible name for display purposes.
              name: string | null,
              // List of attribute's values.
              values:  Array< {
                // The ID of the object.
                id: string,
                sortOrder: number,
                // Visible name for display purposes.
                name: string | null,
                // Internal representation of an attribute name.
                slug: string | null,
              } | null > | null,
            },
          } >,
        } | null,
      },
    } >,
  } | null,
  // List of the shop's collections.
  collections:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      },
    } >,
  } | null,
  // List of the shop's categories.
  categories:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      },
    } >,
  } | null,
};

export interface ProductVariantCreateDataQueryVariables {
  id: string,
};

export interface ProductVariantCreateDataQuery {
  // Lookup a product by ID.
  product:  {
    // The ID of the object.
    id: string,
    images:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          sortOrder: number,
          // The URL of the image.
          url: string,
        },
      } >,
    } | null,
    productType:  {
      // The ID of the object.
      id: string,
      variantAttributes:  {
        edges:  Array< {
          // The item at the end of the edge
          node:  {
            // The ID of the object.
            id: string,
            // Internal representation of an attribute name.
            slug: string | null,
            // Visible name for display purposes.
            name: string | null,
            // List of attribute's values.
            values:  Array< {
              // The ID of the object.
              id: string,
              sortOrder: number,
              // Visible name for display purposes.
              name: string | null,
              // Internal representation of an attribute name.
              slug: string | null,
            } | null > | null,
          },
        } >,
      } | null,
    },
    variants:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
          sku: string,
          image:  {
            edges:  Array< {
              // The item at the end of the edge
              node:  {
                // The ID of the object.
                id: string,
                // The URL of the image.
                url: string,
              },
            } >,
          } | null,
        },
      } >,
    } | null,
  } | null,
};

export interface ProductImageQueryVariables {
  productId: string,
  imageId: string,
};

export interface ProductImageQuery {
  // Lookup a product by ID.
  product:  {
    // The ID of the object.
    id: string,
    // Get a single product image by ID
    mainImage:  {
      // The ID of the object.
      id: string,
      alt: string,
      // The URL of the image.
      url: string,
    } | null,
    images:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          // The URL of the image.
          url: string,
        },
      } >,
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
  } | null,
};

export interface UserFragment {
  // The ID of the object.
  id: string,
  email: string,
  isStaff: boolean,
  note: string | null,
  permissions:  Array< {
    // Internal code for permission.
    code: string,
    // Describe action(s) allowed to do by permission.
    name: string,
  } | null > | null,
};

export interface MoneyFragment {
  // Amount of money.
  amount: number,
  // Currency code.
  currency: string,
};

export interface ProductImageFragment {
  // The ID of the object.
  id: string,
  alt: string,
  sortOrder: number,
  // The URL of the image.
  url: string,
};

export interface ProductFragment {
  // The ID of the object.
  id: string,
  name: string,
  description: string,
  seoTitle: string | null,
  seoDescription: string | null,
  category:  {
    // The ID of the object.
    id: string,
    name: string,
  },
  collections:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
        name: string,
      },
    } >,
  } | null,
  // The product's base price (without any discounts
  // applied).
  price:  {
    // Amount of money.
    amount: number,
    // Currency code.
    currency: string,
  } | null,
  margin:  {
    start: number | null,
    stop: number | null,
  } | null,
  purchaseCost:  {
    // Lower bound of a price range.
    start:  {
      // Amount of money.
      amount: number,
      // Currency code.
      currency: string,
    } | null,
    // Upper bound of a price range.
    stop:  {
      // Amount of money.
      amount: number,
      // Currency code.
      currency: string,
    } | null,
  } | null,
  isPublished: boolean,
  chargeTaxes: boolean,
  availableOn: string | null,
  // List of product attributes assigned to this product.
  attributes:  Array< {
    // Name of an attribute
    attribute:  {
      // The ID of the object.
      id: string,
      // Internal representation of an attribute name.
      slug: string | null,
      // Visible name for display purposes.
      name: string | null,
      // List of attribute's values.
      values:  Array< {
        // Visible name for display purposes.
        name: string | null,
        // Internal representation of an attribute name.
        slug: string | null,
      } | null > | null,
    } | null,
    // Value of an attribute.
    value:  {
      // The ID of the object.
      id: string,
      // Visible name for display purposes.
      name: string | null,
      // Internal representation of an attribute name.
      slug: string | null,
    } | null,
  } | null > | null,
  // Informs about product's availability in the storefront,
  // current price and discounts.
  availability:  {
    available: boolean | null,
    priceRange:  {
      // Lower bound of a price range.
      start:  {
        // Amount of money without taxes.
        net:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        },
      } | null,
      // Upper bound of a price range.
      stop:  {
        // Amount of money without taxes.
        net:  {
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        },
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
        sortOrder: number,
        // The URL of the image.
        url: string,
      },
    } >,
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
          // Amount of money.
          amount: number,
          // Currency code.
          currency: string,
        } | null,
        // Quantity of a product available for sale.
        stockQuantity: number,
        // Gross margin percentage value.
        margin: number | null,
      },
    } >,
  } | null,
  productType:  {
    // The ID of the object.
    id: string,
    name: string,
    hasVariants: boolean,
  },
  // The storefront URL for the product.
  url: string,
};

export interface ProductVariantFragment {
  // The ID of the object.
  id: string,
  // List of attributes assigned to this variant.
  attributes:  Array< {
    // Name of an attribute
    attribute:  {
      // The ID of the object.
      id: string,
      // Visible name for display purposes.
      name: string | null,
      // Internal representation of an attribute name.
      slug: string | null,
      // List of attribute's values.
      values:  Array< {
        // The ID of the object.
        id: string,
        // Visible name for display purposes.
        name: string | null,
        // Internal representation of an attribute name.
        slug: string | null,
      } | null > | null,
    } | null,
    // Value of an attribute.
    value:  {
      // The ID of the object.
      id: string,
      // Visible name for display purposes.
      name: string | null,
      // Internal representation of an attribute name.
      slug: string | null,
    } | null,
  } | null > | null,
  // Cost price of the variant.
  costPrice:  {
    // Amount of money.
    amount: number,
    // Currency code.
    currency: string,
  } | null,
  images:  {
    edges:  Array< {
      // The item at the end of the edge
      node:  {
        // The ID of the object.
        id: string,
      },
    } >,
  } | null,
  name: string,
  // Override the base price of a product if necessary.
  // A value of `null` indicates that the default product price is used.
  priceOverride:  {
    // Amount of money.
    amount: number,
    // Currency code.
    currency: string,
  } | null,
  product:  {
    // The ID of the object.
    id: string,
    images:  {
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          alt: string,
          sortOrder: number,
          // The URL of the image.
          url: string,
        },
      } >,
    } | null,
    name: string,
    // The URL of a main thumbnail for a product.
    thumbnailUrl: string | null,
    variants:  {
      // A total count of items in the collection
      totalCount: number | null,
      edges:  Array< {
        // The item at the end of the edge
        node:  {
          // The ID of the object.
          id: string,
          name: string,
          sku: string,
          image:  {
            edges:  Array< {
              // The item at the end of the edge
              node:  {
                // The ID of the object.
                id: string,
                // The URL of the image.
                url: string,
              },
            } >,
          } | null,
        },
      } >,
    } | null,
  },
  sku: string,
  quantity: number,
  quantityAllocated: number,
};
