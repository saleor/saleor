const HtmlWebpackPlugin = require('html-webpack-plugin');
const WebappWebpackPlugin = require('webapp-webpack-plugin');
const SWPrecacheWebpackPlugin = require('sw-precache-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const path = require('path');

const resolve = path.resolve.bind(path, __dirname);

module.exports = {
    mode: 'development',
    devtool: 'inline-source-map',
    plugins: [
        new CleanWebpackPlugin([resolve('dist')]),
        new HtmlWebpackPlugin(),
        new WebappWebpackPlugin({
            logo: resolve('src/images/logo.svg'),
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