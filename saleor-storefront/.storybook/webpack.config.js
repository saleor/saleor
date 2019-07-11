const path = require("path");
const ForkTsCheckerWebpackPlugin = require("fork-ts-checker-webpack-plugin");
const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");

module.exports = ({ config }) => {
  config.module.rules.push({
    test: /\.(ts|tsx)$/,
    loader: require.resolve("ts-loader"),
    options: {
      transpileOnly: true
    }
  });

  config.module.rules.push({
    test: /stories\.tsx?$/,
    loaders: [require.resolve("@storybook/addon-storysource/loader")],
    enforce: "pre"
  });

  config.resolve.extensions.push(".ts", ".tsx");
  config.resolve.plugins = [
    new TsconfigPathsPlugin({
      configFile: path.resolve(__dirname, "../tsconfig.json")
    })
  ];

  config.resolve.modules = [
    ...(config.resolve.modules || []),
    path.resolve("./")
  ];

  config.plugins.push(
    new ForkTsCheckerWebpackPlugin({
      tslint: true,
      exclude: "node_modules"
    })
  );

  return config;
};
