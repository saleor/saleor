import { History, LocationState } from "history";
import { Base64 } from "js-base64";
import { each } from "lodash";
import { parse as parseQs, stringify as stringifyQs } from "query-string";
import { FetchResult } from "react-apollo";
import { generatePath } from "react-router";

import { OrderDirection, ProductOrderField } from "../../types/globalTypes";
import { FormError } from "./types";

export const slugify = (text: string | number): string =>
  text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-") // Replace spaces with -
    .replace(/&/g, "-and-") // Replace & with 'and'
    .replace(/[^\w\-]+/g, "") // Remove all non-word chars
    .replace(/\-\-+/g, "-"); // Replace multiple - with single -

export const getDBIdFromGraphqlId = (
  graphqlId: string,
  schema?: string
): number => {
  // This is temporary solution, we will use slugs in the future
  const rawId = Base64.decode(graphqlId);
  const regexp = /(\w+):(\d+)/;
  const [, expectedSchema, id] = regexp.exec(rawId);
  if (schema && schema !== expectedSchema) {
    throw new Error("Schema is not correct");
  }
  return parseInt(id, 10);
};

export const getGraphqlIdFromDBId = (id: string, schema: string): string =>
  // This is temporary solution, we will use slugs in the future
  Base64.encode(`${schema}:${id}`);

export const priceToString = (
  price: { amount: number; currency: string },
  locale?: string
): string => {
  const { amount } = price;
  if (locale) {
    return amount.toLocaleString(locale, {
      currency: price.currency,
      style: "currency",
    });
  } else {
    return `${price.currency} ${amount.toFixed(2)}`;
  }
};

export const generateProductUrl = (id: string, name: string) =>
  `/product/${slugify(name)}/${getDBIdFromGraphqlId(id, "Product")}/`;

export const generateCategoryUrl = (id: string, name: string) =>
  `/category/${slugify(name)}/${getDBIdFromGraphqlId(id, "Category")}/`;

export const generateCollectionUrl = (id: string, name: string) =>
  `/collection/${slugify(name)}/${getDBIdFromGraphqlId(id, "Collection")}/`;

export const generatePageUrl = (slug: string) => `/page/${slug}/`;

interface AttributeDict {
  [attributeSlug: string]: string[];
}
export const convertToAttributeScalar = (attributes: AttributeDict) =>
  Object.entries(attributes)
    .map(([key, value]) => value.map(attribute => `${key}:${attribute}`))
    .reduce((prev, curr) => [...prev, ...curr], []);

interface QueryString {
  [key: string]: string[] | string | null | undefined;
}
export const getAttributesFromQs = (qs: QueryString) =>
  Object.keys(qs)
    .filter(
      key => !["pageSize", "priceGte", "priceLte", "sortBy", "q"].includes(key)
    )
    .reduce((prev, curr) => {
      prev[curr] = typeof qs[curr] === "string" ? [qs[curr]] : qs[curr];
      return prev;
    }, {});

export const getValueOrEmpty = <T>(value: T): T | string =>
  value === undefined || value === null ? "" : value;

export const convertSortByFromString = (sortBy: string) => {
  if (!sortBy) {
    return null;
  }
  const direction = sortBy.startsWith("-")
    ? OrderDirection.DESC
    : OrderDirection.ASC;

  let field;
  switch (sortBy.replace(/^-/, "")) {
    case "name":
      field = ProductOrderField.NAME;
      break;

    case "price":
      field = ProductOrderField.PRICE;
      break;

    case "updated_at":
      field = ProductOrderField.DATE;
      break;

    default:
      return null;
  }
  return { field, direction };
};

export const maybe = <T>(exp: () => T, d?: T) => {
  try {
    const result = exp();
    return result === undefined ? d : result;
  } catch {
    return d;
  }
}

export const parseQueryString = (
  location: LocationState
): { [key: string]: string } => {
  const query = {
    ...parseQs(location.search.substr(1)),
  };
  each(query, (value, key) => {
    if (Array.isArray(value)) {
      query[key] = value[0];
    }
  });
  return query as { [key: string]: string };
};

export const updateQueryString = (
  location: LocationState,
  history: History
) => {
  const querystring = parseQueryString(location);

  return (key: string, value?) => {
    if (value === "") {
      delete querystring[key];
    } else {
      querystring[key] = value || key;
    }
    history.replace("?" + stringifyQs(querystring));
  };
};

export const isPath = (pathname: string, url: string) =>
  pathname.indexOf(generatePath(url, { token: undefined })) !== -1;

export const findFormErrors = (result: void | FetchResult): FormError[] => {
  if (result) {
    const data = Object.values(maybe(() => result.data, []));

    return data.reduce((prevVal, currVal) => {
      const errors = currVal.errors || [];

      return [...prevVal, ...errors];
    }, []);
  }
  return [];
};

export const removeEmptySpaces = (text: string) => text.replace(/\s+/g, "");
