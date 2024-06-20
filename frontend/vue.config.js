module.exports = {
  configureWebpack: {
    devServer: {
      host: 'localhost',
      port: '8099',
      https: false
    }
  },
  publicPath: process.env.NODE_ENV === 'production'
    ? '/omero/'
    : '/',
  chainWebpack: config => {
    config
    .plugin('html')
    .tap(args => {
      args[0].title = 'Super resolution'
      return args
    });
  },
  // lintOnSave: process.env.NODE_ENV !== 'production',
  outputDir: process.env.NODE_ENV === 'production'
    ? '/var/www/html/omero/'
    : 'dist'
}