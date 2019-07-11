const fs = require("fs");
const isEmpty = require("lodash/isEmpty");
const path = require("path");

// paths
const PROJECT_ROOT = path.join(__dirname, "..");
const applicationComponentsPath = path.join(
  PROJECT_ROOT,
  "src",
  "@next",
  "components"
);
const componentPath = filePath =>
  path.join(applicationComponentsPath, filePath);

const readDirSync = dirPath => {
  let paths = fs.readdirSync(dirPath);

  return paths
    .filter(path => path !== "index.ts")
    .map(path => path.replace(/\.[^\.]+$/, ""));
};

const required = value => {
  if (isEmpty(value)) {
    return "This field is required.";
  }

  return true;
};

const templatePath = filePath =>
  path.join(PROJECT_ROOT, ".plop/templates", filePath);

const componentChoices = () => readDirSync(applicationComponentsPath);

module.exports = {
  applicationComponentsPath,
  componentChoices,
  componentPath,
  readDirSync,
  required,
  templatePath
};
