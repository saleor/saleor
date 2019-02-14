const autoprefixer = require('autoprefixer');
const CheckerPlugin = require('fork-ts-checker-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const path = require('path');
const url = require('url');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');

const resolve = path.resolve.bind(path, __dirname);

const bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

const providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  Popper: 'popper.js',
  'query-string': 'query-string'
});

const checkerPlugin = new CheckerPlugin({
  reportFiles: ['saleor/**/*.{ts,tsx}'],
  tslint: true
});

module.exports = (env, argv) => {
  const devMode = argv.mode !== 'production';

  let extractCssPlugin;
  let fileLoaderPath;
  let output;

  if (!devMode) {
    const baseStaticPath = process.env.STATIC_URL || '/static/';
    const publicPath = url.resolve(baseStaticPath, 'assets/');
    output = {
      path: resolve('saleor/static/assets/'),
      filename: '[name].[chunkhash].js',
      chunkFilename: '[name].[chunkhash].js',
      publicPath: publicPath
    };
    fileLoaderPath = 'file-loader?name=[name].[hash].[ext]';
    extractCssPlugin = new MiniCssExtractPlugin({
      filename: '[name].[chunkhash].css',
      chunkFilename: '[id].[chunkhash].css'
    });
  } else {
    output = {
      path: resolve('saleor/static/assets/'),
      filename: '[name].js',
      chunkFilename: '[name].js',
      publicPath: '/static/assets/'
    };
    fileLoaderPath = 'file-loader?name=[name].[ext]';
    extractCssPlugin = new MiniCssExtractPlugin({
      filename: '[name].css',
      chunkFilename: '[name].css'
    });
  }

  return {
    entry: {
      dashboard: './saleor/static/dashboard/js/dashboard.js',
      'dashboard-next': './saleor/static/dashboard-next/index.tsx',
      document: './saleor/static/dashboard/js/document.js',
      storefront: './saleor/static/js/storefront.js'
    },
    output: output,
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel-loader'
        },
        {
          test: /\.scss$/,
          use: [
            MiniCssExtractPlugin.loader,
            {
              loader: 'css-loader',
              options: {
                'sourceMap': true
              }
            },
            {
              loader: 'postcss-loader',
              options: {
                'sourceMap': true,
                'plugins': function () {
                  return [autoprefixer];
                }
              }
            },
            {
              loader: 'sass-loader',
              options: {
                'sourceMap': true
              }
            }
          ]
        },
        {
          test: /\.tsx?$/,
          exclude: /node_modules/,
          loader: 'ts-loader',
          options: {
            experimentalWatchApi: true,
            transpileOnly: true
          }
        },
        {
          test: /\.(eot|otf|png|svg|jpg|ttf|woff|woff2)(\?v=[0-9.]+)?$/,
          loader: fileLoaderPath,
          include: [
            resolve('node_modules'),
            resolve('saleor/static/fonts'),
            resolve('saleor/static/images'),
            resolve('saleor/static/dashboard/images')
          ]
        }
      ]
    },
    optimization: {
      removeAvailableModules: false,
      removeEmptyChunks: false,
      splitChunks: false
    },
    plugins: [
      bundleTrackerPlugin,
      extractCssPlugin,
      providePlugin,
      checkerPlugin
    ],
    resolve: {
      alias: {
        jquery: resolve('node_modules/jquery/dist/jquery.js')
      },
      extensions: ['.ts', '.tsx', '.js', '.jsx']
    },
    devtool: 'sourceMap'
  };
};
