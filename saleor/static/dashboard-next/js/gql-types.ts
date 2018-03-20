/* tslint:disable */
//  This file was automatically generated and should not be edited.

export interface CategoryDeleteMutationVariables {
  id: string,
};

export interface CategoryDeleteMutation {
  categoryDelete:  {
    errors:  Array< {
      field: string | null,
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
    errors:  Array< {
      field: string | null,
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
    errors:  Array< {
      field: string | null,
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
  category:  {
    // The ID of the object.
    id: string,
    name: string,
    description: string,
    parent:  {
      // The ID of the object.
      id: string,
    } | null,
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
    products:  {
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
          thumbnailUrl: string | null,
          productType:  {
            id: string,
            name: string,
          } | null,
        } | null,
      } | null >,
    } | null,
  } | null,
};

export interface PageListQueryVariables {
  first?: number | null,
  after?: string | null,
  last?: number | null,
  before?: string | null,
};

export interface PageListQuery {
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
