var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var path = require('path');
var webpack = require('webpack');
var config = require('./webpack.config');

var resolve = path.resolve.bind(path, __dirname);

var bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

var commonsChunkPlugin = new webpack.optimize.CommonsChunkPlugin({
  names: 'vendor'
});

var extractTextPlugin = new ExtractTextPlugin('[name].css');

var occurenceOrderPlugin = new webpack.optimize.OccurenceOrderPlugin();

var environmentPlugin = new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify(process.env.NODE_ENV || 'development')
  }
});

var uglifyJSPlugin = new webpack.optimize.UglifyJsPlugin();

var providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  '_': 'underscore',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  'Tether': 'tether',
  'window.Tether': 'tether'
});

config.output = {
  path: resolve('saleor/static/assets/'),
  filename: '[name].js',
  publicPath: '/'
};

config.plugins = [
  bundleTrackerPlugin,
  commonsChunkPlugin,
  environmentPlugin,
  extractTextPlugin,
  occurenceOrderPlugin,
  providePlugin,
  uglifyJSPlugin
];

module.exports = config;
