module.exports = {
  configureWebpack: {
    devServer: {
      host: 'localhost',
      port: '8099',
      https: false
    }
  },
  // publicPath: process.env.NODE_ENV === 'production'
  //   ? '/omero/'
  //   : '/',
  publicPath: () => {
    if (process.env.NODE_ENV === 'local') {
      return '/';
    }
    return '/omero/';
  },
  chainWebpack: config => {
    config
    .plugin('html')
    .tap(args => {
      args[0].title = 'Super resolution'
      return args
    });
  },
  // lintOnSave: process.env.NODE_ENV !== 'production',
  // outputDir: process.env.NODE_ENV === 'production'
  //   ? '/var/www/html/omero/'
  //   : 'dist'
  outputDir: () => {
    if (process.env.NODE_ENV === 'local') {
      return '/var/www/html/omero/';
    }
    return 'dist';
  }
}