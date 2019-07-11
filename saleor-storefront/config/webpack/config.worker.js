const path = require("path");
const WorkboxPlugin = require("workbox-webpack-plugin");

module.exports = ({ sourceDir, distDir }) => ({
  plugins: [
    new WorkboxPlugin.InjectManifest({
      swSrc: `${sourceDir}/sw.js`,
      swDest: path.join(distDir, './service-worker.js'),
      exclude: [/\.map$/, /^manifest.*\.js(?:on)?$/, /\.js.map$/, /\.css.map/, /\.xls$/]
    })
  ]
});
