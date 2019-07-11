import urljoin from "url-join";

import { searchUrl } from "../../../routes";

export const structuredData = shop => {
  return JSON.stringify({
    "@context": "https://schema.org",
    "@type": "WebSite",
    description: shop.description,
    name: shop.name,
    potentialAction: {
      "@type": "SearchAction",
      "query-input": "required name=q",
      target: urljoin(location.href, searchUrl, "?q={q}"),
    },
    url: location.href,
  });
};
