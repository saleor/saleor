var path = require("path");
var webpack = require("webpack");

var resolve = path.resolve.bind(path, `${__dirname}/../../../../`);

var reactPath;
var reactDomPath;

if (process.env.NODE_ENV === "production") {
  reactPath = "node_modules/react/umd/react.production.min.js";
  reactDomPath = "node_modules/react-dom/umd/react-dom.production.min.js";
} else {
  reactPath = "node_modules/react/umd/react.development.js";
  reactDomPath = "node_modules/react-dom/umd/react-dom.development.js";
}
var providePlugin = new webpack.ProvidePlugin({
  "query-string": "query-string"
});

var config = {
  entry: {
    "dashboard-next": "./saleor/static/dashboard-next/index.tsx"
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "babel-loader"
      },
      {
        test: /\.tsx?$/,
        loader: "ts-loader"
      },
      {
        test: /\.(svg|png)$/,
        loader: "file-loader",
        options: {
          name: "[name].[ext]"
        }
      }
    ]
  },
  plugins: [providePlugin],
  resolve: {
    alias: {
      react: resolve(reactPath),
      "react-dom": resolve(reactDomPath)
    },
    extensions: [".ts", ".tsx", ".js", ".jsx"]
  }
};

module.exports = config;
