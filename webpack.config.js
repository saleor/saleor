const path = require('path');
const autoprefixer = require('autoprefixer');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const WebappWebpackPlugin = require('webapp-webpack-plugin');
const SWPrecacheWebpackPlugin = require('sw-precache-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const resolve = path.resolve.bind(path, __dirname);
const sourceDir = path.join(__dirname, './src/');
const distDir = path.join(__dirname, './dist/');

const isProduction = process.argv.indexOf('-p') >= 0;

module.exports = {
  watchOptions: {
    poll: true,
  },
  node: {
    fs: 'empty',
  },
  entry: {
    app: `${sourceDir}index.js`,
  },
  output: {
    path: distDir,
    filename: 'js/[name].js',
  },
  devtool: 'source-map',
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['env', 'react', 'stage-0'],
          },
        },
      },
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              sourceMap: true,
              importLoaders: 2,
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              sourceMap: true,
              plugins: function () {
                return [autoprefixer];
              }
            }
          },
          {
            loader: 'sass-loader',
            options: {
              sourceMap: true
            }
          }
        ]
      },
      {
        test: /\.woff2?$|\.ttf$|\.eot$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: 'fonts/',
            },
          },
        ],
      },
      {
        test: /\.(gif|jpg|png|svg|)$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: 'images/',
            },
          },
        ],
      },
    ]
  },
  plugins: [
    autoprefixer,
    new CleanWebpackPlugin([resolve('dist')]),
    new HtmlWebpackPlugin({
      template: `${sourceDir}index.html`,
      filename: `${distDir}index.html`
    }),
    new MiniCssExtractPlugin({
      filename: 'css/[name].css',
      chunkFilename: '[id].css'
    }),
    new WebappWebpackPlugin({
      logo: resolve('src/images/logo.svg'),
      prefix: 'images/favicons/',
      favicons: {
        appName: 'Get Saleor',
        appDescription: 'Informations about the Saloer ecommerce',
        display: 'standalone',
        developerURL: null, // prevent retrieving from the nearest package.json
        background: '#ddd',
        theme_color: '#333',
        icons: {
          coast: false,
          yandex: false
        }
      }
    }),
    new SWPrecacheWebpackPlugin({
      cacheId: 'get-saleor',
      filename: 'service-worker.js',
      staticFileGlobsIgnorePatterns: [/\.map$/, /asset-manifest\.json$/],
    })
  ]
};