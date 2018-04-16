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
