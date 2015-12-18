var path = require('path');
var webpack = require('webpack');
var node_modules_dir = path.join(__dirname, 'node_modules');

function modulePath(dep) {
  return path.resolve(node_modules_dir, dep);
}

configuration = {
  entry: {
    dashboard: './saleor/static/js_src/dashboard.jsx',
    storefront: './saleor/static/js_src/storefront.jsx',
  },
  output: {
    filename: './saleor/static/js/[name].js'
  },
  module: {
    loaders: [
      {test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader'},
      {test: /\.json$/, loader: 'json'}
    ],
    noParse: [
      modulePath('jquery/dist/jquery.min.js'),
      modulePath('react/dist/react.min.js')
    ]
  },
  resolve: {
    alias: {
      jquery: modulePath('jquery/dist/jquery.min.js'),
      react: modulePath('react/dist/react.min.js'),
      'react-dom': modulePath('react-dom/dist/react-dom.min.js'),
      'react-redux': modulePath('react-redux/dist/react-redux.min.js'),
      'redux': modulePath('redux/dist/redux.min.js')
    },
    extensions: ['', '.jsx', '.js']
  },
  plugins: [
    new webpack.ProvidePlugin({
      $: 'jquery',
      '_': 'underscore',
      Backbone: 'backbone',
      jQuery: 'jquery',
      'window.Backbone': 'backbone',
      'window.jQuery': 'jquery'
    })
  ]
};

module.exports = configuration;
