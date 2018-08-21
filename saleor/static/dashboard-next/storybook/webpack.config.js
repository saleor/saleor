/* eslint-disable */
module.exports = (baseConfig, env, config) => {
  config.module.rules.push({
    test: /\.tsx?$/,
    exclude: /node_modules/,
    loader: require.resolve("awesome-typescript-loader")
  });
  config.resolve.extensions.push(".ts", ".tsx");
  return config;
};
