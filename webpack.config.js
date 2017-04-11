var autoprefixer = require('autoprefixer');
var BundleTracker = require('webpack-bundle-tracker');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var FaviconsWebpackPlugin = require('favicons-webpack-plugin');
var path = require('path');
var webpack = require('webpack');

var resolve = path.resolve.bind(path, __dirname);

var extractTextPlugin;
var fileLoaderPath;
var output;

if (process.env.NODE_ENV === 'production') {
  output = {
    path: resolve('saleor/static/assets/'),
    filename: '[name].[chunkhash].js',
    publicPath: 'https://saleor-demo.s3.amazonaws.com/assets/'
  };
  fileLoaderPath = 'file?name=[name].[hash].[ext]';
  extractTextPlugin = new ExtractTextPlugin('[name].[contenthash].css');
} else {
  output = {
    path: resolve('saleor/static/assets/'),
    filename: '[name].js',
    publicPath: '/static/assets/'
  };
  fileLoaderPath = 'file?name=[name].[ext]';
  extractTextPlugin = new ExtractTextPlugin('[name].css');
}

var bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

var commonsChunkPlugin = new webpack.optimize.CommonsChunkPlugin({
  names: 'vendor'
});

var occurenceOrderPlugin = new webpack.optimize.OccurenceOrderPlugin();

var environmentPlugin = new webpack.DefinePlugin({
  'process.env': {
    NODE_ENV: JSON.stringify(process.env.NODE_ENV || 'development')
  }
});

var providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  '_': 'underscore',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  'Tether': 'tether',
  'window.Tether': 'tether'
});

var faviconsWebpackPlugin = new FaviconsWebpackPlugin({
  logo: './saleor/static/images/favicon.svg',
  prefix: 'favicons/',
  title: "Saleor"
});

var config = {
  entry: {
    category: './saleor/static/js/category.js',
    dashboard: './saleor/static/dashboard/js/dashboard.js',
    storefront: './saleor/static/js/storefront.js',
    vendor: [
      'babel-es6-polyfill',
      'bootstrap',
      'jquery',
      'jquery.cookie',
      'react',
      'react-relay'
    ]
  },
  output: output,
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
          'css?sourceMap',
          'postcss',
          'sass'
        ])
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
  plugins: [
    bundleTrackerPlugin,
    commonsChunkPlugin,
    environmentPlugin,
    extractTextPlugin,
    occurenceOrderPlugin,
    providePlugin,
    faviconsWebpackPlugin
  ],
  postcss: function() {
    return [autoprefixer];
  },
  resolve: {
    alias: {
      'jquery': resolve('node_modules/jquery/dist/jquery.js'),
      'react': resolve('node_modules/react/dist/react.min.js'),
      'react-dom': resolve('node_modules/react-dom/dist/react-dom.min.js')
    }
  },
  sassLoader: {
    sourceMap: true
  }
};

module.exports = config;
