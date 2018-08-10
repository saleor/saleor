/* eslint-disable */
const path = require("path");

const resolve = path.resolve.bind(path, `${__dirname}/../../../../`);

let reactPath;
let reactDomPath;

if (process.env.NODE_ENV === "production") {
  reactPath = "node_modules/react/umd/react.production.min.js";
  reactDomPath = "node_modules/react-dom/umd/react-dom.production.min.js";
} else {
  reactPath = "node_modules/react/umd/react.development.js";
  reactDomPath = "node_modules/react-dom/umd/react-dom.development.js";
}

const config = {
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "babel-loader"
      },
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        loader: "ts-loader"
      },
      {
        test: /\.(svg|png|jpe?g)$/,
        loader: "file-loader",
        options: {
          name: "[name].[ext]"
        }
      }
    ]
  },
  resolve: {
    alias: {
      react: resolve(reactPath),
      "react-dom": resolve(reactDomPath)
    },
    extensions: [".ts", ".tsx", ".js", ".jsx"]
  }
};

module.exports = config;
