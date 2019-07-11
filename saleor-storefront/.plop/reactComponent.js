const utils = require("./utils");

module.exports = _plop => ({
  description: "It will create new component inside specified directory",
  prompts: [
    {
      type: "list",
      name: "componentGroup",
      message: "Select component group:",
      choices: () => {
        return utils.componentChoices();
      },
      validate: utils.required
    },
    {
      type: "input",
      name: "componentName",
      message: "Component name:",
      validate: utils.required
    },
    {
      type: "confirm",
      name: "componentHasStyles",
      message: "Does component have its own styles?",
      validate: utils.required
    },
    {
      type: "confirm",
      name: "componentHasTests",
      message: "Does component have tests?",
      validate: utils.required
    }
  ],

  actions: answers => {
    const actions = [
      {
        type: "add",
        path: utils.componentPath(
          `{{componentGroup}}/{{> p_componentName}}/index.ts`
        ),
        templateFile: utils.templatePath("reactComponentIndex.ts.hbs")
      },
      {
        type: "add",
        path: utils.componentPath(
          "{{componentGroup}}/{{> p_componentName}}/{{> p_componentName}}.tsx"
        ),
        templateFile: utils.templatePath("reactComponent.tsx.hbs")
      },
      {
        type: "add",
        path: utils.componentPath(
          "{{componentGroup}}/{{> p_componentName}}/types.ts"
        ),
        templateFile: utils.templatePath("reactComponentTypes.ts.hbs")
      },
      {
        type: "add",
        path: utils.componentPath(
          "{{componentGroup}}/{{> p_componentName}}/stories.tsx"
        ),
        templateFile: utils.templatePath("reactComponentStory.tsx.hbs")
      }
    ];

    if (answers.componentHasStyles) {
      actions.push({
        type: "add",
        path: utils.componentPath(
          "{{componentGroup}}/{{> p_componentName}}/styles.ts"
        ),
        templateFile: utils.templatePath("reactComponentStyles.ts.hbs")
      });
    }

    if (answers.componentHasTests) {
      actions.push({
        type: "add",
        path: utils.componentPath(
          "{{componentGroup}}/{{> p_componentName}}/test.tsx"
        ),
        templateFile: utils.templatePath("reactComponentTest.tsx.hbs")
      });
    }

    actions.push({
      type: "append",
      path: utils.componentPath("{{componentGroup}}/index.ts"),
      separator: "",
      templateFile: utils.templatePath("exportAll.ts.hbs")
    });

    return actions;
  }
});
