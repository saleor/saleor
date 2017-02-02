import * as queryString from 'query-string';

export const getFromQuery = (key, defaultValue = null) => {
  let value = queryString.parse(location.search)[key];
  return value || defaultValue;
};

export const getAttributesFromQuery = (exclude) => {
  // Exclude parameter is used to exclude other query string parameters than
  // product attribute filters.
  const urlParams = queryString.parse(location.search);
  let attributes = [];
  Object.keys(urlParams).forEach(key => {
    if (exclude.indexOf(key) === -1) {
      let value = urlParams[key];
      if (Array.isArray(value)) {
        value.map((valueSlug) => {
          attributes.push(`${key}:${valueSlug}`);
        });
      } else {
        attributes.push(`${key}:${value}`);
      }
    }
  });
  return attributes;
};

export const ensureAllowedName = (name, allowed) => {
  let origName = name;
  if (name && name.startsWith('-')) {
    name = name.substr(1, name.length);
  }
  return allowed.indexOf(name) > -1 ? origName : null;
};
