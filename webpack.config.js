var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var path = require('path');
var webpack = require('webpack');

var bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

var commonsChunkPlugin = new webpack.optimize.CommonsChunkPlugin('vendor', '[name].[chunkhash].js');

var extractTextPlugin = new ExtractTextPlugin(
  '[name].[chunkhash].css'
);

var providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  '_': 'underscore',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  Backbone: 'backbone',
  'window.Backbone': 'backbone',
  Hammer: 'hammerjs'
});

var config = {
  entry: {
    dashboard: './saleor/static/js/dashboard.js',
    storefront: './saleor/static/js/storefront.js',
    vendor: [
      'bootstrap-sass',
      'jquery',
      'jquery.cookie',
      'react',
      'react-dom',
      'react-redux',
      'redux'
    ]
  },
  output: {
    path: path.resolve(__dirname, 'saleor/static/assets/'),
    filename: '[name].[chunkhash].js'
  },
  module: {
    loaders: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: 'babel'
      },
      {
        test: /\.json$/,
        loader: 'json'
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract([
          'css',
          'postcss',
          'sass'
        ])
      },
      {
        test: /\.(eot|otf|png|svg|ttf|woff|woff2)(\?v=[0-9.]+)?$/,
        loader: 'file?name=[name].[hash].[ext]',
        include: [
          path.resolve(__dirname, 'node_modules'),
          path.resolve(__dirname, 'saleor/static/fonts'),
          path.resolve(__dirname, 'saleor/static/images'),
          path.resolve(__dirname, 'saleor/static/img')
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
  postcss: function() {
    return [autoprefixer];
  },
  sassLoader: {
    sourceMap: true
  }
};

module.exports = config;
