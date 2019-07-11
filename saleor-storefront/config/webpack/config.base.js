const HtmlWebpackPlugin = require("html-webpack-plugin");
const WebappWebpackPlugin = require("webapp-webpack-plugin");
const CleanWebpackPlugin = require("clean-webpack-plugin");
const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");
const ForkTsCheckerWebpackPlugin = require("fork-ts-checker-webpack-plugin");
const webpack = require("webpack");

module.exports = ({ sourceDir, distDir }) => ({
  resolve: {
    alias: {
      "react-dom": "@hot-loader/react-dom"
    },
    extensions: [".ts", ".tsx", ".js", ".jsx"],
    plugins: [
      new TsconfigPathsPlugin({
        configFile: "./tsconfig.json"
      })
    ]
  },
  entry: {
    app: `${sourceDir}/index.tsx`
  },
  output: {
    path: distDir,
    publicPath: "/"
  },
  devtool: "source-map",
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader",
        exclude: /node_modules/,
        options: {
          experimentalWatchApi: true,
          transpileOnly: true
        }
      },
      {
        test: /\.(woff2?|ttf|eot)$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "[name].[ext]",
              outputPath: "fonts/",
              publicPath: "/fonts/"
            }
          }
        ]
      },
      {
        test: /\.(gif|jpg|png|svg)$/,
        use: [
          {
            loader: "file-loader",
            options: {
              name: "[name].[ext]",
              outputPath: "images/",
              publicPath: "/images/"
            }
          },
          {
            loader: "image-webpack-loader",
            options: {
              mozjpeg: {
                progressive: true,
                quality: 85
              },
              pngquant: {
                quality: "65-90",
                speed: 4
              },
              gifsicle: {
                enabled: false
              }
            }
          }
        ]
      }
    ]
  },
  plugins: [
    new CleanWebpackPlugin([distDir]),
    new HtmlWebpackPlugin({
      filename: `${distDir}/index.html`,
      template: `${sourceDir}/index.html`
    }),
    new ForkTsCheckerWebpackPlugin({
      tslint: true,
      exclude: "node_modules",
      async: false
    }),
    // PWA plugins
    new WebappWebpackPlugin({
      logo: `${sourceDir}/images/favicon.png`,
      prefix: "images/favicons/",
      favicons: {
        appName: "Saleor",
        appDescription: "Storefront for the Saleor e-commerce platform",
        display: "standalone",
        developerURL: null, // prevent retrieving from the nearest package.json
        background: "#ddd",
        theme_color: "#333"
      }
    }),
    new webpack.EnvironmentPlugin(["npm_package_version", "BACKEND_URL"])
  ],
  node: {
    fs: "empty"
  }
});
