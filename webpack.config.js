var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var path = require('path');
var webpack = require('webpack');

var resolve = path.resolve.bind(path, __dirname);

var bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

var commonsChunkPlugin = new webpack.optimize.CommonsChunkPlugin({
  names: 'vendor'
});

var extractTextPlugin = new ExtractTextPlugin('[name].[contenthash].css');

var providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  '_': 'underscore',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  'Tether': 'tether',
  'window.Tether': 'tether'
});

var config = {
  entry: {
    category: './saleor/static/ts/category.tsx',
    dashboard: './saleor/static/ts/dashboard.tsx',
    storefront: './saleor/static/ts/storefront.tsx',
    vendor: [
      'bootstrap',
      'jquery',
      'jquery.cookie',
      'react',
      'react-relay'
    ]
  },
  output: {
    path: resolve('saleor/static/assets/'),
    filename: '[name].[chunkhash].js'
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          'babel-loader',
          'awesome-typescript-loader'
        ]
      },
      {
        test: /\.js$/,
        enforce: 'pre',
        loader: 'source-map-loader'
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract([
          'css-loader?sourceMap',
          {
            loader: 'postcss-loader',
            options: {
              plugins: function () {
                return [autoprefixer];
              }
            }
          },
          'sass-loader?sourceMap'
        ])
      },
      {
        test: /\.(eot|otf|png|svg|jpg|ttf|woff|woff2)(\?v=[0-9.]+)?$/,
        loader: 'url-loader?name=[name].[hash].[ext]',
        include: [
          resolve('node_modules'),
          resolve('saleor/static/fonts'),
          resolve('saleor/static/images'),
          resolve('saleor/static/img')
        ]
      }
    ]
  },
  plugins: [
    bundleTrackerPlugin,
    commonsChunkPlugin,
    extractTextPlugin,
    providePlugin
  ],
  resolve: {
    alias: {
      'jquery': resolve('node_modules/jquery/dist/jquery.js')
    },
    extensions: [
      '.tsx', '.ts', '.js'
    ]
  }
};

module.exports = config;
