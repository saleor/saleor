const reactComponent = require("./reactComponent");
const exampleGenerator = require("./exampleGenerator");

module.exports = plop => {
  plop.setGenerator("React component", reactComponent(plop));
  // Example:
  // plop.setGenerator("Example generator", exampleGenerator(plop));

  plop.setHelper("ifEqual", function(firstValue, secondValue, options) {
    const result = firstValue === secondValue;
    return result ? options.fn(this) : options.inverse(this);
  });
  plop.setHelper("ifNotEqual", function(firstValue, secondValue, options) {
    const result = firstValue !== secondValue;
    return result ? options.fn(this) : options.inverse(this);
  });

  plop.setPartial("p_componentName", "{{pascalCase componentName}}");
  plop.setPartial(
    "p_componentTagName",
    '{{#if componentHasStyles}}Wrapper{{else}}{{#ifEqual applicationType "mobile"}}View{{else}}React.Fragment{{/ifEqual}}{{/if}}'
  );
};
