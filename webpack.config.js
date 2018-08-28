const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const WebappWebpackPlugin = require('webapp-webpack-plugin');
const SWPrecacheWebpackPlugin = require('sw-precache-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const PostcssPresetEnv = require('postcss-preset-env');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');

const sourceDir = path.join(__dirname, './src/');
const distDir = path.join(__dirname, './dist/');
const devMode = process.argv.indexOf('-p') < 0;

module.exports = {
  resolve: {
    extensions: ['.js', '.jsx']
  },
  externals: {
    googleTagManager: 'dataLayer'
  },
  watchOptions: {
    poll: true,
  },
  node: {
    fs: 'empty',
  },
  entry: {
    app: `${sourceDir}index.jsx`,
  },
  output: {
    path: distDir,
    filename: devMode ? 'js/[name].js' : 'js/[name].[contenthash].js',
    publicPath: '/',
  },
  devtool: 'source-map',
  devServer: {
    historyApiFallback: true,
  },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['env', 'react', 'stage-0'],
          },
        },
      },
      {
        test: /\.css$/,
        use: [
          devMode ? 'style-loader' : MiniCssExtractPlugin.loader,
          { loader: 'css-loader', options: { importLoaders: 1 } },
          {
            loader: 'postcss-loader', options: {
              ident: 'postcss',
              plugins: (ctx) => [
                PostcssPresetEnv({
                  stage: 3,
                  features: {
                    'nesting-rules': true,
                    'color-mod-function': {
                      unresolved: 'warn'
                    }
                  }
                })
              ]
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
              name: '[name].[hash].[ext]',
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
              name: '[name].[hash].[ext]',
              outputPath: 'images/',
            }
          },
          {
            loader: 'image-webpack-loader',
            options: {
              mozjpeg: {
                progressive: true,
                quality: 85
              },
              pngquant: {
                quality: '65-90',
                speed: 4
              },
              gifsicle: {
                enabled: false,
              },
            }
          }
        ],
      },
    ]
  },
  optimization: {
    minimizer: [
      new OptimizeCSSAssetsPlugin({})
    ]
  },
  plugins: [
    new CleanWebpackPlugin([distDir]),
    new HtmlWebpackPlugin({
      template: `${sourceDir}index.ejs`,
      filename: `${distDir}index.html`,
      googleTagManager: 'GTM-KL4NB3Z'
    }),
    new MiniCssExtractPlugin({
      filename: devMode ? 'css/[name].css' : 'css/[name].[contenthash].css',
      chunkFilename: devMode ? '[id].css' : '[id].[contenthash].css'
    }),
    new CopyWebpackPlugin(
      [{ from: `${sourceDir}images/`, to: `${distDir}images/` }]),
    // PWA plugins
    new WebappWebpackPlugin({
      logo: `${sourceDir}images/logo.svg`,
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
