var BundleTracker = require('webpack-bundle-tracker');
var MiniCssExtractPlugin = require('mini-css-extract-plugin');
var path = require('path');
var url = require('url');
var webpack = require('webpack');
var autoprefixer = require('autoprefixer');

var resolve = path.resolve.bind(path, __dirname);

var extractCssPlugin;
var fileLoaderPath;
var output;
var reactPath;
var reactDomPath;

if (process.env.NODE_ENV === 'production') {
  const baseStaticPath = process.env.STATIC_URL || '/static/';
  const publicPath = url.resolve(baseStaticPath, 'assets/');
  reactPath = 'node_modules/react/umd/react.production.min.js';
  reactDomPath = 'node_modules/react-dom/umd/react-dom.production.min.js';
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
  reactPath = 'node_modules/react/umd/react.development.js';
  reactDomPath = 'node_modules/react-dom/umd/react-dom.development.js';
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
  Popper: 'popper.js',
  'query-string': 'query-string'
});

var config = {
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
        loader: 'awesome-typescript-loader'
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
      jquery: resolve('node_modules/jquery/dist/jquery.js'),
      react: resolve(reactPath),
      'react-dom': resolve(reactDomPath)
    },
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },
  devtool: 'sourceMap'
};

module.exports = config;
