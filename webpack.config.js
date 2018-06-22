var BundleTracker = require('webpack-bundle-tracker');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
var path = require('path');
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');

var resolve = path.resolve.bind(path, __dirname);

var extractCssPlugin;
var fileLoaderPath;
var output;

if (process.env.NODE_ENV === 'production') {
  output = {
    path: resolve('saleor/static/assets/'),
    filename: '[name].[chunkhash].js',
    chunkFilename: '[name].[chunkhash].js',
    publicPath: process.env.STATIC_URL || '/static/assets/'
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

var bundleTrackerPlugin = new BundleTracker({
  filename: 'webpack-bundle.json'
});

var providePlugin = new webpack.ProvidePlugin({
  $: 'jquery',
  jQuery: 'jquery',
  'window.jQuery': 'jquery',
  'Popper': 'popper.js',
  'query-string': 'query-string'
});

var config = {
  entry: {
    dashboard: './saleor/static/dashboard/js/dashboard.js',
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
    extractCssPlugin,
    providePlugin
  ],
  resolve: {
    alias: {
      'jquery': resolve('node_modules/jquery/dist/jquery.js'),
      'react': resolve('node_modules/react/dist/react.min.js'),
      'react-dom': resolve('node_modules/react-dom/dist/react-dom.min.js')
    }
  }
};

module.exports = config;
