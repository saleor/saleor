import queryString from 'query-string';

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
      if (Array.isArray(urlParams[key])) {
        const values = urlParams[key];
        values.map((valueSlug) => {
          attributes.push(`${key}:${valueSlug}`);
        });
      } else {
        const valueSlug = urlParams[key];
        attributes.push(`${key}:${valueSlug}`);
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

export const convertSortByFromString = (sortBy) => {
  if (!sortBy) {
    return null;
  }
  const direction = sortBy.startsWith('-')
    ? 'DESC'
    : 'ASC';

  let field = sortBy.replace(/^-/, '');
  field =
    field === 'name'
      ? 'NAME'
      : field === 'price'
        ? 'PRICE'
        : undefined;
  let output = { 'field': field, 'direction': direction };
  return output;
};

export const convertSortByFromObject = (sortBy) => {
  if (!sortBy) {
    return '';
  }
  const sortOrder = sortBy.direction === 'DESC' ? '-' : '';
  const sortField = sortBy.field.toLowerCase();
  const output = `${sortOrder}${sortField}`;
  return output;
};
