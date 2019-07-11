const getVariantsStructuredData = variants => {
  const inStock = "https://schema.org/InStock";
  const outOfStock = "https://schema.org/OutOfStock";
  return variants.map(variant => ({
    "@type": "Offer",
    availability: variant.isAvailable ? inStock : outOfStock,
    itemCondition: "https://schema.org/NewCondition",
    price: variant.price.amount.toFixed(2),
    priceCurrency: variant.price.currency,
    sku: variant.sku,
  }));
};

export const structuredData = product => {
  const images = product.images.map(image => new URL(image.url).pathname);
  const variants = product.variants;

  return JSON.stringify({
    "@context": "https://schema.org/",
    "@type": "Product",
    description: !product.seoDescription
      ? `${product.description}`
      : `${product.seoDescription}`,
    image: images,
    name: !product.seoTitle ? `${product.name}` : `${product.seoTitle}`,
    offers: getVariantsStructuredData(variants),
    url: location.href,
  });
};
