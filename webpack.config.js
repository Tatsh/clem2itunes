const path = require('path');
module.exports = {
  devtool: false,
  entry: './src/index.ts',
  mode: 'development',
  module: {
    rules: [{ exclude: /node_modules/, test: /\.tsx?$/, use: 'ts-loader' }],
  },
  output: {
    clean: true,
    filename: 'index.js',
    path: path.resolve(__dirname, 'dist'),
  },
  resolve: {
    extensions: ['.ts'],
  },
};
