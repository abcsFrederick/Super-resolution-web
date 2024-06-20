module.exports = {
  configureWebpack: {
    devServer: {
      host: '0.0.0.0',
      port: '8099',
      https: false,
    },
  },
  chainWebpack: config => {
    config
    .plugin('html')
    .tap(args => {
      args[0].title = 'Super resolution'
      return args
    });
  },
  lintOnSave: false,
  // outputDir: process.env.NODE_ENV === 'production'
  //   ? '/var/www/html'
  //   : 'dist'
}