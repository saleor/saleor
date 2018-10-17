import { CollectionList_collections_edges_node } from "./types/CollectionList";

export const collections: CollectionList_collections_edges_node[] = [
  {
    __typename: "Collection",
    id: "Q29sbGVjdGlvbjox",
    isPublished: true,
    name: "Summer collection",
    products: {
      __typename: "ProductCountableConnection",
      totalCount: 4
    }
  },
  {
    __typename: "Collection",
    id: "Q29sbGVjdGlvbjoy",
    isPublished: true,
    name: "Winter sale",
    products: {
      __typename: "ProductCountableConnection",
      totalCount: 4
    }
  }
];
