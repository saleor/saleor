// FIXME: at this moment it is not clear if storefront url should contain
// PostgreSQL ID or just slug, to for now it's only placeholder
export const storefrontUrl = (slug: string) =>
  `/products/collection/${slug}-1/`;
